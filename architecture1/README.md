# Real-Time LLM Ingestion Architecture

This directory contains the centralized orchestration for the real-time LLM ingestion system using Docker Compose.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Text Input    │───▶│  Kafka Cluster   │───▶│  Embedding      │
│   (Kafka CLI)   │    │                  │    │  Generation     │
└─────────────────┘    └──────────────────┘    │  Service        │
                                               └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Embeddings     │
                                               │  Output Topic   │
                                               └─────────────────┘
```

## Services

### Core Services

1. **Embedding Generation Service** (`embedding-service`)
   - **Port**: 5000
   - **Purpose**: Reads text messages, generates embeddings using Hugging Face models
   - **Health Check**: `http://localhost:5000/health`

2. **Kafka Cluster** (`kafka`)
   - **Port**: 9092 (external), 29092 (internal)
   - **Purpose**: Message streaming and event processing
   - **JMX Port**: 9101

3. **Zookeeper** (`zookeeper`)
   - **Port**: 2181
   - **Purpose**: Kafka coordination and metadata management

### Management & Monitoring

4. **Kafka UI** (`kafka-ui`)
   - **Port**: 8080
   - **Purpose**: Web-based Kafka cluster management
   - **URL**: `http://localhost:8080`

5. **Schema Registry** (`schema-registry`)
   - **Port**: 8081
   - **Purpose**: Avro schema management (for future use)

6. **Kafka Connect** (`kafka-connect`)
   - **Port**: 8083
   - **Purpose**: Data integration platform (for future use)

## Quick Start

### 1. Start All Services

```bash
cd architecture1
docker compose up -d
```

### 2. Verify Services

```bash
# Check all services are running
docker compose ps

# Check embedding service health
curl http://localhost:5000/health

# Access Kafka UI
open http://localhost:8080
```

### 3. Test the System

```bash
# Send test messages (from kafka directory)
cd ../kafka
python kafka_cli.py write text-messages "Hello, this is a test message!"
python kafka_cli.py write text-messages "Machine learning is fascinating!"

# Check generated embeddings
python kafka_cli.py read embeddings --max-messages 5
```

## Service Management

### Start/Stop Services

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes all data)
docker compose down -v

# View logs
docker compose logs -f embedding-service
docker compose logs -f kafka
```

### Individual Service Control

```bash
# Start only specific services
docker compose up -d kafka zookeeper

# Restart a service
docker compose restart embedding-service

# Scale a service (if supported)
docker compose up -d --scale embedding-service=2
```

## Configuration

### Environment Variables

Services can be configured through environment variables in the docker compose.yml file:

- **KAFKA_AUTO_CREATE_TOPICS_ENABLE**: Auto-create topics (default: true)
- **KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR**: Replication factor (default: 1)
- **PYTHONUNBUFFERED**: Python output buffering (default: 1)

### Service Configuration

- **Embedding Service**: Configured via `../embedding_gen_svc/config.yaml`
- **Kafka**: Configured via environment variables in docker compose.yml
- **Kafka UI**: Configured via environment variables

## Monitoring & Debugging

### Health Checks

```bash
# Embedding service health
curl http://localhost:5000/health

# Service statistics
curl http://localhost:5000/stats

# Service configuration
curl http://localhost:5000/config
```

### Logs

```bash
# View all logs
docker compose logs

# Follow specific service logs
docker compose logs -f embedding-service
docker compose logs -f kafka

# View last 100 lines
docker compose logs --tail=100 embedding-service
```

### Kafka Management

```bash
# List topics
docker exec real-time-kafka kafka-topics --list --bootstrap-server localhost:9092

# Create topic manually
docker exec real-time-kafka kafka-topics --create --topic my-topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# Describe topic
docker exec real-time-kafka kafka-topics --describe --topic text-messages --bootstrap-server localhost:9092
```

## Data Flow

### Input Topics
- **text-messages**: Raw text input for embedding generation

### Output Topics
- **embeddings**: Generated embeddings with metadata

### Message Formats

**Input Message (text-messages topic):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "This is the text to embed",
  "timestamp": 1699123456.789,
  "source": "kafka-cli"
}
```

**Output Message (embeddings topic):**
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

## Development

### Adding New Services

1. Create service directory in the project root
2. Add service definition to `docker compose.yml`
3. Configure networking and dependencies
4. Update this README

### Service Dependencies

```
zookeeper → kafka → schema-registry → kafka-connect
     ↓
   kafka-ui
     ↓
embedding-service
```

### Network Configuration

All services run on the `real-time-network` bridge network, allowing:
- Internal service communication
- External access via exposed ports
- Service discovery by hostname

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   - Ensure ports 5000, 8080, 8081, 8083, 9092, 2181 are available
   - Check for other Docker containers using these ports

2. **Service Startup Failures**
   - Check logs: `docker compose logs [service-name]`
   - Verify dependencies are running
   - Check resource availability (memory, disk space)

3. **Kafka Connection Issues**
   - Verify Kafka is running: `docker compose ps kafka`
   - Check Kafka logs: `docker compose logs kafka`
   - Verify network connectivity

4. **Embedding Service Issues**
   - Check model download: `docker compose logs embedding-service`
   - Verify configuration: `curl http://localhost:5000/config`
   - Check Kafka connectivity from service

### Performance Tuning

1. **Memory Allocation**
   - Increase Docker memory limits
   - Adjust JVM heap size for Kafka
   - Monitor memory usage: `docker stats`

2. **Storage Optimization**
   - Use SSD storage for Kafka data
   - Configure appropriate retention policies
   - Monitor disk usage: `docker system df`

3. **Network Optimization**
   - Use host networking for high-throughput scenarios
   - Configure appropriate batch sizes
   - Monitor network usage: `docker stats`

## Production Considerations

### Security
- Use secrets management for sensitive configuration
- Enable TLS/SSL for Kafka communication
- Implement authentication and authorization
- Regular security updates

### Scaling
- Use multiple Kafka brokers for high availability
- Implement horizontal scaling for embedding service
- Use load balancers for external access
- Monitor resource usage and scale accordingly

### Monitoring
- Implement comprehensive logging
- Use monitoring tools (Prometheus, Grafana)
- Set up alerting for service failures
- Monitor message throughput and latency

### Backup & Recovery
- Regular backup of Kafka data
- Configuration backup and version control
- Disaster recovery procedures
- Data retention policies
