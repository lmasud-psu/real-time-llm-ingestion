#!/bin/bash

# Startup script for Real-time LLM Ingestion Architecture
# Uses centralized docker-compose.yml to orchestrate all services

set -e

# Default database type
DATABASE_TYPE=${DATABASE_TYPE:-lancedb}

echo "🚀 Starting Real-time LLM Ingestion Architecture with database: $DATABASE_TYPE"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping all services..."
    docker compose down
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start services based on database type
if [ "$DATABASE_TYPE" = "postgres" ]; then
    echo "📊 Starting with PostgreSQL + pgvector..."
    docker compose --profile postgres up -d
else
    echo "🗄️ Starting with LanceDB..."
    docker compose --profile lancedb up -d
fi

echo "✅ All services started successfully!"
echo "📊 Kafka UI: http://localhost:8080"
echo "🔍 Schema Registry: http://localhost:8081"
echo "🔗 Kafka Connect: http://localhost:8083"
echo "🧠 Embedding Service: http://localhost:5000"
echo "✍️ Writer Service: http://localhost:5001"

if [ "$DATABASE_TYPE" = "postgres" ]; then
    echo "🐘 PostgreSQL: localhost:5432"
    echo "📊 pgAdmin: http://localhost:8080 (admin@example.com / admin)"
else
    echo "🗄️ LanceDB: Ready for CLI operations"
fi

echo ""
echo "🔧 Use 'docker compose logs -f <service-name>' to view logs"
echo "🛑 Use 'docker compose down' to stop all services"
echo "📊 Use 'docker compose ps' to check service status"

# Wait for user interrupt
echo ""
echo "⏳ Press Ctrl+C to stop all services..."
wait
