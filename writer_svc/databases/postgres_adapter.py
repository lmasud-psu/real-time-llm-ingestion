import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, List
import logging
import json

logger = logging.getLogger(__name__)

class PostgresAdapter:
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        
    def connect(self):
        """Connect to PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Connected to PostgreSQL at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
            
    def create_table(self, table_name: str, schema: Dict[str, Any] = None):
        """Create a new table in PostgreSQL"""
        try:
            if not self.conn:
                self.connect()
                
            cursor = self.conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_name,))
            
            if cursor.fetchone()[0]:
                logger.info(f"Table {table_name} already exists")
                return
                
            # Create table with default schema for embeddings
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id VARCHAR(255) PRIMARY KEY,
                    text TEXT NOT NULL,
                    embedding vector(384),  -- Default embedding dimension
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    source VARCHAR(255),
                    metadata JSONB
                );
            """
            
            cursor.execute(create_table_sql)
            self.conn.commit()
            logger.info(f"Created table {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
                
    def insert_data(self, table_name: str, data: List[Dict[str, Any]]):
        """Insert data into a table"""
        try:
            if not self.conn:
                self.connect()
                
            cursor = self.conn.cursor()
            
            for record in data:
                # Convert embedding list to PostgreSQL vector format
                embedding_str = f"[{','.join(map(str, record.get('embedding', [])))}]"
                
                insert_sql = f"""
                    INSERT INTO {table_name} (id, text, embedding, timestamp, source, metadata)
                    VALUES (%s, %s, %s::vector, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        text = EXCLUDED.text,
                        embedding = EXCLUDED.embedding,
                        timestamp = EXCLUDED.timestamp,
                        source = EXCLUDED.source,
                        metadata = EXCLUDED.metadata;
                """
                
                cursor.execute(insert_sql, (
                    record.get('id'),
                    record.get('text'),
                    embedding_str,
                    record.get('timestamp'),
                    record.get('source'),
                    json.dumps(record.get('metadata', {}))
                ))
                
            self.conn.commit()
            logger.info(f"Inserted {len(data)} records into {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to insert data into {table_name}: {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
                
    def query_table(self, table_name: str, query: str = None, limit: int = 10):
        """Query data from a table"""
        try:
            if not self.conn:
                self.connect()
                
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            if query:
                # For similarity search, you would use vector operations
                # This is a basic text search example
                search_sql = f"""
                    SELECT * FROM {table_name} 
                    WHERE text ILIKE %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s;
                """
                cursor.execute(search_sql, (f"%{query}%", limit))
            else:
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT %s;", (limit,))
                
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to query table {table_name}: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
                
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL connection closed")
