# Kafka CLI Tool Usage Guide

A Python command-line interface for managing Kafka topics and performing message operations.

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Note:** The CLI now uses the `click` library for a better user experience with improved help messages, command structure, and error handling.

2. **Make the script executable (optional):**
   ```bash
   chmod +x kafka_cli.py
   ```

## Prerequisites

- Kafka cluster running (use `docker compose up -d` in this directory)
- Python 3.6 or higher
- kafka-python library

## Commands

### 1. Create a Topic

Create a new Kafka topic with specified partitions and replication factor.

```bash
# Basic topic creation
python kafka_cli.py create-topic my-topic

# With custom partitions and replication factor
python kafka_cli.py create-topic my-topic --partitions 3 --replication-factor 1

# Using different Kafka server
python kafka_cli.py --bootstrap-servers localhost:9092 create-topic my-topic
```

### 2. Delete a Topic

Delete a specific topic.

```bash
python kafka_cli.py delete-topic my-topic
```

### 3. Delete All Topics

Delete all user-created topics (preserves internal Kafka topics).

```bash
python kafka_cli.py delete-all-topics
```

**Note:** This command will ask for confirmation before proceeding.

### 4. List Topics

List all available topics in the cluster.

```bash
python kafka_cli.py list-topics
```

### 5. Write to Topic

Send a message to a specified topic.

```bash
# Simple message
python kafka_cli.py write my-topic "Hello, Kafka!"

# Message with key
python kafka_cli.py write my-topic "Hello, Kafka!" --key "message-1"

# JSON message
python kafka_cli.py write my-topic '{"user": "john", "action": "login"}' --key "user-john"
```

### 6. Read from Topic

Read messages from a specified topic.

```bash
# Read up to 10 messages (default)
python kafka_cli.py read my-topic

# Read specific number of messages
python kafka_cli.py read my-topic --max-messages 5

# Read with custom consumer group
python kafka_cli.py read my-topic --group-id my-consumer-group

# Read with timeout
python kafka_cli.py read my-topic --timeout 10
```

## Examples

### Complete Workflow Example

```bash
# 1. Start Kafka cluster
docker compose up -d

# 2. Create a topic
python kafka_cli.py create-topic user-events --partitions 3

# 3. List topics to verify
python kafka_cli.py list-topics

# 4. Write some messages
python kafka_cli.py write user-events '{"user_id": 123, "event": "login"}' --key "user-123"
python kafka_cli.py write user-events '{"user_id": 456, "event": "purchase"}' --key "user-456"

# 5. Read messages
python kafka_cli.py read user-events --max-messages 5

# 6. Clean up (optional)
python kafka_cli.py delete-topic user-events
```

### Testing Message Flow

```bash
# Terminal 1: Start reading messages (will wait for new messages)
python kafka_cli.py read my-topic --max-messages 100

# Terminal 2: Send messages
python kafka_cli.py write my-topic "Message 1"
python kafka_cli.py write my-topic "Message 2"
python kafka_cli.py write my-topic "Message 3"
```

## Error Handling

The CLI tool includes comprehensive error handling:

- **Topic already exists**: Warns if trying to create an existing topic
- **Topic not found**: Warns if trying to delete/read from non-existent topic
- **Connection errors**: Provides clear error messages for connection issues
- **Permission errors**: Handles Kafka permission issues gracefully

## Configuration

### Default Settings

- **Bootstrap servers**: `localhost:9092`
- **Partitions**: 1
- **Replication factor**: 1
- **Max messages to read**: 10
- **Consumer group**: `kafka-cli-consumer`
- **Auto offset reset**: `earliest`

### Custom Configuration

You can override the default Kafka server:

```bash
python kafka_cli.py --bootstrap-servers kafka1:9092,kafka2:9092 list-topics
```

## Tips

1. **Use Ctrl+C** to stop reading messages in the read command
2. **Message keys** are useful for partitioning and ordering
3. **Consumer groups** allow multiple consumers to read from the same topic
4. **JSON messages** are automatically serialized/deserialized
5. **Internal topics** (like `__consumer_offsets`) are preserved when deleting all topics

## Troubleshooting

### Common Issues

1. **Connection refused**: Make sure Kafka is running (`docker compose ps`)
2. **Topic not found**: Create the topic first or check spelling
3. **Permission denied**: Ensure your user has Docker permissions
4. **Import errors**: Install requirements with `pip install -r requirements.txt`

### Debug Mode

For more verbose output, you can modify the script to include debug logging or check the Kafka UI at http://localhost:8080.
