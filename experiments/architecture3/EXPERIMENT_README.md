# Multi-Dataset Ingestion Experiments

This directory contains tools for running comprehensive ingestion experiments across multiple datasets (CC News, Arxiv, Wikipedia) with configurable parameters to measure end-to-end latency and throughput performance.

## 📋 Overview

The experiment infrastructure provides:
- **Multi-dataset support**: CC News, Arxiv, Wikipedia streaming APIs
- **Configurable chunk sizes**: 0.5KB to 80KB with automatic token conversion
- **Burst pattern testing**: Configurable burst durations and intervals
- **End-to-end measurement**: From streaming → Kafka → embedding generation → vector database
- **CSV result output**: Detailed performance metrics for analysis
- **Smoke testing**: Quick validation of infrastructure setup

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
cd /home/latif/doctoral/real-time-llm-ingestion/architecture3
python3 -m venv experiment_venv
source experiment_venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Test Infrastructure

```bash
# Test dataset streaming without Kafka/DB (recommended first step)
python test_experiment_setup.py

# Test full infrastructure with Kafka/DB
python run_multi_dataset_experiments.py --smoke-test
```

### 3. Run Experiments

```bash
# Full experiment suite (all datasets, all chunk sizes, with/without burst)
python run_multi_dataset_experiments.py

# Quick test with specific parameters
python run_multi_dataset_experiments.py \
  --datasets cc_news arxiv wikipedia \
  --chunk-sizes 1 5 10 \
  --no-burst \
  --max-chunks 20

# Burst-only experiments
python run_multi_dataset_experiments.py \
  --datasets wikipedia \
  --chunk-sizes 2 10 \
  --burst-durations 30 60

# Most comprehensive test (all datasets, chunks, bursts)
python run_multi_dataset_experiments.py \
  --architecture architecture3 \
  --model "sentence-transformers/all-MiniLM-L6-v2" \
  --datasets cc_news arxiv wikipedia \
  --chunk-sizes 0.5 1 2 4 8 16 32 64 80 \
  --burst-durations 1 2 5 10 15 30 45 60 \
  --max-chunks 200 \
  --timeout 600
```

## 📁 Files

- **`run_multi_dataset_experiments.py`** - Main experiment runner
- **`test_experiment_setup.py`** - Infrastructure validation (no Kafka/DB required)
- **`run_ingestion_experiment.py`** - Original single-dataset experiment
- **`requirements.txt`** - Python dependencies
- **`experiment_venv/`** - Virtual environment
- **`experiment_results/`** - Output directory for CSV results

## 🔧 Configuration Options

### Dataset Selection
```bash
--datasets cc_news arxiv wikipedia    # Select specific datasets (default: all)
```

### Chunk Sizes
```bash
--chunk-sizes 0.5 1 2 5 10 20 40 80  # Chunk sizes in KB (default: 0.5-80)
```

### Burst Testing
```bash
--burst-durations 30 60               # Burst for 30s, 60s (default: 30,60)
--no-burst                            # Skip burst experiments
```

### Limits and Timeouts
```bash
--max-chunks 50                       # Max chunks per experiment (default: 50)
--timeout 300                         # Timeout per experiment in seconds (default: 300)
```

### Output
```bash
--output-dir ./custom_results         # Custom output directory (default: ./experiment_results)
```

## 📊 Experiment Types

### 1. Regular Streaming
- Streams data at consistent rate
- Tests normal ingestion pipeline performance
- Measures baseline latency and throughput

### 2. Burst Streaming
- Alternates between rapid bursts and pauses
- Simulates real-world traffic patterns
- Tests pipeline under load spikes

#### Burst Pattern Example:
```
Burst for 5s → Pause for 5s → Burst for 5s → ... (for 30-60s total)
```

## 📈 Metrics Collected

Each experiment produces detailed metrics:

