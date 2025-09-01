# Writer Service

Service that reads embeddings from Kafka and writes them to different databases based on configuration.

## Quick Start

Configure the database type and start the service.

```bash
# Install dependencies
pip install -r requirements.txt

# Edit config.yaml to choose database (lancedb or postgres)
# Start service
python app.py
```

## Configuration

Choose database type in `config.yaml`:

```yaml
database:
  type: "lancedb"  # or "postgres"
  
  # LanceDB settings
  lancedb:
    table_name: "embeddings"
    db_path: "./lancedb_data"
  
  # PostgreSQL settings  
  postgres:
    host: "localhost"
    port: 5432
    database: "embeddings_db"
    user: "postgres"
    password: "postgres"
```

## API Endpoints

```bash
GET  /health    # Service health
GET  /stats     # Processing statistics
POST /start     # Start writer service
POST /stop      # Stop writer service
GET  /config    # Current configuration
```

## How It Works

1. **Reads** from Kafka `embeddings` topic
2. **Writes** to configured database (LanceDB or PostgreSQL)
3. **Supports** multiple database types via adapters
4. **Runs** on port 5001 by default

## Database Support

- **LanceDB**: Local file-based vector database
- **PostgreSQL**: With pgvector extension for vector operations
- **Extensible**: Easy to add new database adapters
