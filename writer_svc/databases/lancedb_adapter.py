import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Try to import lancedb with better error handling
try:
    import lancedb
    LANCEDB_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LanceDB not available: {e}")
    LANCEDB_AVAILABLE = False
except Exception as e:
    logger.warning(f"Unexpected error importing LanceDB: {e}")
    LANCEDB_AVAILABLE = False

class LanceDBAdapter:
    def __init__(self, data_path: str):
        if not LANCEDB_AVAILABLE:
            raise ImportError("LanceDB is not available. Please install it with: pip install lancedb")
            
        self.data_path = data_path
        self.db = None
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        """Ensure the data directory exists"""
        os.makedirs(self.data_path, exist_ok=True)
        
    def connect(self):
        """Connect to LanceDB"""
        try:
            self.db = lancedb.connect(self.data_path)
            logger.info(f"Connected to LanceDB at {self.data_path}")
        except Exception as e:
            logger.error(f"Failed to connect to LanceDB: {e}")
            raise
            
    def create_table(self, table_name: str, schema: Dict[str, Any] = None):
        """Create a new table in LanceDB"""
        try:
            if not self.db:
                self.connect()
                
            # Default schema for embeddings
            if schema is None:
                schema = {
                    "id": "string",
                    "text": "string", 
                    "embedding": "float32[384]",  # Default embedding dimension
                    "timestamp": "timestamp[ns]",
                    "source": "string"
                }
            
            # Check if table exists
            if table_name in self.db.table_names():
                logger.info(f"Table {table_name} already exists")
                return
                
            # Create empty table with schema
            data = []
            self.db.create_table(table_name, data, schema=schema)
            logger.info(f"Created table {table_name} with schema")
            
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            raise
            
    def insert_data(self, table_name: str, data: List[Dict[str, Any]]):
        """Insert data into a table"""
        try:
            if not self.db:
                self.connect()
                
            table = self.db.open_table(table_name)
            table.add(data)
            logger.info(f"Inserted {len(data)} records into {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to insert data into {table_name}: {e}")
            raise
            
    def query_table(self, table_name: str, query: str = None, limit: int = 10):
        """Query data from a table"""
        try:
            if not self.db:
                self.connect()
                
            table = self.db.open_table(table_name)
            
            if query:
                result = table.search(query).limit(limit).to_pandas()
            else:
                result = table.to_pandas().head(limit)
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to query table {table_name}: {e}")
            raise
