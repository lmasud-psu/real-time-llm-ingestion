# Kafka Cluster

A complete Kafka cluster with Zookeeper, Schema Registry, Kafka Connect, and Kafka UI.

## Quick Start

```bash
# Fix Docker permissions (if needed)
sudo usermod -aG docker $USER && newgrp docker

# Start cluster
docker compose up -d

# Check status
docker compose ps
```

## Services

- **Kafka**: `localhost:9092`
- **Kafka UI**: http://localhost:8080
- **Schema Registry**: http://localhost:8081
- **Kafka Connect**: http://localhost:8083
- **Zookeeper**: `localhost:2181`

## Python CLI Tool

### Installation
```bash
pip install -r requirements.txt
```

### Basic Commands

```bash
# Create topic
python kafka_cli.py create-topic my-topic --partitions 3

# List topics
python kafka_cli.py list-topics

# Write message
python kafka_cli.py write my-topic "Hello, Kafka!"

# Read messages
python kafka_cli.py read my-topic --max-messages 10

# Delete topic
python kafka_cli.py delete-topic my-topic

# Delete all topics
python kafka_cli.py delete-all-topics
```

### Message Format

Messages are automatically structured with:
```json
{
  "id": "unique-message-id",
  "text": "your message",
  "timestamp": 1234567890.123,
  "source": "kafka-cli"
}
```

### Examples

```bash
# Complete workflow
python kafka_cli.py create-topic user-events
python kafka_cli.py write user-events '{"user_id": 123, "event": "login"}'
python kafka_cli.py read user-events
python kafka_cli.py delete-topic user-events
```

## Management

```bash
# Stop cluster
docker compose down

# Stop and remove data
docker compose down -v

# View logs
docker compose logs -f kafka
```

## Troubleshooting

- **Permission denied**: Run `sudo usermod -aG docker $USER && newgrp docker`
- **Connection refused**: Ensure Kafka is running with `docker compose ps`
- **Import errors**: Install requirements with `pip install -r requirements.txt`
