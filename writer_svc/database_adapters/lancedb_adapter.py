"""
LanceDB Adapter for Writer Service
Handles writing embeddings to LanceDB database.
"""

import logging
import time
from typing import Dict, Any, List
import lancedb
import pandas as pd

logger = logging.getLogger(__name__)

class LanceDBAdapter:
    def __init__(self, config: Dict[str, Any]):
        """Initialize LanceDB adapter with configuration."""
        self.config = config
        self.db = None
        self.table_name = config.get('table_name', 'embeddings')
        self.db_path = config.get('db_path', './lancedb_data')
        
        # Initialize connection
        self._connect()
    
    def _connect(self):
        """Connect to LanceDB database."""
        try:
            self.db = lancedb.connect(self.db_path)
            logger.info(f"Connected to LanceDB at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to LanceDB: {e}")
            raise
    
    def _ensure_table_exists(self):
        """Ensure the embeddings table exists with proper schema."""
        try:
            if self.table_name not in self.db.table_names():
                # Create table with sample data to establish schema
                sample_data = [{
                    "id": "sample",
                    "original_text": "sample text",
                    "embedding": [0.1] * 384,
                    "model_name": "sample-model",
                    "timestamp": time.time(),
                    "embedding_dimension": 384,
                    "processing_timestamp": time.time(),
                    "input_timestamp": time.time(),
                    "input_source": "sample"
                }]
                
                df = pd.DataFrame(sample_data)
                self.db.create_table(self.table_name, data=df, mode="overwrite")
                logger.info(f"Created table '{self.table_name}' with schema")
            
            return True
        except Exception as e:
            logger.error(f"Failed to ensure table exists: {e}")
            return False
    
    def write_embedding(self, message_id: str, original_text: str, 
                       embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Write an embedding to the LanceDB table."""
        try:
            # Ensure table exists
            if not self._ensure_table_exists():
                return False
            
            # Prepare data
            embedding_data = {
                "id": message_id,
                "original_text": original_text,
                "embedding": embedding,
                "model_name": metadata.get('model_name', 'unknown'),
                "timestamp": metadata.get('timestamp', time.time()),
                "embedding_dimension": len(embedding),
                "processing_timestamp": time.time(),
                "input_timestamp": metadata.get('timestamp', time.time()),
                "input_source": metadata.get('source', 'unknown')
            }
            
            # Add any additional metadata fields
            for key, value in metadata.items():
                if key not in embedding_data:
                    embedding_data[f"meta_{key}"] = value
            
            # Convert to DataFrame and insert
            df = pd.DataFrame([embedding_data])
            table = self.db.open_table(self.table_name)
            table.add(df)
            
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
            
            table = self.db.open_table(self.table_name)
            data = table.to_pandas()
            
            if offset >= len(data):
                return []
            
            end_idx = min(offset + limit, len(data))
            result_data = data.iloc[offset:end_idx]
            
            return result_data.to_dict('records')
            
        except Exception as e:
            logger.error(f"Failed to read embeddings: {e}")
            return []
    
    def search_similar(self, query_embedding: List[float], 
                      limit: int = 5, metric: str = "cosine") -> List[Dict[str, Any]]:
        """Search for similar embeddings."""
        try:
            if not self._ensure_table_exists():
                return []
            
            table = self.db.open_table(self.table_name)
            results = table.search(query_embedding).metric(metric).limit(limit).to_pandas()
            
            return results.to_dict('records')
            
        except Exception as e:
            logger.error(f"Failed to search similar embeddings: {e}")
            return []
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about the embeddings table."""
        try:
            if not self._ensure_table_exists():
                return {}
            
            table = self.db.open_table(self.table_name)
            schema = table.schema
            count = table.count_rows()
            
            return {
                'table_name': self.table_name,
                'row_count': count,
                'schema': str(schema),
                'columns': list(schema.names)
            }
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check if the database is healthy."""
        try:
            # Try to list tables
            tables = self.db.table_names()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        # LanceDB connections are stateless, no need to close
        pass
