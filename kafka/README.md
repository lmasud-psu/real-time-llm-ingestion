# Kafka Cluster Docker Compose

This docker compose file sets up a complete Kafka cluster with all the essential components for real-time data streaming.

## Services Included

- **Zookeeper**: Coordination service for Kafka
- **Kafka Broker**: Main message broker
- **Kafka UI**: Web-based management interface
- **Schema Registry**: Manages Avro schemas (optional)
- **Kafka Connect**: Data integration platform (optional)

## Quick Start

1. **Ensure Docker is running and you have permissions:**
   ```bash
   # If you get permission denied errors, add your user to the docker group:
   sudo usermod -aG docker $USER
   # Then log out and back in, or run:
   newgrp docker
   ```

2. **Start the cluster:**
   ```bash
   docker compose up -d
   ```

3. **Check if all services are running:**
   ```bash
   docker compose ps
   ```

4. **View logs:**
   ```bash
   docker compose logs -f kafka
   ```

## Access Points

- **Kafka Broker**: `localhost:9092`
- **Kafka UI**: http://localhost:8080
- **Schema Registry**: http://localhost:8081
- **Kafka Connect**: http://localhost:8083
- **Zookeeper**: `localhost:2181`

## Basic Usage

### Create a Topic
```bash
docker exec kafka kafka-topics --create --topic test-topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

### List Topics
```bash
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Produce Messages
```bash
docker exec -it kafka kafka-console-producer --topic test-topic --bootstrap-server localhost:9092
```

### Consume Messages
```bash
docker exec -it kafka kafka-console-consumer --topic test-topic --bootstrap-server localhost:9092 --from-beginning
```

## Management

- **Stop the cluster:**
  ```bash
  docker compose down
  ```

- **Stop and remove volumes (WARNING: This will delete all data):**
  ```bash
  docker compose down -v
  ```

- **Restart a specific service:**
  ```bash
  docker compose restart kafka
  ```

## Configuration Notes

- Kafka is configured to auto-create topics
- Data is persisted in Docker volumes
- JMX metrics are enabled on port 9101
- The cluster uses a single broker (suitable for development)

## Python CLI Tool

A comprehensive Python CLI tool is included for easy Kafka management:

### Installation
```bash
pip install -r requirements.txt
```

### Quick CLI Examples
```bash
# Create a topic
python kafka_cli.py create-topic my-topic --partitions 3

# Write a message
python kafka_cli.py write my-topic "Hello, Kafka!"

# Read messages
python kafka_cli.py read my-topic --max-messages 10

# List all topics
python kafka_cli.py list-topics

# Delete a topic
python kafka_cli.py delete-topic my-topic

# Get help for any command
python kafka_cli.py --help
python kafka_cli.py create-topic --help
```

For detailed CLI usage, see [CLI_USAGE.md](CLI_USAGE.md).

## For Production Use

For production environments, consider:
- Increasing replication factors
- Using multiple Kafka brokers
- Setting up proper security (SASL/SSL)
- Configuring proper retention policies
- Setting up monitoring and alerting
