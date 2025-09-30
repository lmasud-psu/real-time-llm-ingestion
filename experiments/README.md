# Ingestion Experiments (Kafka -> Embedding -> PGVector)

Run end-to-end latency experiments by sending the contents of files under `experiments/datasets/<name>` to Kafka and measuring when embeddings appear in Postgres.

## Setup

1. Create and activate a virtual environment:
```bash
cd experiments/
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Requirements
- Kafka and services running (embedding service, writer service, postgres)
- Python dependencies installed from requirements.txt (kafka-python, psycopg2-binary)

## Run single-directory experiment
```bash
cd /home/latif/doctoral/real-time-llm-ingestion/experiments/
source venv/bin/activate  # Activate virtual environment
python run_ingestion_experiment.py \
  --dataset-dir ./datasets/smoke \
  --bootstrap-servers localhost:9092 \
  --input-topic text-messages \
  --output-topic embeddings \
  --table text_message_embeddings \
  --timeout 60
```

Environment variables can override connection settings:
- DATABASE_HOST (default: localhost)
- DATABASE_PORT (default: 5432)
- DATABASE_NAME (default: embeddings_db)
- DATABASE_USER (default: postgres)
- DATABASE_PASSWORD (default: postgres)
- KAFKA_BOOTSTRAP_SERVERS (default: localhost:9092)

The script prints a JSON report with total time and per-file step breakdowns.
