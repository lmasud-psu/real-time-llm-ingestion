#!/usr/bin/env python3
"""
LanceDB Migration: Create embeddings table
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from databases.lancedb_adapter import LanceDBAdapter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to create embeddings table"""
    try:
        # Create adapter
        adapter = LanceDBAdapter("./lancedb_data")
        
        # Define schema for embeddings table
        schema = {
            "id": "string",
            "text": "string",
            "embedding": "float32[384]",  # Default embedding dimension
            "timestamp": "timestamp[ns]",
            "source": "string",
            "metadata": "string"  # JSON string
        }
        
        # Create table
        adapter.create_table("embeddings", schema)
        
        logger.info("Migration 001 completed successfully: embeddings table created")
        
    except Exception as e:
        logger.error(f"Migration 001 failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
