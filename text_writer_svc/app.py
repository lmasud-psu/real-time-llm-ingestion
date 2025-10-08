import os
import json
import uuid
import logging
import threading
import yaml
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from kafka import KafkaConsumer
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextWriterService:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.app = Flask(__name__)
        self.db_pool = None
        self.consumer = None
        self.consumer_thread = None
        self.running = False
        
        self._setup_database()
        self._setup_routes()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_path} not found")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise
    
    def _setup_database(self):
        """Setup database connection pool and create tables"""
        db_config = self.config['database']
        
        try:
            # Create connection pool
            self.db_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=db_config['connection_pool_size'],
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['name'],
                user=db_config['user'],
                password=db_config['password']
            )
            
            # Create tables
            self._create_tables()
            logger.info("Database connection established and tables created")
            
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise
    
    def _create_tables(self):
        """Create the text_messages table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS text_messages (
            id UUID PRIMARY KEY,
            message TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_text_messages_created_at ON text_messages(created_at);
        CREATE INDEX IF NOT EXISTS idx_text_messages_processed_at ON text_messages(processed_at);
        """
        
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(create_table_sql)
                conn.commit()
            logger.info("Tables created successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create tables: {e}")
            raise
        finally:
            self.db_pool.putconn(conn)
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            try:
                # Test database connection
                conn = self.db_pool.getconn()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                self.db_pool.putconn(conn)
                
                return jsonify({
                    "status": "healthy",
                    "service": self.config['service']['name'],
                    "version": self.config['service']['version'],
                    "kafka_consumer_running": self.running
                })
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return jsonify({
                    "status": "unhealthy",
                    "error": str(e)
                }), 500
        
        @self.app.route('/messages', methods=['GET'])
        def get_messages():
            """Get messages from database with optional pagination"""
            try:
                limit = request.args.get('limit', 100, type=int)
                offset = request.args.get('offset', 0, type=int)
                
                conn = self.db_pool.getconn()
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute("""
                            SELECT id, message, created_at, processed_at 
                            FROM text_messages 
                            ORDER BY processed_at DESC 
                            LIMIT %s OFFSET %s
                        """, (limit, offset))
                        messages = cursor.fetchall()
                        
                        # Get total count
                        cursor.execute("SELECT COUNT(*) as total FROM text_messages")
                        total = cursor.fetchone()['total']
                        
                    return jsonify({
                        "messages": [dict(msg) for msg in messages],
                        "total": total,
                        "limit": limit,
                        "offset": offset
                    })
                finally:
                    self.db_pool.putconn(conn)
                    
            except Exception as e:
                logger.error(f"Failed to get messages: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/messages/<message_id>', methods=['GET'])
        def get_message(message_id):
            """Get a specific message by ID"""
            try:
                conn = self.db_pool.getconn()
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute("""
                            SELECT id, message, created_at, processed_at 
                            FROM text_messages 
                            WHERE id = %s
                        """, (message_id,))
                        message = cursor.fetchone()
                        
                    if message:
                        return jsonify(dict(message))
                    else:
                        return jsonify({"error": "Message not found"}), 404
                finally:
                    self.db_pool.putconn(conn)
                    
            except Exception as e:
                logger.error(f"Failed to get message {message_id}: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/messages', methods=['POST'])
        def create_message():
            """Manually create a message (for testing)"""
            try:
                data = request.get_json()
                if not data or 'message' not in data:
                    return jsonify({"error": "Message content required"}), 400
                
                message_id = data.get('id', str(uuid.uuid4()))
                message_content = data['message']
                
                self._store_message(message_id, message_content)
                
                return jsonify({
                    "id": message_id,
                    "message": message_content,
                    "status": "created"
                }), 201
                
            except Exception as e:
                logger.error(f"Failed to create message: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """Get message statistics"""
            try:
                conn = self.db_pool.getconn()
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        # Get total count
                        cursor.execute("SELECT COUNT(*) as total FROM text_messages")
                        total = cursor.fetchone()['total']
                        
                        # Get recent count (last hour)
                        cursor.execute("""
                            SELECT COUNT(*) as recent 
                            FROM text_messages 
                            WHERE processed_at > NOW() - INTERVAL '1 hour'
                        """)
                        recent = cursor.fetchone()['recent']
                        
                        # Get oldest and newest
                        cursor.execute("""
                            SELECT 
                                MIN(processed_at) as oldest,
                                MAX(processed_at) as newest
                            FROM text_messages
                        """)
                        time_stats = cursor.fetchone()
                        
                    return jsonify({
                        "total_messages": total,
                        "recent_messages_1h": recent,
                        "oldest_message": time_stats['oldest'].isoformat() if time_stats['oldest'] else None,
                        "newest_message": time_stats['newest'].isoformat() if time_stats['newest'] else None,
                        "kafka_consumer_running": self.running
                    })
                finally:
                    self.db_pool.putconn(conn)
                    
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
                return jsonify({"error": str(e)}), 500
    
    def _store_message(self, message_id: str, message_content: str):
        """Store a message in the database"""
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO text_messages (id, message) 
                    VALUES (%s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (message_id, message_content))
                conn.commit()
                logger.info(f"Stored message: {message_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store message {message_id}: {e}")
            raise
        finally:
            self.db_pool.putconn(conn)
    
    def _kafka_consumer_worker(self):
        """Kafka consumer worker thread"""
        kafka_config = self.config['kafka']
        
        try:
            self.consumer = KafkaConsumer(
                kafka_config['input_topic'],
                bootstrap_servers=kafka_config['bootstrap_servers'],
                group_id=kafka_config['consumer_group'],
                auto_offset_reset=kafka_config['auto_offset_reset'],
                enable_auto_commit=kafka_config['enable_auto_commit'],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None
            )
            
            logger.info(f"Kafka consumer started for topic: {kafka_config['input_topic']}")
            
            for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    data = message.value
                    if data and 'id' in data and 'text' in data:
                        self._store_message(data['id'], data['text'])
                    else:
                        logger.warning(f"Invalid message format: {data}")
                        
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}")
                    
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
                logger.info("Kafka consumer closed")
    
    def start_kafka_consumer(self):
        """Start the Kafka consumer in a separate thread"""
        if not self.running:
            self.running = True
            self.consumer_thread = threading.Thread(target=self._kafka_consumer_worker)
            self.consumer_thread.daemon = True
            self.consumer_thread.start()
            logger.info("Kafka consumer thread started")
    
    def stop_kafka_consumer(self):
        """Stop the Kafka consumer"""
        if self.running:
            self.running = False
            if self.consumer:
                self.consumer.close()
            if self.consumer_thread:
                self.consumer_thread.join(timeout=5)
            logger.info("Kafka consumer stopped")
    
    def run(self):
        """Run the Flask application"""
        self.start_kafka_consumer()
        
        try:
            flask_config = self.config['flask']
            self.app.run(
                host=flask_config['host'],
                port=flask_config['port'],
                debug=flask_config['debug']
            )
        except KeyboardInterrupt:
            logger.info("Shutting down service...")
        finally:
            self.stop_kafka_consumer()

def main():
    """Main entry point"""
    service = TextWriterService()
    service.run()

if __name__ == "__main__":
    main()