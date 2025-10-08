#!/bin/bash

# Architecture 3 Start Script
# This script starts the Text Writer Service architecture with Kafka and PostgreSQL

set -e

echo "[ARCH3] Starting Architecture 3 - Text Writer Service Pipeline"

# Create external network if it doesn't exist
if ! docker network ls | grep -q rt-llm-network; then
    echo "[ARCH3] Creating rt-llm-network..."
    docker network create rt-llm-network
fi

# Build and start services
echo "[ARCH3] Building and starting services..."
docker compose up -d --build

# Wait for services to be healthy
echo "[ARCH3] Waiting for services to be ready..."

# Wait for PostgreSQL
echo "[ARCH3] Waiting for PostgreSQL..."
timeout 60 bash -c 'until docker compose exec postgres pg_isready -U postgres -d text_messages_db; do sleep 2; done'

# Wait for Kafka
echo "[ARCH3] Waiting for Kafka..."
timeout 60 bash -c 'until docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list &>/dev/null; do sleep 2; done'

# Wait for text-writer-service
echo "[ARCH3] Waiting for Text Writer Service..."
timeout 60 bash -c 'until curl -s http://localhost:5002/health &>/dev/null; do sleep 2; done'

echo "[ARCH3] ✅ All services are ready!"
echo ""
echo "Service URLs:"
echo "  - Text Writer Service API: http://localhost:5002"
echo "  - Text Writer Service Health: http://localhost:5002/health"
echo "  - Kafka UI: http://localhost:8080"
echo "  - PostgreSQL: localhost:5434 (user: postgres, db: text_messages_db)"
echo ""
echo "Available CLI commands:"
echo "  cd ../text_writer_svc && python cli.py --url http://localhost:5002 health"
echo "  cd ../text_writer_svc && python cli.py --url http://localhost:5002 list"
echo "  cd ../text_writer_svc && python cli.py --url http://localhost:5002 create 'Hello World'"
echo ""
echo "To send test messages to Kafka:"
echo "  cd ../kafka && python kafka_cli.py produce text-messages '{\"id\":\"test-123\",\"text\":\"Hello from Kafka\"}'"
echo ""
echo "[ARCH3] Architecture 3 is ready for testing!"