#!/usr/bin/env python3
"""
PostgreSQL Migration Runner
"""

import psycopg2
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run all PostgreSQL migrations"""
    try:
        # Database connection parameters
        db_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'embeddings_db'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
        }
        
        # Connect to database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        logger.info("Connected to PostgreSQL database")
        
        # Get migrations directory
        migrations_dir = Path(__file__).parent
        
        # Run SQL migrations in order
        sql_files = sorted([f for f in migrations_dir.glob("*.sql")])
        
        for sql_file in sql_files:
            logger.info(f"Running migration: {sql_file.name}")
            
            with open(sql_file, 'r') as f:
                sql_content = f.read()
                
            # Split SQL content by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    cursor.execute(statement)
                    
            conn.commit()
            logger.info(f"Migration {sql_file.name} completed successfully")
            
        logger.info("All PostgreSQL migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migrations()