| Metric | Description |
|--------|-------------|
| `dataset` | Dataset name (cc_news, arxiv, wikipedia) |
| `chunk_size_kb` | Chunk size in kilobytes |
| `chunk_size_tokens` | Equivalent chunk size in tokens |
| `burst_enabled` | Whether burst pattern was used |
| `burst_duration_s` | Total burst experiment duration |
| `burst_interval_s` | Burst/pause interval length |
| `chunks_produced` | Total chunks sent to Kafka |
| `chunks_processed` | Chunks processed by embedding service |
| `chunks_persisted` | Chunks verified in vector database |
| `total_duration_ms` | End-to-end experiment duration |
| `avg_latency_ms` | Average latency per chunk |
| `throughput_chunks_per_s` | Processing throughput (chunks/second) |
| `throughput_tokens_per_s` | Processing throughput (tokens/second) |
| `success_rate` | Percentage of successfully processed chunks |
| `status` | Experiment status (success/error) |
| `error_message` | Error details if applicable |

## 🎯 Example Experiment Configurations

### Basic Performance Test
```bash
python run_multi_dataset_experiments.py \
  --datasets cc_news \
  --chunk-sizes 1 5 10 \
  --no-burst \
  --max-chunks 30
```

### Burst Load Test
```bash
python run_multi_dataset_experiments.py \
  --datasets arxiv wikipedia \
  --chunk-sizes 2 8 \
  --burst-durations 45 \
  --max-chunks 25
```

### Comprehensive Suite
```bash
python run_multi_dataset_experiments.py \
  --datasets cc_news arxiv wikipedia \
  --chunk-sizes 0.5 2 10 40 \
  --burst-durations 30 60 \
  --max-chunks 40 \
  --timeout 400
```

## 📄 Results Analysis

Results are saved as CSV files in the output directory:

```bash
experiment_results/
├── ingestion_results_20231019_143022.csv     # Intermediate results
├── ingestion_results_20231019_143055.csv     # Updated results
└── final_ingestion_results_20231019_143127.csv # Final complete results
```

### Loading Results in Python
```python
import pandas as pd

# Load results
df = pd.read_csv('experiment_results/final_ingestion_results_20231019_143127.csv')

# Analyze throughput by dataset
throughput_by_dataset = df.groupby('dataset')['throughput_chunks_per_s'].mean()
print(throughput_by_dataset)

# Compare burst vs non-burst performance
burst_comparison = df.groupby('burst_enabled')['avg_latency_ms'].mean()
print(burst_comparison)

# Chunk size impact analysis
chunk_analysis = df.groupby('chunk_size_kb')['success_rate'].mean()
print(chunk_analysis)
```

## 🏗️ Infrastructure Requirements

### Required Services

1. **Kafka** (localhost:9092)
   ```bash
   # Start Kafka (from kafka directory)
   docker-compose up -d
   ```

2. **PostgreSQL with pgvector** (localhost:5432)
   ```bash
   # Start PostgreSQL (from pgvector directory)
   docker-compose up -d
   ```

3. **Embedding Generation Service**
   ```bash
   # Start embedding service (from cqrs_embedding_gen_svc directory)
   docker-compose up -d
   ```

### Environment Variables
```bash
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export KAFKA_INPUT_TOPIC="text-messages"
export KAFKA_OUTPUT_TOPIC="embeddings"
export DATABASE_HOST="localhost"
export DATABASE_PORT="5432"
export DATABASE_NAME="embeddings_db"
export DATABASE_USER="postgres"
export DATABASE_PASSWORD="postgres"
export EMBEDDINGS_TABLE="embeddings"
```

### Dataset Requirements

The experiments use the following dataset streaming APIs:

1. **CC News** (`datasets/cc_news/`)
   - Uses parquet files from HuggingFace
   - High throughput: ~16,000-48,000 chunks/s
   - Good for volume testing

2. **Arxiv** (`datasets/arxiv_abstracts/`)
   - Uses JSONL.gz files
   - Academic paper abstracts
   - Medium throughput: ~100-200 chunks/s

