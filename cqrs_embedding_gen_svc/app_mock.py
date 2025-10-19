"""
Simple CQRS Embedding Generation Service (Mock Version)

This is a simplified version that generates mock embeddings for testing purposes.
"""

import logging
import time
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import uuid
import random

import psycopg2
import psycopg2.extras
import numpy as np
from flask import Flask, request, jsonify
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockEmbeddingProcessor:
    """Handles mock embedding generation and database operations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_config = config['database']
        self.embedding_config = config['embedding']
        self.polling_config = config['polling']
        self.last_processed_timestamp = None
        self._running = False
        self._thread = None
        
    def get_db_connection(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            return conn
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def setup_database(self):
        """Create embeddings table if it doesn't exist"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Enable pgvector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create embeddings table
            embedding_dim = self.embedding_config['dimension']
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS text_embeddings (
                id SERIAL PRIMARY KEY,
                text_message_id UUID REFERENCES text_messages(id),
                text_content TEXT NOT NULL,
                embedding VECTOR({embedding_dim}) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(text_message_id)
            );
            """
            cursor.execute(create_table_sql)
            
            # Create index for vector similarity search
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS text_embeddings_embedding_idx 
                ON text_embeddings USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Database setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            raise
    
    def get_unprocessed_messages(self) -> List[Dict[str, Any]]:
        """Fetch unprocessed text messages from the database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Use timestamp-based filtering if we have processed messages before
            if self.last_processed_timestamp:
                query = """
                SELECT tm.id, tm.content, tm.created_at
                FROM text_messages tm
                LEFT JOIN text_embeddings te ON tm.id = te.text_message_id
                WHERE tm.created_at > %s AND te.text_message_id IS NULL
                ORDER BY tm.created_at ASC
                LIMIT %s;
                """
                cursor.execute(query, (self.last_processed_timestamp, self.polling_config['batch_size']))
            else:
                # First run - get all unprocessed messages
                query = """
                SELECT tm.id, tm.content, tm.created_at
                FROM text_messages tm
                LEFT JOIN text_embeddings te ON tm.id = te.text_message_id
                WHERE te.text_message_id IS NULL
                ORDER BY tm.created_at ASC
                LIMIT %s;
                """
                cursor.execute(query, (self.polling_config['batch_size'],))
            
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error fetching unprocessed messages: {e}")
            return []
    
    def generate_mock_embedding(self, text: str) -> np.ndarray:
        """Generate mock embedding for given text (for testing purposes)"""
        try:
            # Create deterministic mock embedding based on text hash
            text_hash = hash(text)
            random.seed(text_hash)
            
            # Generate random embedding of specified dimension
            embedding = np.array([random.uniform(-1, 1) for _ in range(self.embedding_config['dimension'])])
            
            # Normalize the embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating mock embedding: {e}")
            raise
    
    def store_embedding(self, message_id: str, text_content: str, embedding: np.ndarray):
        """Store embedding in the database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Convert numpy array to list for JSON serialization
            embedding_list = embedding.tolist()
            
            insert_sql = """
            INSERT INTO text_embeddings (text_message_id, text_content, embedding)
            VALUES (%s, %s, %s)
            ON CONFLICT (text_message_id) DO NOTHING;
            """
            
            cursor.execute(insert_sql, (message_id, text_content, embedding_list))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info(f"Stored mock embedding for message ID: {message_id}")
            
        except Exception as e:
            logger.error(f"Error storing embedding for message {message_id}: {e}")
            raise
    
    def process_batch(self, messages: List[Dict[str, Any]]):
        """Process a batch of messages"""
        for message in messages:
            try:
                message_id = str(message['id'])
                text_content = message['content']
                
                # Generate mock embedding
                embedding = self.generate_mock_embedding(text_content)
                
                # Store embedding
                self.store_embedding(message_id, text_content, embedding)
                
                # Update last processed timestamp
                message_timestamp = message['created_at']
                if self.last_processed_timestamp is None or message_timestamp > self.last_processed_timestamp:
                    self.last_processed_timestamp = message_timestamp
                
                logger.info(f"Processed message ID: {message_id}")
                
            except Exception as e:
                logger.error(f"Error processing message {message['id']}: {e}")
                continue
    
    def polling_loop(self):
        """Main polling loop for processing new messages"""
        logger.info("Starting mock embedding processor polling loop")
        
        while self._running:
            try:
                # Fetch unprocessed messages
                messages = self.get_unprocessed_messages()
                
                if messages:
                    logger.info(f"Found {len(messages)} unprocessed messages")
                    self.process_batch(messages)
                else:
                    logger.debug("No unprocessed messages found")
                
                # Sleep before next poll
                time.sleep(self.polling_config['interval_seconds'])
                
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                time.sleep(self.polling_config['error_retry_seconds'])
    
    def start(self):
        """Start the background processing thread"""
        if self._running:
            logger.warning("Processor already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self.polling_loop, daemon=True)
        self._thread.start()
        logger.info("Mock embedding processor started")
    
    def stop(self):
        """Stop the background processing thread"""
        if not self._running:
            logger.warning("Processor not running")
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Mock embedding processor stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get processor status"""
        return {
            'running': self._running,
            'last_processed_timestamp': self.last_processed_timestamp.isoformat() if self.last_processed_timestamp else None,
            'model_type': 'mock',
            'timestamp': datetime.now().isoformat()
        }

