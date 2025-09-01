#!/usr/bin/env python3
"""
Test script for the Embedding Generation Service
This script demonstrates how to send messages and receive embeddings.
"""

import json
import time
import requests
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError


def test_service():
    """Test the embedding generation service."""
    print("Testing Embedding Generation Service")
    print("=" * 50)
    
    # Test messages (now the CLI will auto-generate IDs)
    test_messages = [
        "Machine learning is revolutionizing technology",
        "Natural language processing with transformers is amazing",
        "Embeddings capture semantic meaning in vector space",
        "Kafka enables real-time data streaming",
        "Flask makes web services easy to build"
    ]
    
    # Setup Kafka producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        print("SUCCESS: Kafka producer connected")
    except Exception as e:
        print(f"ERROR: Failed to connect to Kafka: {e}")
        return
    
    # Setup Kafka consumer for embeddings
    try:
        consumer = KafkaConsumer(
            'embeddings',
            bootstrap_servers=['localhost:9092'],
            group_id='test-consumer',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='latest'
        )
        print("SUCCESS: Kafka consumer connected")
    except Exception as e:
        print(f"ERROR: Failed to connect to Kafka consumer: {e}")
        return
    
    # Check service health
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"SUCCESS: Service is healthy: {health_data['status']}")
        else:
            print(f"ERROR: Service health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"ERROR: Service not responding: {e}")
        print("Make sure the service is running: python app.py")
        return
    
    # Send test messages
    print("\nSending test messages...")
    for i, message_text in enumerate(test_messages):
        try:
            # Create structured message with ID (mimicking CLI behavior)
            import uuid
            import time
            message_id = str(uuid.uuid4())
            structured_message = {
                "id": message_id,
                "text": message_text,
                "timestamp": time.time(),
                "source": "test-script"
            }
            
            future = producer.send('text-messages', value=structured_message, key=message_id)
            record_metadata = future.get(timeout=10)
            print(f"SUCCESS: Sent message {message_id}: {message_text[:50]}...")
        except Exception as e:
            print(f"ERROR: Failed to send message {i+1}: {e}")
    
    producer.flush()
    print(f"Sent {len(test_messages)} messages")
    
    # Wait a moment for processing
    print("\nWaiting for embeddings to be generated...")
    time.sleep(5)
    
    # Read embeddings
    print("\nReading generated embeddings...")
    embedding_count = 0
    max_wait_time = 30  # seconds
    start_time = time.time()
    
    try:
        for message in consumer:
            if time.time() - start_time > max_wait_time:
                print("TIMEOUT: Waiting for embeddings")
                break
                
            embedding_data = message.value
            embedding_id = embedding_data.get('id', 'unknown')
            embedding_dim = embedding_data.get('embedding_dimension', 0)
            model_name = embedding_data.get('model_name', 'unknown')
            
            print(f"SUCCESS: Received embedding for {embedding_id}:")
            print(f"   - Model: {model_name}")
            print(f"   - Dimension: {embedding_dim}")
            print(f"   - Original text: {embedding_data.get('original_text', '')[:50]}...")
            print(f"   - Embedding preview: {embedding_data.get('embedding', [])[:5]}...")
            print()
            
            embedding_count += 1
            if embedding_count >= len(test_messages):
                break
                
    except Exception as e:
        print(f"ERROR: Error reading embeddings: {e}")
    
    # Get final statistics
    try:
        response = requests.get('http://localhost:5000/stats', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("Final Statistics:")
            print(f"   - Messages processed: {stats.get('messages_processed', 0)}")
            print(f"   - Embeddings generated: {stats.get('embeddings_generated', 0)}")
            print(f"   - Errors: {stats.get('errors', 0)}")
            print(f"   - Service running: {stats.get('is_running', False)}")
    except Exception as e:
        print(f"ERROR: Failed to get statistics: {e}")
    
    # Cleanup
    producer.close()
    consumer.close()
    
    print(f"\nTest completed! Generated {embedding_count} embeddings")


def test_service_endpoints():
    """Test the REST API endpoints."""
    print("\nTesting REST API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"SUCCESS: Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
    except Exception as e:
        print(f"ERROR: Health check failed: {e}")
    
    # Test stats endpoint
    try:
        response = requests.get(f"{base_url}/stats")
        print(f"SUCCESS: Stats endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Messages processed: {data.get('messages_processed', 0)}")
    except Exception as e:
        print(f"ERROR: Stats endpoint failed: {e}")
    
    # Test config endpoint
    try:
        response = requests.get(f"{base_url}/config")
        print(f"SUCCESS: Config endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Model: {data.get('model', {}).get('name', 'unknown')}")
    except Exception as e:
        print(f"ERROR: Config endpoint failed: {e}")


if __name__ == "__main__":
    print("Embedding Generation Service Test Suite")
    print("Make sure the service is running: python app.py")
    print("Make sure Kafka is running: docker compose up -d")
    print()
    
    # Test REST endpoints first
    test_service_endpoints()
    
    # Test the full workflow
    test_service()
    
    print("\nAll tests completed!")
