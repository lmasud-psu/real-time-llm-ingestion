# Real-Time LLM Ingestion Experiments

This directory contains experiment frameworks for measuring end-to-end performance across different architectures for real-time text ingestion and embedding generation.

## Architecture Comparison

| Feature | Architecture 1 | Architecture 3 |
|---------|---------------|----------------|
| **Pipeline** | Kafka → Embedding Service → Writer Service | Direct CQRS Command Handling |
| **Topics** | `text-messages` → `embeddings` | N/A (no Kafka output) |
| **Database** | `embeddings` table, `id` field | `text_embeddings` table, `text_message_id` field |
| **PostgreSQL Port** | 5432 (standard) | 5434 (non-standard) |
| **Monitoring** | Kafka topics + Database | Database only |
| **Latency Measurement** | Full pipeline (3 stages) | Command → Database (2 stages) |

## Quick Start

### Architecture 1 (Kafka Pipeline)
```bash
cd experiments/architecture1/
./run_experiments.sh setup    # Setup environment
./run_experiments.sh smoke    # Test infrastructure
./run_experiments.sh example  # Complete demonstration
```

### Architecture 3 (CQRS)
```bash
cd experiments/architecture3/
./run_experiments.sh setup    # Setup environment  
./run_experiments.sh smoke    # Test infrastructure
./run_experiments.sh example  # Complete demonstration
```

## Framework Features

Both architectures support:
- **3 Datasets**: CC News, Arxiv abstracts, Wikipedia articles
- **Configurable Chunking**: 0.5KB - 80KB chunk sizes
- **Burst Patterns**: Steady rate vs. burst traffic simulation
- **Comprehensive Metrics**: Throughput, latency, success rates
- **CSV Output**: Compatible format for cross-architecture analysis

## Legacy Single-Directory Experiments

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
