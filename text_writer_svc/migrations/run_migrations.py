#!/usr/bin/env python3

import os
import sys
import psycopg2
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection using environment variables or defaults"""
    return psycopg2.connect(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=int(os.getenv('DATABASE_PORT', '5432')),
        database=os.getenv('DATABASE_NAME', 'text_messages_db'),
        user=os.getenv('DATABASE_USER', 'postgres'),
        password=os.getenv('DATABASE_PASSWORD', 'postgres')
    )

def run_migration(migration_file: str):
    """Run a single migration file"""
    try:
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
            logger.info(f"Successfully applied migration: {migration_file}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to apply migration {migration_file}: {e}")
            raise
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error reading migration file {migration_file}: {e}")
        raise

def run_all_migrations():
    """Run all migration files in order"""
    migrations_dir = Path(__file__).parent
    migration_files = sorted([f for f in migrations_dir.glob("*.sql")])
    
    if not migration_files:
        logger.info("No migration files found")
        return
    
    logger.info(f"Found {len(migration_files)} migration files")
    
    for migration_file in migration_files:
        run_migration(str(migration_file))
    
    logger.info("All migrations completed successfully")

if __name__ == "__main__":
    try:
        run_all_migrations()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)