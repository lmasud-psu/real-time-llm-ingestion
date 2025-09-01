# LanceDB

Vector database for storing and searching embeddings with high performance and simple API.

## Quick Start

Get LanceDB environment ready and test it with basic operations.

```bash
# Start environment
docker compose up -d

# Check status
docker compose ps

# Test CLI (runs locally, not in container)
python lancedb_cli.py list-tables
```

## Services

- **LanceDB Environment**: Python container with dependencies installed (port 9090)
- **Data Storage**: Persistent volume at `/data`

## CLI Tool

Install dependencies and use the command-line interface locally.

```bash
# Install dependencies
pip install -r requirements.txt

# Basic commands
python lancedb_cli.py list-tables
python lancedb_cli.py create-table embeddings
python lancedb_cli.py read-table embeddings
python lancedb_cli.py delete-table embeddings
```

## Examples

Create tables and work with vector data.

```bash
# Create table with sample data
python lancedb_cli.py create-table embeddings
python lancedb_cli.py create-sample-data embeddings --num-records 5

# Insert custom data
python lancedb_cli.py insert-data embeddings data.json

# Vector similarity search
python lancedb_cli.py search-similar embeddings query.json --limit 3
```

## Data Format

JSON files for inserting data into tables.

```json
[
  {
    "id": "msg-1",
    "text": "Hello world",
    "embedding": [0.1, 0.2, 0.3, ...],
    "timestamp": 1234567890
  }
]
```

## How It Works

LanceDB runs as a Python library that creates local database files. The Docker container provides a consistent environment with all dependencies installed, but you run the CLI tool locally to interact with the database.