3. **Wikipedia** (`datasets/wikimedia_difs/`)
   - Uses HuggingFace datasets (with mock fallback)
   - Wikipedia article content
   - Variable throughput depending on data source

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the architecture3 directory
   cd /home/latif/doctoral/real-time-llm-ingestion/architecture3
   
   # Activate virtual environment
   source experiment_venv/bin/activate
   
   # Test imports
   python test_experiment_setup.py
   ```

2. **Kafka Connection Issues**
   ```bash
   # Check Kafka is running
   docker ps | grep kafka
   
   # Test Kafka connectivity
   python -c "from kafka import KafkaProducer; print('Kafka OK')"
   ```

3. **Database Connection Issues**
   ```bash
   # Check PostgreSQL is running
   docker ps | grep postgres
   
   # Test database connectivity
   python -c "import psycopg2; psycopg2.connect('host=localhost port=5432 dbname=embeddings_db user=postgres password=postgres'); print('DB OK')"
   ```

4. **Performance Issues**
   ```bash
   # Reduce experiment scale for testing
   python run_multi_dataset_experiments.py \
     --datasets cc_news \
     --chunk-sizes 1 \
     --max-chunks 5 \
     --no-burst
   ```

### Monitoring

Monitor experiment progress:

```bash
# Check Kafka topics
kafka-console-consumer --bootstrap-server localhost:9092 --topic text-messages --from-beginning

# Check database
psql -h localhost -U postgres -d embeddings_db -c "SELECT COUNT(*) FROM embeddings;"

# Check Docker containers
docker ps
docker logs <container_name>
```

## 🚀 Performance Expectations

Based on test runs:

### Dataset Throughput (chunks/second)
- **CC News**: 16,000 - 48,000 (high volume, parquet files)
- **Arxiv**: 100 - 200 (moderate volume, JSONL.gz)
- **Wikipedia**: Variable (depends on data source availability)

### Chunk Size Impact
- **Smaller chunks** (0.5-2KB): Higher throughput, more overhead
- **Medium chunks** (5-20KB): Balanced performance
- **Large chunks** (40-80KB): Lower throughput, better batching

### Burst vs Regular
- **Regular streaming**: Consistent latency, predictable performance
- **Burst streaming**: Higher peak throughput, variable latency

### Maximum Scale Testing
For the most comprehensive evaluation, use all combinations:
```bash
# 216 total experiment combinations (3 datasets × 9 chunks × 8 bursts)
# Estimated runtime: 4-6 hours
# 200 chunks per test, 10-minute timeout per test
python run_multi_dataset_experiments.py \
  --architecture architecture3 \
  --model "sentence-transformers/all-MiniLM-L6-v2" \
  --datasets cc_news arxiv wikipedia \
  --chunk-sizes 0.5 1 2 4 8 16 32 64 80 \
  --burst-durations 1 2 5 10 15 30 45 60 \
  --max-chunks 200 \
  --timeout 600
```

## 🎯 Integration with Pipeline

The experiments integrate with the broader real-time LLM ingestion architecture:

```
Dataset APIs → run_multi_dataset_experiments.py → Kafka → Embedding Service → Vector DB
     ↓                        ↓                     ↓           ↓              ↓
   CC News              Text Chunks          text-messages  Embeddings    embeddings
   Arxiv                Token-based            Topic        Generation      Table
   Wikipedia            Chunking                            Service
```

This provides end-to-end performance measurement of the complete ingestion pipeline under various load conditions and data characteristics.

## 🤝 Related Components

- **Dataset APIs**: `datasets/*/` - Individual dataset streaming implementations  
- **Embedding Service**: `cqrs_embedding_gen_svc/` - CQRS-based embedding processor
- **Vector Storage**: `lancedb/` and `pgvector/` - Vector database adapters
- **Message Queue**: `kafka/` - Kafka infrastructure and tools
- **Architecture Examples**: `architecture*/` - Complete pipeline demonstrations