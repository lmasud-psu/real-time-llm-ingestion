# Flink Streaming Architecture

This architecture spins up Kafka, the embedding generation service, Apache Flink, and pgvector to build a real-time ingestion pipeline that enriches messages with embeddings and writes them to PostgreSQL.

## Pipeline
- **Kafka (`text-messages`)**: Source topic for raw text payloads.
- **Embedding Service**: Flask service that returns sentence-transformer embeddings via `/generate`.
- **PyFlink Job**: Consumes Kafka messages, calls the embedding service, and persists results to pgvector.
- **pgvector**: Stores the final vectors in the `text_message_embeddings` table.

## Getting Started
1. Build and start the stack:
   ```bash
   docker compose up --build
   ```
2. Produce messages to Kafka (`text-messages`). Each message should be JSON with at least a `text` field, e.g.:
   ```bash
   docker compose exec kafka kafka-console-producer \
     --bootstrap-server kafka:29092 \
     --topic text-messages
   > {"id": "msg-1", "text": "Flink streaming for embeddings"}
   ```
3. Inspect pgvector to confirm inserts:
   ```bash
   docker compose exec pgvector-postgres psql -U postgres -d embeddings_db \
     -c 'SELECT id, model_name, embedding[1:5] FROM text_message_embeddings LIMIT 5;'
   ```
4. Run the end-to-end validation script:
   ```bash
   ./e2e_test.sh
   ```

## Services
- **Flink Dashboard**: http://localhost:8081
- **Kafka UI**: http://localhost:8082
- **pgAdmin**: http://localhost:8080 (user: `admin@example.com`, password: `admin`)
- **Embedding Service Health**: http://localhost:5000/health

## Configuration
Environment variables for the job can be overridden through the `flink-jobmanager`, `flink-taskmanager`, and `flink-submit` services. Key options include:
- `EMBEDDING_SERVICE_URL`
- `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_INPUT_TOPIC`, `KAFKA_GROUP_ID`
- `PGVECTOR_HOST`, `PGVECTOR_DB`, `PGVECTOR_USER`, `PGVECTOR_PASSWORD`, `PGVECTOR_TABLE`, `PGVECTOR_DIMENSION`
- `FLINK_PARALLELISM`, `FLINK_CHECKPOINT_INTERVAL_MS`

## Notes
- The Flink container image is defined in `../flink/Dockerfile` and installs the Kafka connector along with Python dependencies.
- `flink-submit` waits for the JobManager REST endpoint before submitting the PyFlink job and then tails the Flink logs.
- The embedding service has a new `/generate` endpoint that enables synchronous embedding generation for the Flink job.
