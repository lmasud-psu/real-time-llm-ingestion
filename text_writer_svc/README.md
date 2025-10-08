# Text Writer Service

A Flask-based microservice that reads messages from a Kafka topic and stores them in a PostgreSQL database. This service is designed to be part of a real-time data ingestion pipeline.

## Features

- **Kafka Consumer**: Reads messages from configurable Kafka topics
- **PostgreSQL Storage**: Stores messages with UUIDs in a PostgreSQL database
- **REST API**: Provides HTTP endpoints for message management and statistics
- **CLI Tool**: Command-line interface for interacting with the service
- **Health Monitoring**: Built-in health checks and monitoring endpoints
- **Docker Support**: Fully containerized with docker-compose for easy deployment

## Architecture

```
Kafka Topic (text-messages) → Text Writer Service → PostgreSQL (text_messages table)
                                      ↓
                               REST API + CLI Tool
```

## Quick Start

### Using Docker Compose (Recommended)

1. **Start all services**:
```bash
cd text_writer_svc
docker compose up -d
```

2. **Check service health**:
```bash
curl http://localhost:5001/health
```

3. **Send a test message**:
```bash
python cli.py create "Hello, World!"
```

4. **List messages**:
```bash
python cli.py list
```

### Manual Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Start PostgreSQL and Kafka** (using existing services or docker-compose)

3. **Run database migrations**:
```bash
python migrations/run_migrations.py
```

4. **Start the service**:
```bash
python app.py
```

## Configuration

The service is configured via `config.yaml`. Key settings include:

```yaml
# Kafka Configuration
kafka:
  bootstrap_servers: "kafka:29092"
  input_topic: "text-messages"
  consumer_group: "text-writer-service"

# PostgreSQL Configuration
database:
  host: "postgres"
  port: 5432
  name: "text_messages_db"
  user: "postgres"
  password: "postgres"

# Flask Configuration
flask:
  host: "0.0.0.0"
  port: 5001
```

### Environment Variables

You can override configuration using environment variables:

- `DATABASE_HOST` (default: postgres)
- `DATABASE_PORT` (default: 5432)
- `DATABASE_NAME` (default: text_messages_db)
- `DATABASE_USER` (default: postgres)
- `DATABASE_PASSWORD` (default: postgres)

## API Endpoints

### Health Check
```bash
GET /health
```
Returns service health status and basic information.

### List Messages
```bash
GET /messages?limit=10&offset=0
```
Returns paginated list of messages.

### Get Message
```bash
GET /messages/{message_id}
```
Returns a specific message by UUID.

### Create Message
```bash
POST /messages
Content-Type: application/json

{
  "id": "uuid-here",  # optional
  "message": "Your message content"
}
```
Creates a new message. If no ID is provided, a UUID will be generated.

### Service Statistics
```bash
GET /stats
```
Returns service statistics including message counts and timestamps.

## CLI Usage

The CLI tool (`cli.py`) provides a convenient interface:

### Basic Commands

```bash
# Check service health
python cli.py health

# List recent messages
python cli.py list --limit 20

# Get a specific message
python cli.py get <message-id>

# Create a new message
python cli.py create "Your message here"

# Create with custom ID
python cli.py create "Your message" --id "custom-uuid"

# Get service statistics
python cli.py stats

# Send messages from a file (one per line)
python cli.py send-file messages.txt
```

### CLI Options

```bash
# Use different service URL
python cli.py --url http://remote-host:5001 health

# Different output formats
python cli.py list --format json
python cli.py stats --format pretty
```

## Database Schema

The service creates a `text_messages` table with the following structure:

```sql
CREATE TABLE text_messages (
    id UUID PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Kafka Message Format

The service expects Kafka messages in JSON format:

```json
{
  "id": "uuid-string",
  "text": "Message content"
}
```

- `id`: UUID string identifying the message
- `text`: The actual message content to store

## Testing

### Unit Tests

Run the test suite:

```bash
# Start services first
docker-compose up -d

# Run tests
python test_service.py
```

### Manual Testing

1. **Send a message via Kafka**:
```bash
# Using kafka CLI (if available)
echo '{"id":"test-123","text":"Hello Kafka"}' | kafka-console-producer --topic text-messages --bootstrap-server localhost:9092

# Using the CLI
python cli.py create "Test message"
```

2. **Verify in database**:
```bash
python cli.py list
```

3. **Check service logs**:
```bash
docker-compose logs -f text-writer-service
```

## Development

### Project Structure

```
text_writer_svc/
├── app.py                 # Main Flask application
├── cli.py                 # Command-line interface
├── config.yaml           # Service configuration
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Multi-service setup
├── test_service.py       # Unit tests
├── migrations/           # Database migrations
│   ├── 001_create_text_messages_table.sql
│   └── run_migrations.py
└── README.md            # This file
```

### Adding New Features

1. **New API endpoints**: Add routes in the `_setup_routes()` method in `app.py`
2. **CLI commands**: Add new commands in `cli.py` using the `@cli.command()` decorator
3. **Database changes**: Create new migration files in the `migrations/` directory

### Environment Setup

For development, you can run individual components:

```bash
# Start only PostgreSQL and Kafka
docker-compose up -d postgres kafka zookeeper

# Run the service locally
python app.py

# Use the CLI with local service
python cli.py --url http://localhost:5001 health
```

## Monitoring and Logging

### Health Checks

The service includes comprehensive health checks:

- **HTTP health endpoint**: `GET /health`
- **Docker health check**: Built into the Dockerfile
- **Database connectivity**: Verified in health checks
- **Kafka consumer status**: Reported in health and stats endpoints

### Logging

Logs are written to stdout/stderr and include:

- Kafka message processing
- Database operations
- HTTP requests
- Error conditions

### Metrics

The `/stats` endpoint provides operational metrics:

- Total message count
- Recent message count (last hour)
- Oldest/newest message timestamps
- Kafka consumer status

## Troubleshooting

### Common Issues

1. **Service won't start**:
   - Check if PostgreSQL is running and accessible
   - Verify Kafka connectivity
   - Check logs: `docker-compose logs text-writer-service`

2. **Messages not being processed**:
   - Verify Kafka topic exists and has messages
   - Check consumer group status
   - Review service logs for errors

3. **Database connection errors**:
   - Ensure PostgreSQL is running
   - Verify credentials in config.yaml or environment variables
   - Check network connectivity between containers

4. **CLI not working**:
   - Ensure service is running and accessible
   - Check the service URL parameter
   - Verify network connectivity

### Debug Mode

Enable debug mode by setting `flask.debug: true` in `config.yaml` or running:

```bash
FLASK_DEBUG=1 python app.py
```

## Production Deployment

### Security Considerations

- Change default PostgreSQL credentials
- Use environment variables for sensitive configuration
- Enable SSL/TLS for database connections
- Implement proper authentication for API endpoints
- Use a reverse proxy (nginx) for HTTPS termination

### Performance Tuning

- Adjust database connection pool size
- Configure Kafka consumer settings for throughput
- Monitor memory usage and adjust container limits
- Consider horizontal scaling for high load

### Monitoring

- Set up log aggregation (ELK stack, Fluentd)
- Monitor health endpoints with external tools
- Track database performance metrics
- Monitor Kafka consumer lag

## License

This project is part of the real-time LLM ingestion pipeline and follows the same license terms.