# Load configuration
def load_config(config_path: str = 'config.yaml') -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise

# Flask app setup
app = Flask(__name__)
processor = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'cqrs-embedding-gen-mock'}), 200

@app.route('/status', methods=['GET'])
def get_status():
    """Get processor status"""
    if processor:
        return jsonify(processor.get_status()), 200
    else:
        return jsonify({'error': 'Processor not initialized'}), 500

@app.route('/start', methods=['POST'])
def start_processor():
    """Start the embedding processor"""
    try:
        if processor:
            processor.start()
            return jsonify({'message': 'Processor started'}), 200
        else:
            return jsonify({'error': 'Processor not initialized'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stop', methods=['POST'])
def stop_processor():
    """Stop the embedding processor"""
    try:
        if processor:
            processor.stop()
            return jsonify({'message': 'Processor stopped'}), 200
        else:
            return jsonify({'error': 'Processor not initialized'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process-batch', methods=['POST'])
def process_batch_manually():
    """Manually trigger batch processing"""
    try:
        if not processor:
            return jsonify({'error': 'Processor not initialized'}), 500
        
        messages = processor.get_unprocessed_messages()
        if messages:
            processor.process_batch(messages)
            return jsonify({
                'message': f'Processed {len(messages)} messages',
                'processed_count': len(messages)
            }), 200
        else:
            return jsonify({'message': 'No unprocessed messages found'}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/embeddings/search', methods=['POST'])
def search_embeddings():
    """Search for similar embeddings using mock similarity"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query text required'}), 400
        
        query_text = data['query']
        limit = data.get('limit', 10)
        
        if not processor:
            return jsonify({'error': 'Processor not initialized'}), 500
        
        # Generate embedding for query
        query_embedding = processor.generate_mock_embedding(query_text)
        
        # Search database (simplified - just return recent embeddings)
        conn = processor.get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        search_sql = """
        SELECT 
            te.id,
            te.text_content,
            te.created_at,
            0.5 as distance
        FROM text_embeddings te
        ORDER BY te.created_at DESC
        LIMIT %s;
        """
        
        cursor.execute(search_sql, (limit,))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'query': query_text,
            'results': [dict(row) for row in results],
            'note': 'Using mock similarity scores'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def initialize_app():
    """Initialize the application"""
    global processor
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize processor
        processor = MockEmbeddingProcessor(config)
        processor.setup_database()
        
        # Auto-start if configured
        if config.get('auto_start', False):
            processor.start()
        
        logger.info("Mock embedding application initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        raise

if __name__ == '__main__':
    initialize_app()
    
    # Start Flask app
    app.run(
        host='0.0.0.0',
        port=5003,
        debug=False
    )