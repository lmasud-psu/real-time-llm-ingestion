#!/usr/bin/env python3
"""
Kafka CLI Tool
A simple command-line interface for managing Kafka topics and operations.
"""

import json
import time
import uuid
from typing import List, Optional
import click
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError, UnknownTopicOrPartitionError, KafkaError


class KafkaCLI:
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """Initialize the Kafka CLI with connection settings."""
        self.bootstrap_servers = bootstrap_servers
        self.admin_client = None
        self.producer = None
        self.consumer = None
        
    def _get_admin_client(self):
        """Get or create admin client."""
        if self.admin_client is None:
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id='kafka-cli-admin'
            )
        return self.admin_client
    
    def _get_producer(self):
        """Get or create producer."""
        if self.producer is None:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
        return self.producer
    
    def _get_consumer(self, topic: str, group_id: str = "kafka-cli-consumer"):
        """Get or create consumer."""
        if self.consumer is None:
            self.consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
        return self.consumer
    
    def create_topic(self, topic_name: str, partitions: int = 1, replication_factor: int = 1) -> bool:
        """Create a new Kafka topic."""
        try:
            admin_client = self._get_admin_client()
            
            # Check if topic already exists
            existing_topics = admin_client.list_topics()
            if topic_name in existing_topics:
                click.echo(f"Topic '{topic_name}' already exists.")
                return False
            
            # Create new topic
            topic = NewTopic(
                name=topic_name,
                num_partitions=partitions,
                replication_factor=replication_factor
            )
            
            admin_client.create_topics([topic])
            click.echo(f"Successfully created topic '{topic_name}' with {partitions} partitions and replication factor {replication_factor}.")
            return True
            
        except TopicAlreadyExistsError:
            click.echo(f"Topic '{topic_name}' already exists.")
            return False
        except KafkaError as e:
            click.echo(f"Error creating topic '{topic_name}': {e}", err=True)
            return False
    
    def delete_topic(self, topic_name: str) -> bool:
        """Delete a Kafka topic."""
        try:
            admin_client = self._get_admin_client()
            
            # Check if topic exists
            existing_topics = admin_client.list_topics()
            if topic_name not in existing_topics:
                click.echo(f"Topic '{topic_name}' does not exist.")
                return False
            
            admin_client.delete_topics([topic_name])
            click.echo(f"Successfully deleted topic '{topic_name}'.")
            return True
            
        except UnknownTopicOrPartitionError:
            click.echo(f"Topic '{topic_name}' does not exist.")
            return False
        except KafkaError as e:
            click.echo(f"Error deleting topic '{topic_name}': {e}", err=True)
            return False
    
    def delete_all_topics(self) -> bool:
        """Delete all topics (except internal Kafka topics)."""
        try:
            admin_client = self._get_admin_client()
            existing_topics = admin_client.list_topics()
            
            # Filter out internal Kafka topics
            internal_topics = {'__consumer_offsets', '__transaction_state', '_schemas'}
            topics_to_delete = [topic for topic in existing_topics if topic not in internal_topics]
            
            if not topics_to_delete:
                click.echo("No user topics found to delete.")
                return True
            
            click.echo(f"Found {len(topics_to_delete)} topics to delete: {', '.join(topics_to_delete)}")
            if not click.confirm("Are you sure you want to delete all topics?"):
                click.echo("Operation cancelled.")
                return False
            
            admin_client.delete_topics(topics_to_delete)
            click.echo(f"Successfully deleted {len(topics_to_delete)} topics.")
            return True
            
        except KafkaError as e:
            click.echo(f"Error deleting topics: {e}", err=True)
            return False
    
    def list_topics(self) -> List[str]:
        """List all topics."""
        try:
            admin_client = self._get_admin_client()
            topics = admin_client.list_topics()
            return list(topics)
        except KafkaError as e:
            click.echo(f"Error listing topics: {e}", err=True)
            return []
    
    def write_to_topic(self, topic_name: str, message: str, key: Optional[str] = None) -> bool:
        """Write a message to a Kafka topic."""
        try:
            producer = self._get_producer()
            
            # Check if topic exists
            admin_client = self._get_admin_client()
            existing_topics = admin_client.list_topics()
            if topic_name not in existing_topics:
                click.echo(f"Topic '{topic_name}' does not exist. Creating it...")
                if not self.create_topic(topic_name):
                    return False
            
            # Generate a unique ID for the message
            message_id = str(uuid.uuid4())
            
            # Structure the message with ID and timestamp
            structured_message = {
                "id": message_id,
                "text": message,
                "timestamp": time.time(),
                "source": "kafka-cli"
            }
            
            # Use the message ID as the key if no key is provided
            message_key = key if key else message_id
            
            # Send message
            future = producer.send(topic_name, value=structured_message, key=message_key)
            record_metadata = future.get(timeout=10)
            
            click.echo(f"Message sent to topic '{topic_name}' with ID '{message_id}' at partition {record_metadata.partition}, offset {record_metadata.offset}")
            return True
            
        except KafkaError as e:
            click.echo(f"Error writing to topic '{topic_name}': {e}", err=True)
            return False
    
    def read_from_topic(self, topic_name: str, group_id: str = "kafka-cli-consumer", max_messages: int = 10, timeout: int = 5) -> bool:
        """Read messages from a Kafka topic."""
        try:
            # Check if topic exists
            admin_client = self._get_admin_client()
            existing_topics = admin_client.list_topics()
            if topic_name not in existing_topics:
                click.echo(f"Topic '{topic_name}' does not exist.")
                return False
            
            consumer = self._get_consumer(topic_name, group_id)
            message_count = 0
            
            click.echo(f"Reading messages from topic '{topic_name}' (max {max_messages} messages, timeout {timeout}s)...")
            click.echo("Press Ctrl+C to stop reading.\n")
            
            try:
                for message in consumer:
                    click.echo(f"Partition: {message.partition}, Offset: {message.offset}")
                    if message.key:
                        click.echo(f"Key: {message.key}")
                    
                    # Handle both structured and simple message formats
                    message_value = message.value
                    if isinstance(message_value, dict):
                        if 'id' in message_value:
                            click.echo(f"Message ID: {message_value['id']}")
                        if 'text' in message_value:
                            click.echo(f"Text: {message_value['text']}")
                        if 'timestamp' in message_value:
                            click.echo(f"Message Timestamp: {message_value['timestamp']}")
                        if 'source' in message_value:
                            click.echo(f"Source: {message_value['source']}")
                        # Show full value for complex messages
                        click.echo(f"Full Value: {json.dumps(message_value, indent=2)}")
                    else:
                        click.echo(f"Value: {message_value}")
                    
                    click.echo(f"Kafka Timestamp: {message.timestamp}")
                    click.echo("-" * 50)
                    
                    message_count += 1
                    if message_count >= max_messages:
                        break
                        
            except KeyboardInterrupt:
                click.echo("\nStopped reading messages.")
            
            click.echo(f"Read {message_count} messages from topic '{topic_name}'.")
            return True
            
        except KafkaError as e:
            click.echo(f"Error reading from topic '{topic_name}': {e}", err=True)
            return False
    
    def close(self):
        """Close all connections."""
        if self.admin_client:
            self.admin_client.close()
        if self.producer:
            self.producer.close()
        if self.consumer:
            self.consumer.close()


