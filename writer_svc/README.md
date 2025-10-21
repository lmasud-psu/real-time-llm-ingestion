# Writer Service# Writer Service



A Flask-based service that reads embeddings from Kafka and writes them to PostgreSQL database.A Flask-based service that reads embeddings from Kafka and writes them to PostgreSQL database.



## Features## Features



- **Kafka Integration**: Consumes embedding data from Kafka topics- **Kafka Integration**: Consumes embedding data from Kafka topics

- **Database Support**: PostgreSQL with pgvector extension- **Database Adapters**: Supports PostgreSQL with pgvector

- **Health Monitoring**: Provides health check endpoints- **Health Monitoring**: Provides health check endpoints

- **Configurable**: YAML-based configuration- **Configurable**: YAML-based configuration

- **Resilient**: Automatic reconnection and error handling- **Resilient**: Automatic reconnection and error handling



## Architecture## Architecture



The service acts as a bridge between Kafka and PostgreSQL:The service acts as a bridge between Kafka and the database:

1. Reads embedding messages from Kafka topics1. Reads embedding messages from Kafka topics

2. Processes and validates the data2. Processes and validates the data

3. Stores embeddings in PostgreSQL database3. Stores embeddings in the configured database

- Database type (postgres)

## Quick Start- Kafka connection parameters

- Message processing settings

### Prerequisites

## Quick Start

- Python 3.10+

- Kafka cluster running### Prerequisites

- PostgreSQL with pgvector extension

- Python 3.10+

### Installation- Kafka cluster running

- PostgreSQL with pgvector extension

```bash

# Install dependencies### Installation

pip install -r requirements.txt

```bash

# Set up PostgreSQL database# Install dependencies

python databases/postgres/migrations/001_create_embeddings_table.pypip install -r requirements.txt



# Start the service# Set up database

python app.py**For PostgreSQL:**

``````bash

python databases/postgres/migrations/001_create_embeddings_table.py

## Configuration

## End-to-End Example

The service uses a YAML configuration file (`config.yaml`):

### 1. Start Infrastructure

```yaml

service:```bash

  name: "writer-service"# Start Kafka

  port: 5000cd ../kafka

docker compose up -d

kafka:

  bootstrap_servers: ["localhost:9092"]# Start PostgreSQL (if using postgres)

  topic: "embeddings"cd ../pgvector

  group_id: "writer-service-group"docker compose up -d



database:# Wait for services to be ready

  type: "postgres"sleep 10

  postgres:```

    host: "localhost"

    port: 5432### 2. Run Migrations

    database: "embeddings_db"

    user: "postgres"```bash

    password: "postgres"cd ../writer_svc

```

# For LanceDB (default)

## Usage Examplepython databases/lancedb/migrations/001_create_embeddings_table.py



```python# OR for PostgreSQL

from databases.postgres_adapter import PostgresAdapterexport POSTGRES_HOST=localhost

export POSTGRES_PORT=5432

adapter = PostgresAdapter(export POSTGRES_DB=embeddings_db

    host='localhost',export POSTGRES_USER=postgres

    port=5432,export POSTGRES_PASSWORD=postgres

    database='embeddings_db',python databases/postgres/migrations/run_migrations.py

    user='postgres',```

    password='postgres'

)### 3. Start Writer Service



# Insert embedding```bash

embedding_data = {python app.py

    'id': 'unique-id',```

    'text': 'Sample text',

    'embedding': [0.1, 0.2, 0.3, ...],### 4. Send Test Message

    'timestamp': '2024-01-01T00:00:00Z'

}Using the Kafka CLI from the kafka directory:

adapter.insert_embedding(embedding_data)

``````bash

cd ../kafka

## API Endpointspython kafka_cli.py write-to-topic embeddings '{"id": "test-001", "text": "Hello world", "embedding": [0.1, 0.2, 0.3], "timestamp": "2024-01-01T00:00:00Z", "source": "test", "table_name": "embeddings"}'

```

- `GET /health` - Health check

- `GET /stats` - Service statistics### 5. Verify Data

- `POST /write` - Manual embedding insertion

**For LanceDB:**

## Running with Docker```bash

cd ../writer_svc

```bashpython -c "

docker compose up -dfrom databases.lancedb_adapter import LanceDBAdapter

```adapter = LanceDBAdapter('./lancedb_data')

adapter.connect()

## Troubleshootingresult = adapter.query_table('embeddings')

print('Records found:', len(result))

1. **Connection Issues**: Check Kafka and PostgreSQL connection settingsprint('Sample record:', result.iloc[0] if len(result) > 0 else 'No records')

2. **Memory Usage**: Monitor memory consumption for large embedding batches"

3. **Database Errors**: Ensure PostgreSQL has pgvector extension installed```

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
