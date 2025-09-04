from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseFactory:
    @staticmethod
    def create_adapter(db_type: str, config: Dict[str, Any]):
        """Create a database adapter based on the specified type"""
        try:
            if db_type.lower() == "lancedb":
                try:
                    from .lancedb_adapter import LanceDBAdapter
                    data_path = config.get("lancedb", {}).get("data_path", "./lancedb_data")
                    return LanceDBAdapter(data_path)
                except ImportError as e:
                    logger.error(f"LanceDB adapter not available: {e}")
                    raise ImportError("LanceDB adapter not available. Please install lancedb: pip install lancedb")
                
            elif db_type.lower() == "postgres":
                try:
                    from .postgres_adapter import PostgresAdapter
                    postgres_config = config.get("postgres", {})
                    return PostgresAdapter(
                        host=postgres_config.get("host", "localhost"),
                        port=postgres_config.get("port", 5432),
                        database=postgres_config.get("database", "embeddings_db"),
                        user=postgres_config.get("user", "postgres"),
                        password=postgres_config.get("password", "postgres")
                    )
                except ImportError as e:
                    logger.error(f"PostgreSQL adapter not available: {e}")
                    raise ImportError("PostgreSQL adapter not available. Please install psycopg2-binary: pip install psycopg2-binary")
                
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
                
        except Exception as e:
            logger.error(f"Failed to create database adapter for {db_type}: {e}")
            raise
