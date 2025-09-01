# Embedding Generation Service

Flask service that reads text from Kafka, generates embeddings, and writes them back to Kafka.

## Quick Start

Get the service running and test it with a simple message.

```bash
# Start services
cd ../architecture1
docker compose up -d

# Check health
curl http://localhost:5000/health

# Send test message
cd ../kafka
python kafka_cli.py write text-messages "Hello world"

# Read embeddings
python kafka_cli.py read embeddings
```

## Configuration

Configure Kafka connection and model settings in the YAML file.

`config.yaml`:
```yaml
kafka:
  bootstrap_servers: "localhost:9092"
  input_topic: "text-messages"
  output_topic: "embeddings"

model:
  name: "sentence-transformers/all-MiniLM-L6-v2"
  device: "cpu"
```

## API

REST endpoints for monitoring and controlling the service.

```bash
GET  /health    # Status
GET  /stats     # Statistics
POST /start     # Start service
POST /stop      # Stop service
```

## Message Format

Messages flow through Kafka topics with specific JSON structures.

**Input** (text-messages):
```json
{"id": "msg-1", "text": "Hello world", "timestamp": 123, "source": "kafka-cli"}
```

**Output** (embeddings):
```json
{"id": "msg-1", "original_text": "Hello world", "embedding": [0.1, 0.2, ...]}
```
