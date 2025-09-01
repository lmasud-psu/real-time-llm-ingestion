#!/usr/bin/env python3
"""
Writer Service
A service that reads embeddings from Kafka and writes them to different databases.
"""

import json
import time
import logging
import os
from typing import Dict, Any, Optional
from flask import Flask, jsonify, request
import yaml
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import threading
import signal
import sys

# Database adapters
from database_adapters.lancedb_adapter import LanceDBAdapter
from database_adapters.postgres_adapter import PostgresAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('writer_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WriterService:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the writer service with configuration."""
        self.config = self._load_config(config_path)
        self.consumer = None
        self.database_adapter = None
        self.running = False
        self.stats = {
            'messages_processed': 0,
            'messages_written': 0,
            'errors': 0,
            'last_processed_timestamp': None,
            'start_time': time.time()
        }
        
        # Initialize database adapter
        self._init_database_adapter()
        
        # Initialize Kafka consumer
        self._init_kafka_consumer()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def _init_database_adapter(self):
        """Initialize the appropriate database adapter based on configuration."""
        # Check environment variable first, then config file
        db_type = os.environ.get('DATABASE_TYPE') or self.config.get('database', {}).get('type', 'lancedb')
        db_type = db_type.lower()
        
        if db_type == 'lancedb':
            self.database_adapter = LanceDBAdapter(self.config['database'])
            logger.info("Initialized LanceDB adapter")
        elif db_type == 'postgres':
            self.database_adapter = PostgresAdapter(self.config['database'])
            logger.info("Initialized PostgreSQL adapter")
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def _init_kafka_consumer(self):
        """Initialize Kafka consumer."""
        kafka_config = self.config['kafka']
        
        self.consumer = KafkaConsumer(
            kafka_config['input_topic'],
            bootstrap_servers=kafka_config['bootstrap_servers'],
            group_id=kafka_config['consumer_group'],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            key_deserializer=lambda x: x.decode('utf-8') if x else None
        )
        
        logger.info(f"Kafka consumer initialized for topic: {kafka_config['input_topic']}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _process_message(self, message) -> bool:
        """Process a single message from Kafka."""
        try:
            # Extract message data
            message_data = message.value
            message_key = message.key
            
            logger.debug(f"Processing message: {message_key}")
            
            # Validate message structure
            if not isinstance(message_data, dict):
                logger.warning(f"Invalid message format: {type(message_data)}")
                return False
            
            # Extract required fields
            message_id = message_data.get('id')
            original_text = message_data.get('original_text')
            embedding = message_data.get('embedding')
            
            if not all([message_id, original_text, embedding]):
                logger.warning(f"Missing required fields in message: {message_data}")
                return False
            
            # Write to database
            success = self.database_adapter.write_embedding(
                message_id=message_id,
                original_text=original_text,
                embedding=embedding,
                metadata=message_data
            )
            
            if success:
                self.stats['messages_written'] += 1
                logger.info(f"Successfully wrote embedding for message: {message_id}")
            else:
                logger.error(f"Failed to write embedding for message: {message_id}")
            
            self.stats['messages_processed'] += 1
            self.stats['last_processed_timestamp'] = time.time()
            
            return success
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error processing message: {e}")
            return False
    
    def start(self):
        """Start the writer service."""
        if self.running:
            logger.warning("Service is already running")
            return
        
        self.running = True
        logger.info("Starting writer service...")
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                
                self._process_message(message)
                
        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the writer service."""
        if not self.running:
            return
        
        logger.info("Stopping writer service...")
        self.running = False
        
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")
        
        if self.database_adapter:
            self.database_adapter.close()
            logger.info("Database adapter closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        uptime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_seconds': uptime,
            'uptime_formatted': f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s",
            'running': self.running
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get service health status."""
        try:
            db_health = self.database_adapter.health_check()
            kafka_health = self.consumer is not None
            
            return {
                'status': 'healthy' if (db_health and kafka_health) else 'unhealthy',
                'database': 'healthy' if db_health else 'unhealthy',
                'kafka': 'healthy' if kafka_health else 'unhealthy',
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }

# Flask app
app = Flask(__name__)
writer_service = None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    if writer_service:
        return jsonify(writer_service.get_health())
    return jsonify({'status': 'not_initialized'})

@app.route('/stats', methods=['GET'])
def stats():
    """Statistics endpoint."""
    if writer_service:
        return jsonify(writer_service.get_stats())
    return jsonify({'error': 'Service not initialized'})

@app.route('/start', methods=['POST'])
def start_service():
    """Start the writer service."""
    global writer_service
    
    if not writer_service:
        try:
            writer_service = WriterService()
        except Exception as e:
            return jsonify({'error': f'Failed to initialize service: {e}'}), 500
    
    if writer_service.running:
        return jsonify({'message': 'Service is already running'})
    
    # Start service in background thread
    thread = threading.Thread(target=writer_service.start, daemon=True)
    thread.start()
    
    return jsonify({'message': 'Service started successfully'})

@app.route('/stop', methods=['POST'])
def stop_service():
    """Stop the writer service."""
    global writer_service
    
    if not writer_service:
        return jsonify({'error': 'Service not initialized'}), 400
    
    writer_service.stop()
    return jsonify({'message': 'Service stopped successfully'})

@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    if writer_service:
        return jsonify({
            'database_type': writer_service.config.get('database', {}).get('type'),
            'kafka_topic': writer_service.config.get('kafka', {}).get('input_topic'),
            'bootstrap_servers': writer_service.config.get('kafka', {}).get('bootstrap_servers')
        })
    return jsonify({'error': 'Service not initialized'}), 400

if __name__ == '__main__':
    try:
        writer_service = WriterService()
        logger.info("Writer service initialized successfully")
        
        # Start the service
        app.run(
            host=writer_service.config.get('flask', {}).get('host', '0.0.0.0'),
            port=writer_service.config.get('flask', {}).get('port', 5001),
            debug=writer_service.config.get('flask', {}).get('debug', False)
        )
    except Exception as e:
        logger.error(f"Failed to start writer service: {e}")
        sys.exit(1)
