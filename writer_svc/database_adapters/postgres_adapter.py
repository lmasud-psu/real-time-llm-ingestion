"""
PostgreSQL Adapter for Writer Service
Handles writing embeddings to PostgreSQL database with pgvector.
"""

import logging
import time
import os
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class PostgresAdapter:
    def __init__(self, config: Dict[str, Any]):
        """Initialize PostgreSQL adapter with configuration."""
        self.config = config
        self.connection = None
        self.table_name = config.get('table_name', 'embeddings')
        
        # Database connection parameters from environment variables
        self.host = os.environ.get('DATABASE_HOST', config.get('postgres', {}).get('host', 'localhost'))
        self.port = int(os.environ.get('DATABASE_PORT', config.get('postgres', {}).get('port', 5432)))
        self.database = os.environ.get('DATABASE_NAME', config.get('postgres', {}).get('database', 'embeddings_db'))
        self.user = os.environ.get('DATABASE_USER', config.get('postgres', {}).get('user', 'postgres'))
        self.password = os.environ.get('DATABASE_PASSWORD', config.get('postgres', {}).get('password', 'postgres'))
        
        # Initialize connection
        self._connect()
    
    def _connect(self):
        """Connect to PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.connection.autocommit = True
            logger.info(f"Connected to PostgreSQL at {self.host}:{self.port}/{self.database}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def _ensure_table_exists(self):
        """Ensure the embeddings table exists with proper schema."""
        try:
            with self.connection.cursor() as cursor:
                # Check if table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, (self.table_name,))
                
                if not cursor.fetchone()[0]:
                    # Create table with pgvector support
                    cursor.execute(f"""
                        CREATE TABLE {self.table_name} (
                            id SERIAL PRIMARY KEY,
                            message_id VARCHAR(255) UNIQUE NOT NULL,
                            original_text TEXT NOT NULL,
                            embedding vector(384),
                            model_name VARCHAR(255),
                            timestamp DOUBLE PRECISION,
                            embedding_dimension INTEGER,
                            processing_timestamp DOUBLE PRECISION,
                            input_timestamp DOUBLE PRECISION,
                            input_source VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # Create vector index
                    cursor.execute(f"""
                        CREATE INDEX {self.table_name}_vector_idx 
                        ON {self.table_name} USING ivfflat (embedding vector_cosine_ops) 
                        WITH (lists = 100);
                    """)
                    
                    logger.info(f"Created table '{self.table_name}' with pgvector schema")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to ensure table exists: {e}")
            return False
    
    def write_embedding(self, message_id: str, original_text: str, 
                       embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Write an embedding to the PostgreSQL table."""
        try:
            # Ensure table exists
            if not self._ensure_table_exists():
                return False
            
            # Prepare data
            with self.connection.cursor() as cursor:
                cursor.execute(f"""
                    INSERT INTO {self.table_name} (
                        message_id, original_text, embedding, model_name, 
                        timestamp, embedding_dimension, processing_timestamp, 
                        input_timestamp, input_source
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (message_id) DO UPDATE SET
                        original_text = EXCLUDED.original_text,
                        embedding = EXCLUDED.embedding,
                        model_name = EXCLUDED.model_name,
                        timestamp = EXCLUDED.timestamp,
                        embedding_dimension = EXCLUDED.embedding_dimension,
                        processing_timestamp = EXCLUDED.processing_timestamp,
                        input_timestamp = EXCLUDED.input_timestamp,
                        input_source = EXCLUDED.input_source
                """, (
                    message_id,
                    original_text,
                    embedding,
                    metadata.get('model_name', 'unknown'),
                    metadata.get('timestamp', time.time()),
                    len(embedding),
                    time.time(),
                    metadata.get('timestamp', time.time()),
                    metadata.get('source', 'unknown')
                ))
                
                logger.debug(f"Successfully wrote embedding for message {message_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to write embedding for message {message_id}: {e}")
            return False
    
    def read_embeddings(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Read embeddings from the table."""
        try:
            if not self._ensure_table_exists():
                return []
            
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(f"""
                    SELECT message_id, original_text, model_name, timestamp, 
                           embedding_dimension, input_source, created_at
                    FROM {self.table_name}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to read embeddings: {e}")
            return []
    
    def search_similar(self, query_embedding: List[float], 
                      limit: int = 5, metric: str = "cosine") -> List[Dict[str, Any]]:
        """Search for similar embeddings using pgvector."""
        try:
            if not self._ensure_table_exists():
                return []
            
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(f"""
                    SELECT message_id, original_text, model_name, 
                           1 - (embedding <=> %s) AS similarity
                    FROM {self.table_name}
                    WHERE 1 - (embedding <=> %s) > 0.5
                    ORDER BY embedding <=> %s
                    LIMIT %s
                """, (query_embedding, query_embedding, query_embedding, limit))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to search similar embeddings: {e}")
            return []
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about the embeddings table."""
        try:
            if not self._ensure_table_exists():
                return {}
            
            with self.connection.cursor() as cursor:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                row_count = cursor.fetchone()[0]
                
                # Get schema info
                cursor.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (self.table_name,))
                
                columns = [{"name": row[0], "type": row[1]} for row in cursor.fetchall()]
                
                return {
                    'table_name': self.table_name,
                    'row_count': row_count,
                    'columns': columns
                }
                
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check if the database is healthy."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("PostgreSQL connection closed")
