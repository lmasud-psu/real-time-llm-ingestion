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

# Check if docker ps works
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Current user does not have permission to run docker commands."
    echo "🔧 Adding user '$USER' to the docker group..."
    sudo usermod -aG docker $USER
    newgrp docker
    echo "✅ User '$USER' added to docker group."
fi

# Check if tilt is installed
if ! command -v tilt &> /dev/null; then
    echo "🛠️ Tilt not found. Installing Tilt..."
    curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash
    echo "✅ Tilt installed."
fi

# Install Python dependencies for Kafka CLI
if [ -f "../kafka/requirements.txt" ]; then
    echo "📦 Installing Python dependencies for Kafka CLI..."
    pip install -r ../kafka/requirements.txt
fi

# Launch Tiltfile
export DATABASE_TYPE

echo "🚀 Launching Tilt for Real-time LLM Ingestion Architecture with database: $DATABASE_TYPE"
tilt up

exit 0
