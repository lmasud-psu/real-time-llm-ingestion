# Embedding Generation Service

A Flask-based microservice that reads text messages from Kafka, generates embeddings using Hugging Face models, and writes the embeddings back to Kafka topics.

## Features

- **Real-time Processing**: Continuously reads messages from a configured Kafka topic
- **Hugging Face Integration**: Uses sentence-transformers models for embedding generation
- **Kafka Integration**: Reads from input topic and writes to output topic
- **REST API**: Provides health checks, statistics, and service control endpoints
- **Configurable**: All settings managed through YAML configuration file
- **Docker Support**: Fully containerized with Docker and docker compose
- **Monitoring**: Built-in logging and statistics tracking

## Architecture

```
Kafka Input Topic → Embedding Service → Kafka Output Topic
     (text)              (Flask)            (embeddings)
```

## Quick Start

### Using Centralized Architecture (Recommended)

**Note:** This service is now orchestrated through the centralized `architecture1` directory. The service uses the shared Kafka cluster on port 9092.

1. **Start all services from the architecture directory:**
   ```bash
   cd ../architecture1
   docker compose up -d
   ```

2. **Check service health:**
   ```bash
   curl http://localhost:5000/health
   ```

3. **Send test messages using the Kafka CLI:**
   ```bash
   # From the kafka directory
   python kafka_cli.py write text-messages "Hello, this is a test message!"
   python kafka_cli.py write text-messages "Another message for embedding generation"
   ```

4. **Check generated embeddings:**
   ```bash
   python kafka_cli.py read embeddings --max-messages 10
   ```

### Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Kafka is running:**
   ```bash
   # From the architecture1 directory
   cd ../architecture1
   docker compose up -d
   ```

3. **Create required topics:**
   ```bash
   python kafka_cli.py create-topic text-messages
   python kafka_cli.py create-topic embeddings
   ```

4. **Run the service:**
   ```bash
   python app.py
   ```

## Configuration

The service is configured via `config.yaml`:

```yaml
# Kafka Configuration
kafka:
  bootstrap_servers: "localhost:9092"
  input_topic: "text-messages"
  output_topic: "embeddings"
  consumer_group: "embedding-service"

# Hugging Face Model Configuration
model:
  name: "sentence-transformers/all-MiniLM-L6-v2"
  max_length: 512
  device: "cpu"  # Use "cuda" for GPU

# Flask Configuration
flask:
  host: "0.0.0.0"
  port: 5000
  debug: false
```

### Model Options

You can use any sentence-transformers model from Hugging Face:

- `sentence-transformers/all-MiniLM-L6-v2` (default, fast, 384 dimensions)
- `sentence-transformers/all-mpnet-base-v2` (slower, better quality, 768 dimensions)
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (multilingual)

## API Endpoints

### Health Check
```bash
GET /health
```
Returns service status and basic statistics.

### Statistics
```bash
GET /stats
```
Returns detailed service statistics including:
- Messages processed
- Embeddings generated
- Error count
- Last processed timestamp

### Service Control
```bash
POST /start  # Start the service
POST /stop   # Stop the service
```

### Configuration
```bash
GET /config
```
Returns current configuration.

## Message Format

### Input Messages (text-messages topic)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "This is the text to embed",
  "timestamp": 1699123456.789,
  "source": "kafka-cli"
}
```

**Note:** The Kafka CLI automatically generates unique IDs and timestamps for all messages.

### Output Messages (embeddings topic)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "original_text": "This is the text to embed",
  "embedding": [0.1, 0.2, 0.3, ...],
  "model_name": "sentence-transformers/all-MiniLM-L6-v2",
  "timestamp": 1699123456.789,
  "embedding_dimension": 384,
  "processing_timestamp": 1699123457.123,
  "input_timestamp": 1699123456.789,
  "input_source": "kafka-cli"
}
```

## Usage Examples

### Using the Kafka CLI

1. **Send text messages:**
   ```bash
   python kafka_cli.py write text-messages "Machine learning is fascinating!"
   python kafka_cli.py write text-messages "Natural language processing with transformers"
   ```

2. **Read generated embeddings:**
   ```bash
   python kafka_cli.py read embeddings --max-messages 5
   ```

### Using curl

1. **Check service status:**
   ```bash
   curl http://localhost:5000/health
   ```

2. **Get statistics:**
   ```bash
   curl http://localhost:5000/stats
   ```

### Using Python

```python
from kafka import KafkaProducer
import json

# Send messages
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

message = {
    "id": "test-1",
    "text": "This is a test message for embedding generation"
}

producer.send('text-messages', value=message)
producer.flush()
```

## Monitoring and Logs

### Logs
- Application logs: `embedding_service.log`
- Docker logs: `docker compose logs -f embedding-service`

### Metrics
- Messages processed per minute
- Embedding generation latency
- Error rates
- Memory and CPU usage (via Docker stats)

## Development

### Running Tests
```bash
pytest tests/
```

### Code Structure
```
embedding_gen_svc/
├── app.py              # Main Flask application
├── config.yaml         # Configuration file
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container definition
├── docker compose.yml # Service orchestration
└── README.md          # This file
```

### Adding New Models
1. Update the model name in `config.yaml`
2. The service will automatically download and cache the model
3. Restart the service to load the new model

## Troubleshooting

### Common Issues

1. **Model download fails:**
   - Check internet connection
   - Verify model name is correct
   - Check available disk space

2. **Kafka connection issues:**
   - Ensure Kafka is running: `docker compose ps`
   - Check bootstrap servers in config
   - Verify topic names exist

3. **High memory usage:**
   - Use smaller models (all-MiniLM-L6-v2)
   - Reduce batch size
   - Use CPU instead of GPU

4. **Slow processing:**
   - Use GPU if available (set device: "cuda")
   - Use faster models
   - Increase consumer timeout

### Debug Mode
Enable debug logging in `config.yaml`:
```yaml
logging:
  level: "DEBUG"
```

## Performance Tuning

### For High Throughput
- Use GPU acceleration (`device: "cuda"`)
- Increase Kafka consumer batch size
- Use faster models (all-MiniLM-L6-v2)
- Run multiple service instances

### For Better Quality
- Use larger models (all-mpnet-base-v2)
- Increase max_length for longer texts
- Use specialized domain models

## Security Considerations

- Run as non-root user (Dockerfile includes this)
- Use environment variables for sensitive config
- Enable TLS for Kafka in production
- Implement authentication for REST endpoints
- Regular security updates for dependencies

## Production Deployment

1. **Use production-ready configuration:**
   ```yaml
   flask:
     debug: false
   logging:
     level: "INFO"
   ```

2. **Set up monitoring:**
   - Prometheus metrics
   - Grafana dashboards
   - Alert manager

3. **Use orchestration:**
   - Kubernetes deployment
   - Docker Swarm
   - AWS ECS/Fargate

4. **Implement scaling:**
   - Horizontal pod autoscaling
   - Load balancing
   - Multiple service instances
