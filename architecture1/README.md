# Real-time LLM Ingestion Architecture

A centralized architecture for real-time LLM ingestion using Kafka, embedding generation, and flexible database storage.

## 🚀 Quick Start

### Option 1: Using the Startup Script (Recommended)
```bash
# Start with LanceDB (default)
./start.sh

# Start with PostgreSQL
DATABASE_TYPE=postgres ./start.sh
```

### Option 2: Using Docker Compose Directly
```bash
# Start with LanceDB
docker compose --profile lancedb up -d

# Start with PostgreSQL
DATABASE_TYPE=postgres docker compose --profile postgres up -d

# Stop all services
docker compose down
```

## 🏗️ Architecture Overview

This architecture orchestrates multiple services using a centralized `docker-compose.yml` that imports configurations from individual service directories:

- **Kafka Infrastructure**: Message broker, Zookeeper, Schema Registry, Kafka Connect, Kafka UI
- **Embedding Service**: Generates embeddings from text using Hugging Face models
- **Writer Service**: Writes embeddings to configured database (LanceDB or PostgreSQL)
- **Database Layer**: Flexible storage with LanceDB (file-based) or PostgreSQL + pgvector

## 📁 Directory Structure

```
architecture1/
├── docker-compose.yml          # Centralized orchestration
├── start.sh                    # Easy startup script
├── README.md                   # This file
└── Tiltfile                    # Legacy Tilt configuration (not used)

kafka/                          # Kafka cluster configuration
embedding_gen_svc/             # Embedding generation service
writer_svc/                     # Writer service with database adapters
pgvector/                       # PostgreSQL + pgvector setup
lancedb/                        # LanceDB configuration
```

## 🔧 Configuration

### Environment Variables
- `DATABASE_TYPE`: Choose database (`lancedb` or `postgres`)

### Service Ports
- **Kafka**: 9092
- **Kafka UI**: 8080
- **Schema Registry**: 8081
- **Kafka Connect**: 8083
- **Embedding Service**: 5000
- **Writer Service**: 5001
- **PostgreSQL**: 5432
- **pgAdmin**: 8080 (conflicts with Kafka UI - use different port)

## 🚦 Service Management

### Start Services
```bash
# All services
docker compose up -d

# Specific profile
docker compose --profile postgres up -d
docker compose --profile lancedb up -d
```

### Check Status
```bash
# Service status
docker compose ps

# Service logs
docker compose logs -f <service-name>
docker compose logs -f kafka
docker compose logs -f embedding-service
```

### Stop Services
```bash
# Stop all
docker compose down

# Stop specific services
docker compose stop kafka embedding-service
```

## 🔄 Service Dependencies

The architecture ensures proper startup order:
1. **Kafka Infrastructure** (Zookeeper, Kafka, Schema Registry)
2. **Embedding Service** (waits for Kafka)
3. **Writer Service** (waits for embedding service)
4. **Database** (waits for Kafka)

## 🧪 Testing & Operations

### Create Kafka Topics
```bash
cd ../kafka
python kafka_cli.py create-topic text-messages
python kafka_cli.py create-topic embeddings
```

### Send Test Messages
```bash
cd ../kafka
python kafka_cli.py write text-messages "Test message for embedding generation"
```

### Check Embeddings
```bash
cd ../kafka
python kafka_cli.py read embeddings --max-messages 5
```

### Database Operations
```bash
# LanceDB
cd ../lancedb
python lancedb_cli.py list-tables

# PostgreSQL
cd ../pgvector
python pgvector_cli.py list-tables
```

## 🆘 Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure ports are available (especially 8080)
2. **Network Issues**: Services use shared `kafka-network`
3. **Database Connection**: Check database credentials and connectivity

### Debug Commands
```bash
# Check network
docker network ls
docker network inspect architecture1_kafka-network

# Check volumes
docker volume ls

# Check logs
docker compose logs -f
```

## 🔄 Migration from Tilt

This architecture replaces the previous Tilt-based approach with:
- **Simpler orchestration** using Docker Compose
- **Better dependency management** with explicit `depends_on`
- **Easier debugging** with standard Docker Compose commands
- **Profile-based configuration** for different database types

## 📚 Next Steps

1. **Start the architecture**: `./start.sh`
2. **Create topics**: Use Kafka CLI to create required topics
3. **Send test messages**: Verify the full pipeline
4. **Monitor services**: Check logs and health endpoints
5. **Scale as needed**: Add more services or modify configurations
