#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test all required imports"""
    try:
        logger.info("Testing basic imports...")
        
        # Test Flask
        import flask
        logger.info("✅ Flask imported successfully")
        
        # Test Kafka
        import kafka
        logger.info("✅ Kafka imported successfully")
        
        # Test YAML
        import yaml
        logger.info("✅ YAML imported successfully")
        
        # Test NumPy
        import numpy
        logger.info("✅ NumPy imported successfully")
        
        # Test Pandas
        import pandas
        logger.info("✅ Pandas imported successfully")
        
        # Test Requests
        import requests
        logger.info("✅ Requests imported successfully")
        
        logger.info("Testing database adapters...")
        
        # Test PostgreSQL
        try:
            import psycopg2
            logger.info("✅ PostgreSQL (psycopg2) imported successfully")
        except ImportError as e:
            logger.warning(f"⚠️ PostgreSQL not available: {e}")
        
        logger.info("Testing local modules...")
        
        # Test database factory
        from databases.database_factory import DatabaseFactory
        logger.info("✅ DatabaseFactory imported successfully")
        
        # Test PostgreSQL adapter
        try:
            from databases.postgres_adapter import PostgresAdapter
            logger.info("✅ PostgresAdapter imported successfully")
        except ImportError as e:
            logger.warning(f"⚠️ PostgresAdapter not available: {e}")
        
        logger.info("🎉 All import tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
