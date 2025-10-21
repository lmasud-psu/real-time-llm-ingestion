#!/bin/bash

echo "Setting up directories for Real-time LLM Ingestion Architecture..."

# Create logs directory
mkdir -p ../writer_svc/logs
echo "✅ Created ../writer_svc/logs"

echo ""
echo "🎉 Directory setup complete!"
echo ""
echo "You can now start the architecture with:"
echo "  • PostgreSQL: tilt up"
