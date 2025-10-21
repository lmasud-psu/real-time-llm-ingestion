# Real-time LLM Ingestion Architecture

A centralized architecture for real-time LLM ingestion using Kafka, embedding generation, and vector database storage.

## Architecture Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Kafka     │───▶│  Embedding   │───▶│   Writer    │
│  Cluster    │    │   Service    │    │  Service    │
└─────────────┘    └──────────────┘    └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────┐    ┌─────────────┐
                    │  Embeddings  │    │  Vector     │
                    │   Messages   │    │  Database   │
                    └──────────────┘    └─────────────┘
```

## Services

### Core Infrastructure
- **Kafka Cluster**: Zookeeper, Kafka, Schema Registry, Kafka Connect, Kafka UI
- **Embedding Service**: Generates embeddings from text messages (Port 5000)
- **Writer Service**: Consumes embeddings and writes to PostgreSQL database (Port 5001)

### Database
- **PostgreSQL + pgvector**: Relational database with vector extension

## Quick Start

### 1. Setup Directories
```bash
cd architecture1
./setup_directories.sh
```

### 2. Start Architecture

```bash
tilt up
```

### 3. Verify Services
```bash
# Check all services are running
tilt get uiresources

# Test writer service health
tilt trigger validate-writer-service

# Run end-to-end validation
tilt trigger end-to-end-validation
```

## Service Details

### Writer Service
- **Port**: 5001 (external), 5000 (internal)
- **Auto-start**: Automatically begins consuming from Kafka on startup
- **Database Support**: PostgreSQL with pgvector
- **Message Format**: Expects JSON with `id`, `text`, `embedding`, `timestamp`, `source`, and `table_name`

### Database Configuration
The writer service uses PostgreSQL with pgvector extension.

## Available Commands

### Health Checks
- `tilt trigger health-check` - Check embedding service health (port 5000)
- `tilt trigger db-health-check` - Check database health
- `tilt trigger validate-writer-service` - Validate writer service (port 5001)

### Database Operations
- `tilt trigger validate-postgres-writes` - Test PostgreSQL writes

### Kafka Operations
- `tilt trigger create-topics` - Create required Kafka topics
- `tilt trigger send-test-message` - Send test message to text-messages topic
- `tilt trigger read-embeddings` - Read from embeddings topic

## Configuration

### Volumes
- `postgres_data`: PostgreSQL data storage
- `writer-logs`: Writer service logs

## Development

### Adding New Services
1. Create service directory with `docker-compose.yml`
2. Add service to appropriate database-specific compose file
3. Update Tiltfile with new resources if needed

### Testing
- Use `test_architecture.py` for comprehensive testing
- Individual service tests available in respective directories
- End-to-end validation through Tilt resources

## Troubleshooting

### Common Issues
1. **Port Conflicts**: 
   - Embedding Service: Port 5000
   - Writer Service: Port 5001
   - Kafka: Port 9092
   - Zookeeper: Port 2181
2. **Permission Errors**: Run `./setup_directories.sh` to fix directory permissions
3. **Network Issues**: Check that `kafka-network` is created and accessible

### Logs
```bash
# View all logs
tilt logs

# View specific service logs
docker compose logs -f writer-service
docker compose logs -f kafka
```

### Reset
```bash
# Stop all services
tilt down

# Clean start
tilt up
```

## File Structure

```
architecture1/
├── docker-compose.yml              # Base services (Kafka, Embedding)
├── docker-compose.postgres.yml     # PostgreSQL + Writer Service
├── Tiltfile                        # Tilt orchestration
├── setup_directories.sh            # Directory setup script
├── test_architecture.py            # Architecture test script
└── README.md                       # This file
```
