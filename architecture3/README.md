# Architecture 3: Text Writer Service Pipeline

This architecture demonstrates a simple Kafka-to-PostgreSQL text ingestion pipeline using the Text Writer Service.

## Architecture Overview

```
Kafka Topic (text-messages) → Text Writer Service → PostgreSQL (text_messages table)
                                      ↓
                               REST API + Health Monitoring
```

## Components

- **Apache Kafka**: Message streaming platform
- **Text Writer Service**: Flask-based microservice that consumes Kafka messages and stores them in PostgreSQL
- **PostgreSQL**: Database for storing text messages
- **Kafka UI**: Web interface for monitoring Kafka topics and messages

## Quick Start

### 1. Start the Architecture

```bash
cd architecture3
./start.sh
```

This will:
- Create the necessary Docker network
- Start Kafka, PostgreSQL, and the Text Writer Service
- Run health checks to ensure all services are ready

### 2. Verify Services

Check that all services are running:

```bash
docker compose ps
```

### 3. Test the Pipeline

Run the end-to-end test:

```bash
./e2e_test.sh
```

## Service URLs

After starting, the following services will be available:

- **Text Writer Service API**: http://localhost:5002
- **Text Writer Service Health**: http://localhost:5002/health
- **Kafka UI**: http://localhost:8080
- **PostgreSQL**: localhost:5434 (user: postgres, db: text_messages_db)

## Usage Examples

### Using the CLI Tool

```bash
# Check service health
cd ../text_writer_svc
python cli.py --url http://localhost:5002 health

# List messages
python cli.py --url http://localhost:5002 list

# Create a message
python cli.py --url http://localhost:5002 create "Hello from Architecture 3!"

# Get service statistics
python cli.py --url http://localhost:5002 stats
```

### Sending Messages via Kafka

```bash
# Send a message to the Kafka topic
cd ../kafka
python kafka_cli.py produce text-messages '{"id":"test-123","text":"Hello from Kafka"}'

# List messages in the topic
python kafka_cli.py consume text-messages --max-messages 10
```

### Direct Database Access

```bash
# Connect to PostgreSQL
PGPASSWORD=postgres psql -h localhost -p 5434 -U postgres -d text_messages_db

# Query messages
SELECT * FROM text_messages ORDER BY processed_at DESC LIMIT 10;
```

### REST API Examples

```bash
# Get service health
curl http://localhost:5002/health

# List recent messages
curl "http://localhost:5002/messages?limit=10"

# Get a specific message
curl "http://localhost:5002/messages/your-message-id"

# Create a message via API
curl -X POST http://localhost:5002/messages \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello via API"}'

# Get service statistics
curl http://localhost:5002/stats
```

## Data Flow

1. **Message Production**: Messages are sent to the Kafka topic `text-messages` in JSON format:
   ```json
   {
     "id": "unique-uuid",
     "text": "Message content"
   }
   ```

2. **Message Consumption**: The Text Writer Service consumes messages from Kafka and stores them in PostgreSQL

3. **Database Storage**: Messages are stored in the `text_messages` table with the following schema:
   ```sql
   CREATE TABLE text_messages (
       id UUID PRIMARY KEY,
       message TEXT NOT NULL,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );
   ```

4. **API Access**: The REST API provides endpoints to query and manage stored messages

## Configuration

### Port Mappings

- **Text Writer Service**: 5002 → 5001 (internal)
- **PostgreSQL**: 5434 → 5432 (internal)
- **Kafka UI**: 8080 → 8080
- **Zookeeper**: 42181 → 2181 (internal)

### Environment Variables

The Text Writer Service can be configured using these environment variables:

- `DATABASE_HOST`: PostgreSQL hostname (default: postgres)
- `DATABASE_PORT`: PostgreSQL port (default: 5432)
- `DATABASE_NAME`: Database name (default: text_messages_db)
- `DATABASE_USER`: Database user (default: postgres)
- `DATABASE_PASSWORD`: Database password (default: postgres)

## Monitoring and Troubleshooting

### Check Service Health

```bash
# Text Writer Service
curl http://localhost:5002/health

# PostgreSQL
PGPASSWORD=postgres pg_isready -h localhost -p 5434 -U postgres

# Kafka (via Kafka UI)
open http://localhost:8080
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f text-writer-service
docker compose logs -f postgres
docker compose logs -f kafka
```

### Common Issues

1. **Port Conflicts**: If ports are already in use, modify the port mappings in `docker-compose.yml`

2. **Service Not Starting**: Check logs and ensure all dependencies are healthy:
   ```bash
   docker compose logs text-writer-service
   ```

3. **Database Connection Issues**: Verify PostgreSQL is running and accessible:
   ```bash
   docker compose exec postgres pg_isready -U postgres
   ```

4. **Kafka Issues**: Check Kafka UI or use the Kafka CLI tools:
   ```bash
   docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
   ```

## Stopping the Architecture

```bash
# Stop all services
docker compose down

# Stop and remove volumes (data will be lost)
docker compose down -v
```

## Integration with Other Architectures

This architecture can be combined with other architectures in the project:

- Use the same Kafka cluster for multiple consumers
- Connect to shared PostgreSQL instances
- Integrate with the embedding generation and vector storage pipelines

## Performance Considerations

- **Kafka**: Configured for single-node deployment, suitable for development and testing
- **PostgreSQL**: Uses default configuration, consider tuning for production workloads
- **Text Writer Service**: Single instance, can be scaled horizontally if needed

## Development

To modify the Text Writer Service:

1. Edit files in `../text_writer_svc/`
2. Rebuild and restart: `docker compose up -d --build text-writer-service`
3. Test changes with the CLI or API calls

For database schema changes:

1. Add migration files to `../text_writer_svc/migrations/`
2. Restart PostgreSQL to apply migrations
3. Verify with: `./e2e_test.sh`