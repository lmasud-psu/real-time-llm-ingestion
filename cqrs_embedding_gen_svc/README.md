# CQRS Embedding Generation Service

This service implements a CQRS (Command Query Responsibility Segregation) pattern to monitor PostgreSQL for new text entries and generate embeddings using SentenceTransformer models.

## Architecture

The service uses a polling-based approach to:
1. **Monitor** the `text_messages` table for new entries
2. **Generate** embeddings using a SentenceTransformer model 
3. **Store** embeddings in a separate `text_embeddings` table with pgvector
4. **Provide** similarity search capabilities

## Features

- 🔄 **Real-time Processing**: Polls PostgreSQL for new text messages
- 🧠 **Embedding Generation**: Uses SentenceTransformer models (default: all-MiniLM-L6-v2)
- 🔍 **Vector Search**: Provides similarity search via REST API
- 📊 **CQRS Pattern**: Separates read/write operations for optimal performance
- 🐳 **Docker Ready**: Containerized with health checks
- 🛠️ **CLI Tools**: Command-line interface for management
- 📈 **Monitoring**: Status endpoints and logging

## Quick Start

### Using Docker Compose

```bash
# Start the service
docker-compose up -d

# Check service health
curl http://localhost:5003/health

# Check processor status
curl http://localhost:5003/status

# Start the embedding processor
curl -X POST http://localhost:5003/start
```

### Using CLI Tool

```bash
# Install dependencies
pip install -r requirements.txt

# Check service health
python cli.py health

# Start the processor
python cli.py start

# Monitor status
python cli.py monitor

# Search for similar texts
python cli.py search "machine learning algorithms"
```

## API Endpoints

### Health & Status
- `GET /health` - Service health check
- `GET /status` - Processor status and statistics

### Processor Control
- `POST /start` - Start the embedding processor
- `POST /stop` - Stop the embedding processor  
- `POST /process-batch` - Manually trigger batch processing

### Search
- `POST /embeddings/search` - Search for similar embeddings
  ```json
  {
    "query": "machine learning algorithms",
    "limit": 10
  }
  ```

## Configuration

Edit `config.yaml` to customize:

```yaml
database:
  host: postgres
  port: 5432
  database: realtime_llm
  user: postgres
  password: password

embedding:
  model_name: "all-MiniLM-L6-v2"
  dimension: 384

polling:
  interval_seconds: 5
  batch_size: 10
  error_retry_seconds: 30

auto_start: true
```

## Database Schema

### Source Table (text_messages)
```sql
CREATE TABLE text_messages (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    source VARCHAR(255) DEFAULT 'unknown',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Target Table (text_embeddings)
```sql
CREATE TABLE text_embeddings (
    id SERIAL PRIMARY KEY,
    text_message_id INTEGER REFERENCES text_messages(id),
    text_content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(text_message_id)
);
```

## How It Works

1. **Polling Loop**: The service continuously polls the `text_messages` table for new entries
2. **Embedding Generation**: For each new message, it generates an embedding using SentenceTransformer
3. **Storage**: Embeddings are stored in `text_embeddings` with a foreign key reference
4. **Vector Index**: pgvector provides efficient similarity search with IVFFLAT indexing
5. **CQRS Separation**: Read queries (search) and write operations (embedding generation) are optimized separately

## Performance Considerations

- **Batch Processing**: Processes multiple messages in batches for efficiency
- **Connection Pooling**: Reuses database connections to minimize overhead
- **Vector Indexing**: Uses IVFFLAT index for fast similarity search
- **Lightweight Model**: Default model (all-MiniLM-L6-v2) balances quality and speed
- **Configurable Polling**: Adjustable intervals to balance latency vs resource usage

## Integration with Architecture3

To integrate with the existing architecture3 setup:

1. **Add to docker-compose.yml**:
```yaml
services:
  cqrs-embedding-gen:
    build: ../cqrs_embedding_gen_svc
    container_name: cqrs-embedding-gen
    ports:
      - "5003:5003"
    depends_on:
      - postgres
    networks:
      - realtime-llm-network
```

2. **Update PostgreSQL config** to ensure pgvector extension is available

3. **Configure database connection** to point to the shared PostgreSQL instance

## Testing

Run the test suite:

```bash
# Run all tests
python test_service.py

# Test specific functionality
python cli.py process  # Manual batch processing
python cli.py search "test query"  # Search test
```

## Monitoring

Monitor the service using:

```bash
# CLI monitoring
python cli.py monitor

# Check logs
docker-compose logs -f cqrs-embedding-gen

# Health check
curl http://localhost:5003/health
```

## Troubleshooting

### Common Issues

1. **Model Loading Errors**: Ensure sufficient memory for SentenceTransformer model
2. **Database Connection**: Verify PostgreSQL is running and pgvector extension is installed
3. **Permission Issues**: Check database user permissions for table creation
4. **Memory Usage**: Monitor memory consumption during embedding generation

### Debug Mode

Set debug logging in config.yaml:
```yaml
logging:
  level: DEBUG
```

## Architecture Benefits

- **Scalability**: Can scale embedding generation independently of text ingestion
- **Fault Tolerance**: Polling approach ensures no message loss
- **Flexibility**: Easy to change embedding models without affecting other services
- **Performance**: Optimized for both writes (batch processing) and reads (vector search)
- **Monitoring**: Built-in status tracking and health checks