@click.group()
@click.option('--bootstrap-servers', default='localhost:9092', 
              help='Kafka bootstrap servers (default: localhost:9092)')
@click.pass_context
def cli(ctx, bootstrap_servers):
    """Kafka CLI Tool for topic management and message operations."""
    ctx.ensure_object(dict)
    ctx.obj['bootstrap_servers'] = bootstrap_servers


@cli.command()
@click.argument('topic')
@click.option('--partitions', default=1, help='Number of partitions (default: 1)')
@click.option('--replication-factor', default=1, help='Replication factor (default: 1)')
@click.pass_context
def create_topic(ctx, topic, partitions, replication_factor):
    """Create a new topic."""
    kafka_cli = KafkaCLI(ctx.obj['bootstrap_servers'])
    try:
        kafka_cli.create_topic(topic, partitions, replication_factor)
    finally:
        kafka_cli.close()


@cli.command()
@click.argument('topic')
@click.pass_context
def delete_topic(ctx, topic):
    """Delete a topic."""
    kafka_cli = KafkaCLI(ctx.obj['bootstrap_servers'])
    try:
        kafka_cli.delete_topic(topic)
    finally:
        kafka_cli.close()


@cli.command()
@click.pass_context
def delete_all_topics(ctx):
    """Delete all topics."""
    kafka_cli = KafkaCLI(ctx.obj['bootstrap_servers'])
    try:
        kafka_cli.delete_all_topics()
    finally:
        kafka_cli.close()


@cli.command()
@click.pass_context
def list_topics(ctx):
    """List all topics."""
    kafka_cli = KafkaCLI(ctx.obj['bootstrap_servers'])
    try:
        topics = kafka_cli.list_topics()
        if topics:
            click.echo("Available topics:")
            for topic in sorted(topics):
                click.echo(f"  - {topic}")
        else:
            click.echo("No topics found.")
    finally:
        kafka_cli.close()


@cli.command()
@click.argument('topic')
@click.argument('message')
@click.option('--key', help='Message key (optional)')
@click.pass_context
def write(ctx, topic, message, key):
    """Write a message to a topic."""
    kafka_cli = KafkaCLI(ctx.obj['bootstrap_servers'])
    try:
        kafka_cli.write_to_topic(topic, message, key)
    finally:
        kafka_cli.close()


@cli.command()
@click.argument('topic')
@click.option('--group-id', default='kafka-cli-consumer', help='Consumer group ID (default: kafka-cli-consumer)')
@click.option('--max-messages', default=10, help='Maximum messages to read (default: 10)')
@click.option('--timeout', default=5, help='Timeout in seconds (default: 5)')
@click.pass_context
def read(ctx, topic, group_id, max_messages, timeout):
    """Read messages from a topic."""
    kafka_cli = KafkaCLI(ctx.obj['bootstrap_servers'])
    try:
        kafka_cli.read_from_topic(topic, group_id, max_messages, timeout)
    finally:
        kafka_cli.close()


if __name__ == '__main__':
    cli()