#!/bin/bash

if [ "$1" = "submit" ]; then
    echo "Waiting for JobManager to be ready..."
    until curl -s "flink-jobmanager:8081" > /dev/null; do
        echo "JobManager is unavailable - sleeping"
        sleep 2
    done
    echo "JobManager is up - submitting job"
    
    # Set environment variables for the Flink job
    export EMBEDDING_SERVICE_URL=${EMBEDDING_SERVICE_URL:-http://embedding-service:5000}
    export PGVECTOR_HOST=${PGVECTOR_HOST:-pgvector-postgres}
    export PGVECTOR_DB=${PGVECTOR_DB:-embeddings_db}
    export PGVECTOR_USER=${PGVECTOR_USER:-postgres}
    export PGVECTOR_PASSWORD=${PGVECTOR_PASSWORD:-postgres}
    export PGVECTOR_TABLE=${PGVECTOR_TABLE:-text_message_embeddings}
    export PGVECTOR_DIMENSION=${PGVECTOR_DIMENSION:-384}
    export KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS:-kafka:29092}
    export KAFKA_INPUT_TOPIC=${KAFKA_INPUT_TOPIC:-text-messages}
    export KAFKA_GROUP_ID=${KAFKA_GROUP_ID:-flink-embedding-consumer}
    export FLINK_PARALLELISM=${FLINK_PARALLELISM:-1}
    
    echo "Submitting Java job with environment variables set..."
    flink run -m flink-jobmanager:8081 -d /opt/flink/usrlib/embedding-pipeline.jar
else
    # Call the original Flink entrypoint
    exec /docker-entrypoint.sh "$@"
fi
