#!/usr/bin/env python3
"""
PostgreSQL pgvector CLI Tool
A command-line interface for managing PostgreSQL databases with pgvector extension.
"""

import json
import sys
import time
from typing import List, Optional, Dict, Any
import click
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np


class PgVectorCLI:
    def __init__(self, host: str = "localhost", port: int = 5432, database: str = "embeddings_db", 
                 user: str = "postgres", password: str = "postgres"):
        """Initialize the PostgreSQL CLI with connection settings."""
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        
    def _get_connection(self):
        """Get or create database connection."""
        if self.connection is None or self.connection.closed:
            try:
                self.connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                self.connection.autocommit = True
            except psycopg2.Error as e:
                click.echo(f"Error connecting to database: {e}", err=True)
                raise
        return self.connection
    
    def _execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        """Execute a SQL query and return results."""
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                return cursor.rowcount
        except psycopg2.Error as e:
            click.echo(f"Database error: {e}", err=True)
            raise

    def _get_table_columns(self, table_name: str) -> List[str]:
        """Return list of column names for a given table (in public schema)."""
        q = (
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s"
        )
        rows = self._execute_query(q, (table_name,))
        return [r['column_name'] for r in rows]
    
    def list_tables(self) -> List[Dict[str, Any]]:
        """List all tables in the database."""
        query = """
        SELECT 
            table_name,
            description,
            vector_dimension,
            model_name,
            created_at
        FROM table_metadata 
        ORDER BY table_name
        """
        try:
            results = self._execute_query(query)
            return results
        except Exception as e:
            click.echo(f"Error listing tables: {e}", err=True)
            return []
    
    def create_table(self, table_name: str, vector_dimension: int = 384, 
                    model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
                    description: str = "") -> bool:
        """Create a new table with pgvector support."""
        try:
            # Create the table
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                message_id VARCHAR(255) UNIQUE NOT NULL,
                original_text TEXT NOT NULL,
                embedding vector({vector_dimension}),
                model_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            self._execute_query(create_table_query, fetch=False)
            
            # Create vector index
            index_query = f"""
            CREATE INDEX IF NOT EXISTS {table_name}_vector_idx 
            ON {table_name} USING ivfflat (embedding vector_cosine_ops) 
            WITH (lists = 100)
            """
            self._execute_query(index_query, fetch=False)
            
            # Create trigger for updated_at
            trigger_function_query = """
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
            """
            self._execute_query(trigger_function_query, fetch=False)
            
            trigger_query = f"""
            CREATE TRIGGER update_{table_name}_updated_at 
                BEFORE UPDATE ON {table_name} 
                FOR EACH ROW 
                EXECUTE FUNCTION update_updated_at_column()
            """
            self._execute_query(trigger_query, fetch=False)
            
            # Add metadata
            metadata_query = """
            INSERT INTO table_metadata (table_name, description, vector_dimension, model_name) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (table_name) DO UPDATE SET
                description = EXCLUDED.description,
                vector_dimension = EXCLUDED.vector_dimension,
                model_name = EXCLUDED.model_name
            """
            self._execute_query(metadata_query, (table_name, description, vector_dimension, model_name), fetch=False)
            
            click.echo(f"Successfully created table '{table_name}' with vector dimension {vector_dimension}")
            return True
            
        except Exception as e:
            click.echo(f"Error creating table '{table_name}': {e}", err=True)
            return False
    
    def delete_table(self, table_name: str) -> bool:
        """Delete a table and its metadata."""
        try:
            # Drop the table
            drop_table_query = f"DROP TABLE IF EXISTS {table_name} CASCADE"
            self._execute_query(drop_table_query, fetch=False)
            
            # Remove metadata
            delete_metadata_query = "DELETE FROM table_metadata WHERE table_name = %s"
            self._execute_query(delete_metadata_query, (table_name,), fetch=False)
            
            click.echo(f"Successfully deleted table '{table_name}'")
            return True
            
        except Exception as e:
            click.echo(f"Error deleting table '{table_name}': {e}", err=True)
            return False
    
    def delete_all_tables(self) -> bool:
        """Delete all user tables (except system tables)."""
        try:
            # Get all user tables
            tables_query = """
            SELECT table_name FROM table_metadata 
            WHERE table_name NOT IN ('table_metadata')
            """
            results = self._execute_query(tables_query)
            
            if not results:
                click.echo("No user tables found to delete.")
                return True
            
            table_names = [row['table_name'] for row in results]
            click.echo(f"Found {len(table_names)} tables to delete: {', '.join(table_names)}")
            
            if not click.confirm("Are you sure you want to delete all tables?"):
                click.echo("Operation cancelled.")
                return False
            
            # Delete each table
            for table_name in table_names:
                self.delete_table(table_name)
            
            click.echo(f"Successfully deleted {len(table_names)} tables.")
            return True
            
        except Exception as e:
            click.echo(f"Error deleting tables: {e}", err=True)
            return False
    
    def insert_embedding(self, table_name: str, message_id: str, original_text: str, 
                        embedding: List[float], model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> bool:
        """Insert an embedding into a table."""
        try:
            query = f"""
            INSERT INTO {table_name} (message_id, original_text, embedding, model_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (message_id) DO UPDATE SET
                original_text = EXCLUDED.original_text,
                embedding = EXCLUDED.embedding,
                model_name = EXCLUDED.model_name,
                updated_at = CURRENT_TIMESTAMP
            """
            self._execute_query(query, (message_id, original_text, embedding, model_name), fetch=False)
            click.echo(f"Successfully inserted/updated embedding for message '{message_id}'")
            return True
            
        except Exception as e:
            click.echo(f"Error inserting embedding: {e}", err=True)
            return False

    def insert_writer_schema(self, table_name: str, record: Dict[str, Any]) -> bool:
        """Insert a record into a writer-service style table (id, text, embedding, timestamp, source, metadata)."""
        try:
            embedding = record.get('embedding', []) or []
            # Normalize to default writer dimension (384): pad with zeros or truncate
            target_dim = 384
            emb_list = [float(x) for x in embedding]
            if len(emb_list) < target_dim:
                emb_list = emb_list + [0.0] * (target_dim - len(emb_list))
            elif len(emb_list) > target_dim:
                emb_list = emb_list[:target_dim]
            embedding_str = f"[{','.join(map(str, emb_list))}]"
            insert_sql = f"""
                INSERT INTO {table_name} (id, text, embedding, timestamp, source, metadata)
                VALUES (%s, %s, %s::vector, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    text = EXCLUDED.text,
                    embedding = EXCLUDED.embedding,
                    timestamp = EXCLUDED.timestamp,
                    source = EXCLUDED.source,
                    metadata = EXCLUDED.metadata
            """
            params = (
                record.get('id'),
                record.get('text'),
                embedding_str,
                record.get('timestamp'),
                record.get('source', 'cli'),
                json.dumps(record.get('metadata', {}))
            )
            self._execute_query(insert_sql, params, fetch=False)
            return True
        except Exception as e:
            click.echo(f"Error inserting writer-schema record: {e}", err=True)
            return False
    
    def read_table(self, table_name: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Read records from a table."""
        try:
            cols = set(self._get_table_columns(table_name))
            if {'message_id', 'original_text', 'model_name', 'created_at'} <= cols:
                # CLI-managed schema
                query = f"""
                SELECT id, message_id, original_text, model_name, created_at, updated_at
                FROM {table_name}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """
                results = self._execute_query(query, (limit, offset))
            else:
                # Writer service schema fallback: id, text, embedding, timestamp, source, metadata
                # Map fields for display
                select_query = f"""
                SELECT 
                  id,
                  id AS message_id,
                  text AS original_text,
                  COALESCE(source, 'unknown') AS model_name,
                  timestamp AS created_at,
                  timestamp AS updated_at
                FROM {table_name}
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
                """
                results = self._execute_query(select_query, (limit, offset))
            return results
            
        except Exception as e:
            click.echo(f"Error reading table '{table_name}': {e}", err=True)
            return []
    

    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a table."""
        try:
            # Get metadata
            metadata_query = "SELECT * FROM table_metadata WHERE table_name = %s"
            metadata_results = self._execute_query(metadata_query, (table_name,))
            
            if not metadata_results:
                click.echo(f"Table '{table_name}' not found in metadata.")
                return None
            
            metadata = metadata_results[0]
            
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_results = self._execute_query(count_query)
            row_count = count_results[0]['count'] if count_results else 0
            
            # Get sample data
            sample_query = f"SELECT * FROM {table_name} LIMIT 1"
            sample_results = self._execute_query(sample_query)
            
            info = {
                'table_name': metadata['table_name'],
                'description': metadata['description'],
                'vector_dimension': metadata['vector_dimension'],
                'model_name': metadata['model_name'],
                'created_at': metadata['created_at'],
                'row_count': row_count,
                'sample_data': sample_results[0] if sample_results else None
            }
            
            return info
            
        except Exception as e:
            click.echo(f"Error getting table info: {e}", err=True)
            return None
    
    def close(self):
        """Close the database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()


@click.group()
@click.option('--host', default='localhost', help='PostgreSQL host (default: localhost)')
@click.option('--port', default=5432, help='PostgreSQL port (default: 5432)')
@click.option('--database', default='embeddings_db', help='Database name (default: embeddings_db)')
@click.option('--user', default='postgres', help='Database user (default: postgres)')
@click.option('--password', default='postgres', help='Database password (default: postgres)')
@click.pass_context
def cli(ctx, host, port, database, user, password):
    """PostgreSQL pgvector CLI Tool for database management and vector operations."""
    ctx.ensure_object(dict)
    ctx.obj['pgvector_cli'] = PgVectorCLI(host, port, database, user, password)


@cli.command()
@click.pass_context
def list_tables(ctx):
    """List all tables in the database."""
    pgvector_cli = ctx.obj['pgvector_cli']
    try:
        tables = pgvector_cli.list_tables()
        if tables:
            click.echo("Available tables:")
            for table in tables:
                click.echo(f"  - {table['table_name']}")
                click.echo(f"    Description: {table['description']}")
                click.echo(f"    Vector Dimension: {table['vector_dimension']}")
                click.echo(f"    Model: {table['model_name']}")
                click.echo(f"    Created: {table['created_at']}")
                click.echo()
        else:
            click.echo("No tables found.")
    finally:
        pgvector_cli.close()


@cli.command()
@click.argument('table_name')
@click.option('--vector-dimension', default=384, help='Vector dimension (default: 384)')
@click.option('--model-name', default='sentence-transformers/all-MiniLM-L6-v2', help='Model name')
@click.option('--description', default='', help='Table description')
@click.pass_context
def create_table(ctx, table_name, vector_dimension, model_name, description):
    """Create a new table with pgvector support."""
    pgvector_cli = ctx.obj['pgvector_cli']
    try:
        pgvector_cli.create_table(table_name, vector_dimension, model_name, description)
    finally:
        pgvector_cli.close()


@cli.command()
@click.argument('table_name')
@click.pass_context
def delete_table(ctx, table_name):
    """Delete a table."""
    pgvector_cli = ctx.obj['pgvector_cli']
    try:
        pgvector_cli.delete_table(table_name)
    finally:
        pgvector_cli.close()


@cli.command()
@click.pass_context
def delete_all_tables(ctx):
    """Delete all user tables."""
    pgvector_cli = ctx.obj['pgvector_cli']
    try:
        pgvector_cli.delete_all_tables()
    finally:
        pgvector_cli.close()


@cli.command()
@click.argument('table_name')
@click.option('--limit', default=10, help='Number of records to return (default: 10)')
@click.option('--offset', default=0, help='Number of records to skip (default: 0)')
@click.pass_context
def read_table(ctx, table_name, limit, offset):
    """Read records from a table."""
    pgvector_cli = ctx.obj['pgvector_cli']
    try:
        results = pgvector_cli.read_table(table_name, limit, offset)
        if results:
            click.echo(f"Records from table '{table_name}':")
            for record in results:
                click.echo(f"  ID: {record['id']}")
                click.echo(f"  Message ID: {record['message_id']}")
                click.echo(f"  Text: {record['original_text'][:100]}...")
                click.echo(f"  Model: {record['model_name']}")
                click.echo(f"  Created: {record['created_at']}")
                click.echo()
        else:
            click.echo(f"No records found in table '{table_name}'")
    finally:
        pgvector_cli.close()


@cli.command()
@click.argument('table_name')
@click.argument('message_id')
@click.argument('text')
@click.argument('embedding_file')
@click.option('--model-name', default='sentence-transformers/all-MiniLM-L6-v2', help='Model name')
@click.pass_context
def insert_embedding(ctx, table_name, message_id, text, embedding_file, model_name):
    """Insert an embedding from a JSON file."""
    pgvector_cli = ctx.obj['pgvector_cli']
    try:
        # Load embedding from file
        with open(embedding_file, 'r') as f:
            embedding_data = json.load(f)
            embedding = embedding_data.get('embedding', [])
        
        if not embedding:
            click.echo("Error: No embedding found in file", err=True)
            return
        
        pgvector_cli.insert_embedding(table_name, message_id, text, embedding, model_name)
    finally:
        pgvector_cli.close()


@cli.command()
@click.argument('table_name')
@click.argument('data_json')
@click.pass_context
def insert_data(ctx, table_name, data_json):
    """Insert data directly from JSON string."""
    pgvector_cli = ctx.obj['pgvector_cli']
    try:
        # Parse JSON data
        try:
            data = json.loads(data_json)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON format: {e}", err=True)
            return
        
        # Extract fields
        message_id = data.get('id')
        text = data.get('text')
        embedding = data.get('embedding', [])
        source = data.get('source', 'cli')

        if not message_id or not text:
            click.echo("Error: Missing required fields 'id' or 'text'", err=True)
            return

        # Detect table schema and insert accordingly
        cols = set(pgvector_cli._get_table_columns(table_name))
        ok = False
        if {'message_id', 'original_text', 'embedding'} <= cols:
            ok = pgvector_cli.insert_embedding(table_name, message_id, text, embedding, source)
        elif {'id', 'text', 'embedding'} <= cols:
            record = {
                'id': message_id,
                'text': text,
                'embedding': embedding,
                'timestamp': data.get('timestamp'),
                'source': source,
                'metadata': data.get('metadata', {})
            }
            ok = pgvector_cli.insert_writer_schema(table_name, record)
        else:
            click.echo("Error: Unrecognized table schema; cannot determine insert format", err=True)
            return

        if ok:
            click.echo(f"Successfully inserted data into table '{table_name}'")
        else:
            click.echo(f"Failed to insert data into table '{table_name}'", err=True)
        
    finally:
        pgvector_cli.close()


@cli.command()
@click.argument('table_name')
@click.option('--limit', default=10, help='Number of records to return (default: 10)')
@click.option('--query', help='Text to search for in the original_text field')
@click.pass_context
def query_table(ctx, table_name, limit, query):
    """Query records from a table with optional text search."""
    pgvector_cli = ctx.obj['pgvector_cli']
    try:
        if query:
            # Search for text in the table
            results = pgvector_cli.search_text(table_name, query, limit)
            if results:
                click.echo(f"Search results for '{query}' in table '{table_name}':")
                for record in results:
                    click.echo(f"  ID: {record['id']}")
                    click.echo(f"  Message ID: {record['message_id']}")
                    click.echo(f"  Text: {record['original_text'][:100]}...")
                    click.echo(f"  Model: {record['model_name']}")
                    click.echo(f"  Created: {record['created_at']}")
                    click.echo()
            else:
                click.echo(f"No results found for '{query}' in table '{table_name}'")
        else:
            # Just read the table
            results = pgvector_cli.read_table(table_name, limit, 0)
            if results:
                click.echo(f"Records from table '{table_name}':")
                for record in results:
                    click.echo(f"  ID: {record['id']}")
                    click.echo(f"  Message ID: {record['message_id']}")
                    click.echo(f"  Text: {record['original_text'][:100]}...")
                    click.echo(f"  Model: {record['model_name']}")
                    click.echo(f"  Created: {record['created_at']}")
                    click.echo()
            else:
                click.echo(f"No records found in table '{table_name}'")
    finally:
        pgvector_cli.close()


@cli.command()
@click.argument('table_name')
@click.pass_context
def table_info(ctx, table_name):
    """Get detailed information about a table."""
    pgvector_cli = ctx.obj['pgvector_cli']
    try:
        info = pgvector_cli.get_table_info(table_name)
        if info:
            click.echo(f"Table Information for '{table_name}':")
            click.echo(f"  Description: {info['description']}")
            click.echo(f"  Vector Dimension: {info['vector_dimension']}")
            click.echo(f"  Model: {info['model_name']}")
            click.echo(f"  Created: {info['created_at']}")
            click.echo(f"  Row Count: {info['row_count']}")
            if info['sample_data']:
                click.echo(f"  Sample Message ID: {info['sample_data']['message_id']}")
        else:
            click.echo(f"Table '{table_name}' not found.")
    finally:
        pgvector_cli.close()


if __name__ == '__main__':
    cli()
