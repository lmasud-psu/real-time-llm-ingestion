#!/usr/bin/env python3
"""
Embedding Generation Service
A Flask service that reads text messages from Kafka, generates embeddings using Hugging Face models,
and writes the embeddings back to Kafka.
"""

import json
import logging
import threading
import time
from typing import Dict, Any, Optional
import yaml
from flask import Flask, jsonify, request
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from sentence_transformers import SentenceTransformer
import torch
import numpy as np


class EmbeddingService:
    """Main service class for generating embeddings from Kafka messages."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the embedding service with configuration."""
        self.config = self._load_config(config_path)
        self.model = None
        self.consumer = None
        self.producer = None
        self.is_running = False
        self.consumer_thread = None
        self.stats = {
            "messages_processed": 0,
            "embeddings_generated": 0,
            "errors": 0,
            "last_processed": None
        }
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {config_path} not found")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO').upper())
        format_str = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        logging.basicConfig(
            level=level,
            format=format_str,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('embedding_service.log')
            ]
        )
    
    def _load_model(self):
        """Load the Hugging Face model for embedding generation."""
        model_config = self.config['model']
        model_name = model_config['name']
        device = model_config.get('device', 'cpu')
        
        self.logger.info(f"Loading model: {model_name} on device: {device}")
        
        try:
            self.model = SentenceTransformer(model_name, device=device)
            self.logger.info(f"Successfully loaded model: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def _setup_kafka_consumer(self):
        """Setup Kafka consumer for reading messages."""
        kafka_config = self.config['kafka']
        
        self.logger.info(f"Setting up Kafka consumer for topic: {kafka_config['input_topic']}")
        
        try:
            self.consumer = KafkaConsumer(
                kafka_config['input_topic'],
                bootstrap_servers=kafka_config['bootstrap_servers'],
                group_id=kafka_config['consumer_group'],
                auto_offset_reset=kafka_config.get('auto_offset_reset', 'latest'),
                enable_auto_commit=kafka_config.get('enable_auto_commit', True),
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                consumer_timeout_ms=1000  # 1 second timeout for graceful shutdown
            )
            self.logger.info("Kafka consumer setup successful")
        except Exception as e:
            self.logger.error(f"Failed to setup Kafka consumer: {e}")
            raise
    
    def _setup_kafka_producer(self):
        """Setup Kafka producer for writing embeddings."""
        kafka_config = self.config['kafka']
        
        self.logger.info(f"Setting up Kafka producer for topic: {kafka_config['output_topic']}")
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=3,
                retry_backoff_ms=100
            )
            self.logger.info("Kafka producer setup successful")
        except Exception as e:
            self.logger.error(f"Failed to setup Kafka producer: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for the given text."""
        if not self.model:
            self.logger.error("Model not loaded")
            return None
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def _process_message(self, message):
        """Process a single Kafka message and generate embedding."""
        try:
            # Extract text from message
            message_data = message.value
            if isinstance(message_data, dict):
                text = message_data.get('text', '')
                message_id = message_data.get('id', message.key or 'unknown')
                # Preserve additional metadata from input message
                input_timestamp = message_data.get('timestamp')
                input_source = message_data.get('source')
            else:
                text = str(message_data)
                message_id = message.key or 'unknown'
                input_timestamp = None
                input_source = None
            
            if not text.strip():
                self.logger.warning(f"Empty text in message {message_id}")
                return
            
            self.logger.info(f"Processing message {message_id}: {text[:100]}...")
            
            # Generate embedding
            embedding = self._generate_embedding(text)
            if embedding is None:
                self.stats["errors"] += 1
                return
            
            # Prepare output message with preserved metadata
            output_message = {
                "id": message_id,
                "original_text": text,
                "embedding": embedding.tolist(),  # Convert numpy array to list
                "model_name": self.config['model']['name'],
                "timestamp": time.time(),
                "embedding_dimension": len(embedding),
                "processing_timestamp": time.time()
            }
            
            # Preserve input metadata if available
            if input_timestamp:
                output_message["input_timestamp"] = input_timestamp
            if input_source:
                output_message["input_source"] = input_source
            
            # Send to output topic
            kafka_config = self.config['kafka']
            future = self.producer.send(
                kafka_config['output_topic'],
                value=output_message,
                key=message_id
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            self.logger.info(f"Embedding sent to topic {kafka_config['output_topic']} at partition {record_metadata.partition}, offset {record_metadata.offset}")
            
            # Update stats
            self.stats["messages_processed"] += 1
            self.stats["embeddings_generated"] += 1
            self.stats["last_processed"] = time.time()
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.stats["errors"] += 1
    
    def _consume_messages(self):
        """Main consumer loop for processing Kafka messages."""
        self.logger.info("Starting message consumption loop")
        
        while self.is_running:
            try:
                # Poll for messages
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                if message_batch:
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            if self.is_running:
                                self._process_message(message)
                            else:
                                break
                
            except Exception as e:
                self.logger.error(f"Error in consumer loop: {e}")
                time.sleep(1)  # Brief pause before retrying
        
        self.logger.info("Message consumption loop stopped")
    
    def start(self):
        """Start the embedding service."""
        if self.is_running:
            self.logger.warning("Service is already running")
            return
        
        self.logger.info("Starting embedding generation service")
        
        try:
            # Load model
            self._load_model()
            
            # Setup Kafka connections
            self._setup_kafka_consumer()
            self._setup_kafka_producer()
            
            # Start consumer thread
            self.is_running = True
            self.consumer_thread = threading.Thread(target=self._consume_messages, daemon=True)
            self.consumer_thread.start()
            
            self.logger.info("Embedding generation service started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the embedding service."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping embedding generation service")
        self.is_running = False
        
        # Wait for consumer thread to finish
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5)
        
        # Close Kafka connections
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.close()
        
        self.logger.info("Embedding generation service stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            **self.stats,
            "is_running": self.is_running,
            "model_loaded": self.model is not None,
            "consumer_connected": self.consumer is not None,
            "producer_connected": self.producer is not None
        }


# Flask application
app = Flask(__name__)
embedding_service = None


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    if embedding_service is None:
        return jsonify({"status": "error", "message": "Service not initialized"}), 500
    
    stats = embedding_service.get_stats()
    return jsonify({
        "status": "healthy" if stats["is_running"] else "stopped",
        "service": "embedding-generation-service",
        "stats": stats
    })


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get service statistics."""
    if embedding_service is None:
        return jsonify({"error": "Service not initialized"}), 500
    
    return jsonify(embedding_service.get_stats())


@app.route('/start', methods=['POST'])
def start_service():
    """Start the embedding service."""
    global embedding_service
    
    if embedding_service is None:
        return jsonify({"error": "Service not initialized"}), 500
    
    if embedding_service.is_running:
        return jsonify({"message": "Service is already running"}), 200
    
    try:
        embedding_service.start()
        return jsonify({"message": "Service started successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to start service: {str(e)}"}), 500


@app.route('/stop', methods=['POST'])
def stop_service():
    """Stop the embedding service."""
    global embedding_service
    
    if embedding_service is None:
        return jsonify({"error": "Service not initialized"}), 500
    
    try:
        embedding_service.stop()
        return jsonify({"message": "Service stopped successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to stop service: {str(e)}"}), 500


@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration (without sensitive data)."""
    if embedding_service is None:
        return jsonify({"error": "Service not initialized"}), 500
    
    config = embedding_service.config.copy()
    # Remove any sensitive information if needed
    return jsonify(config)


def main():
    """Main function to run the Flask application."""
    global embedding_service
    
    # Initialize the embedding service
    embedding_service = EmbeddingService()
    
    # Get Flask configuration
    flask_config = embedding_service.config.get('flask', {})
    host = flask_config.get('host', '0.0.0.0')
    port = flask_config.get('port', 5000)
    debug = flask_config.get('debug', False)
    
    # Start the service
    try:
        embedding_service.start()
        app.logger.info(f"Starting Flask application on {host}:{port}")
        app.run(host=host, port=port, debug=debug, threaded=True)
    except KeyboardInterrupt:
        app.logger.info("Received interrupt signal")
    except Exception as e:
        app.logger.error(f"Application error: {e}")
    finally:
        if embedding_service:
            embedding_service.stop()


if __name__ == '__main__':
    main()
