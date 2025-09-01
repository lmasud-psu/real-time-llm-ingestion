# PostgreSQL pgvector Database

A PostgreSQL database setup with pgvector extension for storing and querying vector embeddings with similarity search capabilities.

## Features

- **PostgreSQL 16** with pgvector extension
- **Automatic indexing** for fast vector queries
- **pgAdmin** web interface for database management
- **Python CLI tool** for database operations
- **Docker Compose** orchestration
- **Health checks** and monitoring

## Quick Start

### 1. Start the Database

```bash
cd pgvector
docker compose up -d
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Test the Setup

```bash
# List tables (should show the default embeddings table)
python pgvector_cli.py list-tables

# Get information about the embeddings table
python pgvector_cli.py table-info embeddings
```

## Services

### PostgreSQL with pgvector
- **Port**: 5432
- **Database**: embeddings_db
- **User**: postgres
- **Password**: postgres
- **Extension**: pgvector enabled

### pgAdmin
- **URL**: http://localhost:8080
- **Email**: admin@example.com
- **Password**: admin

## CLI Tool Usage

### Basic Operations

```bash
# List all tables
python pgvector_cli.py list-tables

# Create a new table
python pgvector_cli.py create-table my_embeddings --vector-dimension 384 --description "My custom embeddings"

# Read table contents
python pgvector_cli.py read-table embeddings --limit 10

# Get table information
python pgvector_cli.py table-info embeddings

# Delete a table
python pgvector_cli.py delete-table my_embeddings

# Delete all tables (with confirmation)
python pgvector_cli.py delete-all-tables
```

### Vector Operations

```bash
# Insert an embedding from JSON file
python pgvector_cli.py insert-embedding embeddings "msg-123" "Hello world" embedding.json
```

### Connection Options

```bash
# Use custom connection settings
python pgvector_cli.py --host localhost --port 5432 --database embeddings_db --user postgres --password postgres list-tables
```

## Management

### Start/Stop Services

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Stop and remove volumes (WARNING: deletes all data)
docker compose down -v

# View logs
docker compose logs -f postgres
docker compose logs -f pgadmin
```

### Database Access

```bash
# Connect via psql
docker exec -it pgvector-postgres psql -U postgres -d embeddings_db

# Connect via pgAdmin
# Open http://localhost:8080
# Login: admin@example.com / admin
# Add server: localhost:5432, postgres/postgres
```


## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if PostgreSQL is running
   docker compose ps
   
   # Check logs
   docker compose logs postgres
   ```

2. **pgvector Extension Not Found**
   ```bash
   # Connect to database and enable extension
   docker exec -it pgvector-postgres psql -U postgres -d embeddings_db
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **Permission Denied**
   ```bash
   # Check file permissions
   chmod 644 init.sql
   chmod +x pgvector_cli.py
   ```

4. **Port Conflicts**
   ```bash
   # Check what's using port 5432
   lsof -i :5432
   
   # Use different port
   docker compose up -d -p 5433:5432
   ```

### Reset Database

```bash
# Stop and remove everything
docker compose down -v

# Remove data volumes
docker volume rm pgvector_postgres_data pgvector_pgadmin_data

# Restart
docker compose up -d
```
