from flask import Flask, jsonify, request
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import yaml
import json
import logging
import threading
import time
import os
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import database factory with better error handling
try:
    from databases.database_factory import DatabaseFactory
    DATABASE_AVAILABLE = True
except ImportError as e:
    logger.error(f"Database adapters not available: {e}")
    logger.error("Please install required packages:")
    logger.error("  pip install lancedb psycopg2-binary")
    DATABASE_AVAILABLE = False
except Exception as e:
    logger.error(f"Unexpected error importing database adapters: {e}")
    DATABASE_AVAILABLE = False

app = Flask(__name__)

class WriterService:
    def __init__(self, config_path: str = "config.yaml"):
        if not DATABASE_AVAILABLE:
            raise ImportError("Database adapters not available. Please install required packages.")
            
        self.config_path = config_path
        self.config = self._load_config()
        self._override_config_from_env()
        self.consumer = None
        self.db_adapter = None
        self.running = False
        self.stats = {
            "messages_processed": 0,
            "messages_failed": 0,
            "last_message_time": None
        }
        
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
            
    def _override_config_from_env(self):
        """Override configuration with environment variables"""
        # Database type override
        if os.environ.get('DATABASE_TYPE'):
            self.config['database']['type'] = os.environ.get('DATABASE_TYPE')
            logger.info(f"Database type overridden from environment: {self.config['database']['type']}")
        
        # PostgreSQL overrides
        if os.environ.get('DATABASE_HOST'):
            self.config['database']['postgres']['host'] = os.environ.get('DATABASE_HOST')
        if os.environ.get('DATABASE_PORT'):
            self.config['database']['postgres']['port'] = int(os.environ.get('DATABASE_PORT'))
        if os.environ.get('DATABASE_NAME'):
            self.config['database']['postgres']['database'] = os.environ.get('DATABASE_NAME')
        if os.environ.get('DATABASE_USER'):
            self.config['database']['postgres']['user'] = os.environ.get('DATABASE_USER')
        if os.environ.get('DATABASE_PASSWORD'):
            self.config['database']['postgres']['password'] = os.environ.get('DATABASE_PASSWORD')
            
        # Kafka overrides
        if os.environ.get('KAFKA_BOOTSTRAP_SERVERS'):
            self.config['kafka']['bootstrap_servers'] = os.environ.get('KAFKA_BOOTSTRAP_SERVERS')
        if os.environ.get('KAFKA_INPUT_TOPIC'):
            self.config['kafka']['topic'] = os.environ.get('KAFKA_INPUT_TOPIC')
        if os.environ.get('KAFKA_CONSUMER_GROUP'):
            self.config['kafka']['group_id'] = os.environ.get('KAFKA_CONSUMER_GROUP')
            
        # LanceDB overrides
        if os.environ.get('LANCEDB_DATA_DIR'):
            self.config['database']['lancedb']['data_path'] = os.environ.get('LANCEDB_DATA_DIR')
            
        logger.info(f"Configuration loaded: {self.config}")
            
    def _setup_database(self):
        """Setup database adapter"""
        try:
            db_type = self.config["database"]["type"]
            self.db_adapter = DatabaseFactory.create_adapter(db_type, self.config["database"])
            logger.info(f"Database adapter created for {db_type}")
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise
            
    def _setup_kafka_consumer(self):
        """Setup Kafka consumer"""
        try:
            kafka_config = self.config["kafka"]
            self.consumer = KafkaConsumer(
                kafka_config["topic"],
                bootstrap_servers=kafka_config["bootstrap_servers"],
                group_id=kafka_config["group_id"],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info(f"Kafka consumer created for topic: {kafka_config['topic']}")
        except Exception as e:
            logger.error(f"Failed to setup Kafka consumer: {e}")
            raise
            
    def _process_message(self, message):
        """Process a single message from Kafka"""
        try:
            value = message.value
            logger.info(f"Processing message: {value.get('id', 'unknown')}")
            
            # Extract table name from message metadata
            table_name = value.get('table_name', 'embeddings')
            
            # Ensure table exists
            self.db_adapter.create_table(table_name)
            
            # Prepare data for insertion
            data = [{
                'id': value.get('id'),
                'text': value.get('text'),
                'embedding': value.get('embedding'),
                'timestamp': value.get('timestamp'),
                'source': value.get('source'),
                'metadata': value.get('metadata', {})
            }]
            
            # Insert data
            self.db_adapter.insert_data(table_name, data)
            
            # Update stats
            self.stats["messages_processed"] += 1
            self.stats["last_message_time"] = datetime.now().isoformat()
            
            logger.info(f"Successfully processed message {value.get('id')} to table {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            self.stats["messages_failed"] += 1
            
    def start(self):
        """Start the writer service"""
        try:
            logger.info("Starting writer service...")
            
            # Setup components
            self._setup_database()
            self._setup_kafka_consumer()
            
            self.running = True
            
            # Start consuming messages
            for message in self.consumer:
                if not self.running:
                    break
                    
                self._process_message(message)
                
        except Exception as e:
            logger.error(f"Error in writer service: {e}")
            self.running = False
        finally:
            if self.consumer:
                self.consumer.close()
            if hasattr(self.db_adapter, 'close'):
                self.db_adapter.close()
                
    def stop(self):
        """Stop the writer service"""
        logger.info("Stopping writer service...")
        self.running = False
        if self.consumer:
            self.consumer.close()

# Global writer service instance
writer_service = None
service_thread = None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    if not DATABASE_AVAILABLE:
        return jsonify({
            'status': 'unhealthy',
            'error': 'Database adapters not available',
            'service_running': False,
            'timestamp': datetime.now().isoformat()
        }), 500
        
    return jsonify({
        'status': 'healthy',
        'service_running': writer_service.running if writer_service else False,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/stats', methods=['GET'])
def stats():
    """Get service statistics"""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database adapters not available'}), 500
        
    if writer_service:
        return jsonify(writer_service.stats)
    return jsonify({'error': 'Service not running'})

@app.route('/start', methods=['POST'])
def start_service():
    """Start the writer service"""
    global writer_service, service_thread
    
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database adapters not available'}), 500
    
    if writer_service and writer_service.running:
        return jsonify({'message': 'Service already running'})
        
    try:
        writer_service = WriterService()
        service_thread = threading.Thread(target=writer_service.start, daemon=True)
        service_thread.start()
        
        return jsonify({'message': 'Writer service started successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to start service: {str(e)}'}), 500

@app.route('/stop', methods=['POST'])
def stop_service():
    """Stop the writer service"""
    global writer_service
    
    if not writer_service:
        return jsonify({'message': 'Service not running'})
        
    try:
        writer_service.stop()
        return jsonify({'message': 'Writer service stopped successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to stop service: {str(e)}'}), 500

@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database adapters not available'}), 500
        
    if writer_service:
        return jsonify(writer_service.config)
    return jsonify({'error': 'Service not running'})

if __name__ == '__main__':
    if not DATABASE_AVAILABLE:
        logger.error("Cannot start service: Database adapters not available")
        sys.exit(1)
        
    # Auto-start the service when the app starts
    try:
        writer_service = WriterService()
        service_thread = threading.Thread(target=writer_service.start, daemon=True)
        service_thread.start()
        logger.info("Writer service auto-started")
    except Exception as e:
        logger.error(f"Failed to auto-start service: {e}")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
