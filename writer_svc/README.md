# Writer Service

A Flask-based service that reads embeddings from Kafka and writes them to either LanceDB or PostgreSQL databases.

## Features

- **Kafka Consumer**: Reads from the `embeddings` topic
- **Database Adapters**: Supports LanceDB and PostgreSQL with pgvector
- **Auto-start**: Service automatically starts consuming messages on startup
- **REST API**: Health checks, statistics, and manual control endpoints
- **Database Migrations**: Automated table creation and schema management

## Configuration

Edit `config.yaml` to configure:
- Kafka connection settings
- Database type (lancedb/postgres)
- Database-specific connection parameters

## Quick Start

### 1. Start Kafka

```bash
cd ../kafka
docker compose up -d
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations

**For LanceDB:**
```bash
python databases/lancedb/migrations/001_create_embeddings_table.py
```

**For PostgreSQL:**
```bash
# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=embeddings_db
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres

# Run migrations
python databases/postgres/migrations/run_migrations.py
```

### 4. Start the Writer Service

```bash
python app.py
```

The service will automatically start consuming messages from Kafka.

## End-to-End Example

### 1. Start Infrastructure

```bash
# Start Kafka
cd ../kafka
docker compose up -d

# Start PostgreSQL (if using postgres)
cd ../pgvector
docker compose up -d

# Wait for services to be ready
sleep 10
```

### 2. Run Migrations

```bash
cd ../writer_svc

# For LanceDB (default)
python databases/lancedb/migrations/001_create_embeddings_table.py

# OR for PostgreSQL
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=embeddings_db
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
python databases/postgres/migrations/run_migrations.py
```

### 3. Start Writer Service

```bash
python app.py
```

### 4. Send Test Message

Using the Kafka CLI from the kafka directory:

```bash
cd ../kafka
python kafka_cli.py write-to-topic embeddings '{"id": "test-001", "text": "Hello world", "embedding": [0.1, 0.2, 0.3], "timestamp": "2024-01-01T00:00:00Z", "source": "test", "table_name": "embeddings"}'
```

### 5. Verify Data

**For LanceDB:**
```bash
cd ../writer_svc
python -c "
from databases.lancedb_adapter import LanceDBAdapter
adapter = LanceDBAdapter('./lancedb_data')
adapter.connect()
result = adapter.query_table('embeddings')
print('Records found:', len(result))
print('Sample record:', result.iloc[0] if len(result) > 0 else 'No records')
"
```

**For PostgreSQL:**
```bash
cd ../pgvector
python pgvector_cli.py query-table embeddings
```

## API Endpoints

- `GET /health` - Service health check
- `GET /stats` - Processing statistics
- `GET /config` - Current configuration
- `POST /start` - Manually start service
- `POST /stop` - Manually stop service

## Docker Deployment

```bash
# Build and run with Docker Compose
docker compose up -d

# View logs
docker compose logs -f writer-service
```

## Database Schemas

### LanceDB
- `id`: string (primary key)
- `text`: string
- `embedding`: float32[384]
- `timestamp`: timestamp[ns]
- `source`: string
- `metadata`: string (JSON)

### PostgreSQL
- `id`: VARCHAR(255) (primary key)
- `text`: TEXT
- `embedding`: vector(384)
- `timestamp`: TIMESTAMP WITH TIME ZONE
- `source`: VARCHAR(255)
- `metadata`: JSONB

## Troubleshooting

1. **Kafka Connection Issues**: Ensure Kafka is running and accessible
2. **Database Connection**: Check database credentials and network connectivity
3. **Permission Errors**: Ensure proper file permissions for LanceDB data directory
4. **Schema Issues**: Run migrations to create required tables

## Development

- Service auto-starts on Flask app initialization
- Background thread handles Kafka consumption
- Graceful shutdown on SIGTERM
- Comprehensive error logging
