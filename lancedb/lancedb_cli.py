#!/usr/bin/env python3
"""
LanceDB CLI Tool
A command-line interface for managing LanceDB databases and tables.
"""

import json
import sys
import time
from typing import List, Optional, Dict, Any
import click
import lancedb
import pandas as pd
import numpy as np


class LanceDBCLI:
    def __init__(self, db_path: str = "./lancedb_data"):
        """Initialize the LanceDB CLI with database path."""
        self.db_path = db_path
        self.db = None
        
    def _get_connection(self):
        """Get or create database connection."""
        if self.db is None:
            try:
                self.db = lancedb.connect(self.db_path)
            except Exception as e:
                click.echo(f"Error connecting to LanceDB: {e}", err=True)
                raise
        return self.db
    
    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        try:
            db = self._get_connection()
            tables = db.table_names()
            return tables
        except Exception as e:
            click.echo(f"Error listing tables: {e}", err=True)
            return []
    
    def create_table(self, table_name: str, data: List[Dict] = None, schema: Dict = None) -> bool:
        """Create a new table with optional initial data."""
        try:
            db = self._get_connection()
            
            if data is None:
                # Create empty table with default schema
                data = [{"id": "sample", "text": "sample text", "embedding": [0.1] * 384}]
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Create table
            table = db.create_table(table_name, data=df, mode="overwrite")
            click.echo(f"Successfully created table '{table_name}' with {len(data)} initial records")
            return True
            
        except Exception as e:
            click.echo(f"Error creating table '{table_name}': {e}", err=True)
            return False
    
    def delete_table(self, table_name: str) -> bool:
        """Delete a table."""
        try:
            db = self._get_connection()
            db.drop_table(table_name)
            click.echo(f"Successfully deleted table '{table_name}'")
            return True
            
        except Exception as e:
            click.echo(f"Error deleting table '{table_name}': {e}", err=True)
            return False
    
    def delete_all_tables(self) -> bool:
        """Delete all tables."""
        try:
            db = self._get_connection()
            tables = db.table_names()
            
            if not tables:
                click.echo("No tables found to delete.")
                return True
            
            click.echo(f"Found {len(tables)} tables to delete: {', '.join(tables)}")
            
            if not click.confirm("Are you sure you want to delete all tables?"):
                click.echo("Operation cancelled.")
                return False
            
            for table_name in tables:
                db.drop_table(table_name)
            
            click.echo(f"Successfully deleted {len(tables)} tables.")
            return True
            
        except Exception as e:
            click.echo(f"Error deleting tables: {e}", err=True)
            return False
    
    def insert_data(self, table_name: str, data_source: str) -> bool:
        """Insert data from a JSON file or data list into a table."""
        try:
            # Check if data_source is a file path or data
            if isinstance(data_source, str) and (data_source.endswith('.json') or '/' in data_source):
                # Load data from file
                with open(data_source, 'r') as f:
                    data = json.load(f)
            else:
                # Assume it's already data
                data = data_source
            
            if not isinstance(data, list):
                data = [data]
            
            db = self._get_connection()
            table = db.open_table(table_name)
            
            # Convert to DataFrame and insert
            df = pd.DataFrame(data)
            table.add(df)
            
            click.echo(f"Successfully inserted {len(data)} records into table '{table_name}'")
            return True
            
        except Exception as e:
            click.echo(f"Error inserting data: {e}", err=True)
            return False
    
    def read_table(self, table_name: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Read data from a table."""
        try:
            db = self._get_connection()
            table = db.open_table(table_name)
            
            # Get total count
            total_count = table.count_rows()
            
            # Read data with pagination
            data = table.to_pandas()
            
            if offset >= len(data):
                return []
            
            end_idx = min(offset + limit, len(data))
            result_data = data.iloc[offset:end_idx]
            
            return result_data.to_dict('records')
            
        except Exception as e:
            click.echo(f"Error reading table '{table_name}': {e}", err=True)
            return []
    
    def search_similar(self, table_name: str, query_embedding: List[float], 
                      limit: int = 5, metric: str = "cosine") -> List[Dict[str, Any]]:
        """Search for similar vectors in a table."""
        try:
            db = self._get_connection()
            table = db.open_table(table_name)
            
            # Perform vector search
            results = table.search(query_embedding).metric(metric).limit(limit).to_pandas()
            
            return results.to_dict('records')
            
        except Exception as e:
            click.echo(f"Error performing similarity search: {e}", err=True)
            return []
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a table."""
        try:
            db = self._get_connection()
            table = db.open_table(table_name)
            
            # Get table statistics
            schema = table.schema
            count = table.count_rows()
            
            info = {
                'table_name': table_name,
                'row_count': count,
                'schema': str(schema),
                'columns': list(schema.names)
            }
            
            return info
            
        except Exception as e:
            click.echo(f"Error getting table info: {e}", err=True)
            return None
    
    def create_sample_data(self, table_name: str, num_records: int = 10, 
                          vector_dim: int = 384) -> bool:
        """Create sample data for testing."""
        try:
            sample_data = []
            
            for i in range(num_records):
                record = {
                    "id": f"sample-{i}",
                    "text": f"This is sample text number {i}",
                    "embedding": np.random.rand(vector_dim).tolist(),
                    "timestamp": time.time(),
                    "category": f"category-{i % 3}"
                }
                sample_data.append(record)
            
            # Insert sample data directly
            db = self._get_connection()
            table = db.open_table(table_name)
            
            # Convert to DataFrame and insert
            df = pd.DataFrame(sample_data)
            table.add(df)
            
            click.echo(f"Successfully created {num_records} sample records in table '{table_name}'")
            return True
            
        except Exception as e:
            click.echo(f"Error creating sample data: {e}", err=True)
            return False
    
    def close(self):
        """Close the database connection."""
        # LanceDB connections are stateless, no need to close
        pass


@click.group()
@click.option('--db-path', default='./lancedb_data', help='LanceDB database path (default: ./lancedb_data)')
@click.pass_context
def cli(ctx, db_path):
    """LanceDB CLI Tool for database management and vector operations."""
    ctx.ensure_object(dict)
    ctx.obj['lancedb_cli'] = LanceDBCLI(db_path)


@cli.command()
@click.pass_context
def list_tables(ctx):
    """List all tables in the database."""
    lancedb_cli = ctx.obj['lancedb_cli']
    try:
        tables = lancedb_cli.list_tables()
        if tables:
            click.echo("Available tables:")
            for table in tables:
                click.echo(f"  - {table}")
        else:
            click.echo("No tables found.")
    finally:
        lancedb_cli.close()


@cli.command()
@click.argument('table_name')
@click.option('--data-file', help='JSON file with initial data')
@click.pass_context
def create_table(ctx, table_name, data_file):
    """Create a new table."""
    lancedb_cli = ctx.obj['lancedb_cli']
    try:
        if data_file:
            # Load data from file
            with open(data_file, 'r') as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = [data]
        else:
            data = None
        
        lancedb_cli.create_table(table_name, data)
    finally:
        lancedb_cli.close()


@cli.command()
@click.argument('table_name')
@click.pass_context
def delete_table(ctx, table_name):
    """Delete a table."""
    lancedb_cli = ctx.obj['lancedb_cli']
    try:
        lancedb_cli.delete_table(table_name)
    finally:
        lancedb_cli.close()


@cli.command()
@click.pass_context
def delete_all_tables(ctx):
    """Delete all tables."""
    lancedb_cli = ctx.obj['lancedb_cli']
    try:
        lancedb_cli.delete_all_tables()
    finally:
        lancedb_cli.close()


@cli.command()
@click.argument('table_name')
@click.option('--limit', default=10, help='Number of records to return (default: 10)')
@click.option('--offset', default=0, help='Number of records to skip (default: 0)')
@click.pass_context
def read_table(ctx, table_name, limit, offset):
    """Read data from a table."""
    lancedb_cli = ctx.obj['lancedb_cli']
    try:
        results = lancedb_cli.read_table(table_name, limit, offset)
        if results:
            click.echo(f"Records from table '{table_name}':")
            for record in results:
                click.echo(f"  {record}")
        else:
            click.echo(f"No records found in table '{table_name}'")
    finally:
        lancedb_cli.close()


@cli.command()
@click.argument('table_name')
@click.argument('data_file')
@click.pass_context
def insert_data(ctx, table_name, data_file):
    """Insert data from a JSON file into a table."""
    lancedb_cli = ctx.obj['lancedb_cli']
    try:
        lancedb_cli.insert_data(table_name, data_file)
    finally:
        lancedb_cli.close()


@cli.command()
@click.argument('table_name')
@click.argument('query_embedding_file')
@click.option('--limit', default=5, help='Number of results (default: 5)')
@click.option('--metric', default='cosine', help='Distance metric (default: cosine)')
@click.pass_context
def search_similar(ctx, table_name, query_embedding_file, limit, metric):
    """Search for similar vectors."""
    lancedb_cli = ctx.obj['lancedb_cli']
    try:
        # Load query embedding from file
        with open(query_embedding_file, 'r') as f:
            embedding_data = json.load(f)
            query_embedding = embedding_data.get('embedding', [])
        
        if not query_embedding:
            click.echo("Error: No embedding found in file", err=True)
            return
        
        results = lancedb_cli.search_similar(table_name, query_embedding, limit, metric)
        if results:
            click.echo(f"Similarity search results (metric: {metric}):")
            for result in results:
                click.echo(f"  {result}")
        else:
            click.echo("No similar vectors found.")
    finally:
        lancedb_cli.close()


@cli.command()
@click.argument('table_name')
@click.pass_context
def table_info(ctx, table_name):
    """Get detailed information about a table."""
    lancedb_cli = ctx.obj['lancedb_cli']
    try:
        info = lancedb_cli.get_table_info(table_name)
        if info:
            click.echo(f"Table Information for '{table_name}':")
            click.echo(f"  Row Count: {info['row_count']}")
            click.echo(f"  Columns: {', '.join(info['columns'])}")
            click.echo(f"  Schema: {info['schema']}")
        else:
            click.echo(f"Table '{table_name}' not found.")
    finally:
        lancedb_cli.close()


@cli.command()
@click.argument('table_name')
@click.option('--num-records', default=10, help='Number of sample records (default: 10)')
@click.option('--vector-dim', default=384, help='Vector dimension (default: 384)')
@click.pass_context
def create_sample_data(ctx, table_name, num_records, vector_dim):
    """Create sample data for testing."""
    lancedb_cli = ctx.obj['lancedb_cli']
    try:
        lancedb_cli.create_sample_data(table_name, num_records, vector_dim)
    finally:
        lancedb_cli.close()


if __name__ == '__main__':
    cli()
