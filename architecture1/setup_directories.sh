#!/bin/bash

echo "Setting up directories for Real-time LLM Ingestion Architecture..."

# Create writer service data directory
mkdir -p ../writer_svc/lancedb_data
echo "✅ Created ../writer_svc/lancedb_data"

# Set proper permissions
chmod 755 ../writer_svc/lancedb_data
echo "✅ Set permissions on lancedb_data directory"

# Create logs directory
mkdir -p ../writer_svc/logs
echo "✅ Created ../writer_svc/logs"

echo ""
echo "🎉 Directory setup complete!"
echo ""
echo "You can now start the architecture with:"
echo "  • LanceDB: tilt up"
echo "  • PostgreSQL: DATABASE_TYPE=postgres tilt up"
