# Quick Reference: Multi-Dataset Ingestion Experiments

## 🚀 Getting Started (30 seconds)

```bash
cd /home/latif/doctoral/real-time-llm-ingestion/experiments

# 1. Setup environment
./run_experiments.sh setup

# 2. Test datasets (no infrastructure required)
./run_experiments.sh test

# 3. Start infrastructure and run smoke test
# Start Kafka: docker-compose up -d (from kafka/)
# Start PostgreSQL: docker-compose up -d (from pgvector/) 
# Start embedding service: docker-compose up -d (from cqrs_embedding_gen_svc/)
./run_experiments.sh smoke

# 4. Run quick experiment
./run_experiments.sh quick
```

## 📋 Experiment Commands

| Command | Duration | Description |
|---------|----------|-------------|
| `./run_experiments.sh test` | 30s | Test dataset streaming (no Kafka/DB) |
| `./run_experiments.sh smoke` | 1min | Test full infrastructure |
| `./run_experiments.sh quick` | 5min | Quick performance test |
| `./run_experiments.sh performance` | 20min | Medium-scale performance test |
| `./run_experiments.sh burst` | 15min | Burst pattern testing |
| `./run_experiments.sh comprehensive` | 1-2hrs | Full experiment suite |

## 🎯 Custom Experiments

```bash
# Test specific dataset and chunk sizes  
python run_multi_dataset_experiments.py \
  --architecture "architecture1" \
  --model "sentence-transformers/all-MiniLM-L6-v2" \
  --datasets cc_news arxiv \
  --chunk-sizes 1 5 10 \
  --max-chunks 20 \
  --no-burst

# Burst testing with custom parameters  
python run_multi_dataset_experiments.py \
  --architecture "architecture2" \
  --model "text-embedding-ada-002" \
  --datasets wikipedia \
  --chunk-sizes 2 8 \
  --burst-durations 30 60 \
  --burst-interval 5 \
  --max-chunks 25

# Smoke test only
python run_multi_dataset_experiments.py \
  --architecture "test_arch" \
  --model "test_model" \
  --smoke-test
```

## 📊 Available Datasets

| Dataset | Throughput | Description |
|---------|------------|-------------|
| `cc_news` | ~16k-48k chunks/s | News articles from CC-News corpus |
| `arxiv` | ~100-200 chunks/s | Academic paper abstracts |  
| `wikipedia` | Variable | Wikipedia articles (with mock fallback) |

## 🔧 Chunk Sizes

- **0.5KB** → 128 tokens (high throughput, more overhead)
- **1KB** → 256 tokens  
- **2KB** → 512 tokens
- **5KB** → 1,280 tokens (balanced performance)
- **10KB** → 2,560 tokens
- **20KB** → 5,120 tokens
- **40KB** → 10,240 tokens  
- **80KB** → 20,480 tokens (lower throughput, better batching)

## 📈 Results

Results are saved as CSV files in `experiment_results/`:

**Summary CSV Format (user-requested):**
| Architecture | Model | Dataset | Chunk | Burst_Length | Result_ms |
|--------------|-------|---------|-------|--------------|-----------|
| architecture1 | all-MiniLM-L6-v2 | cc_news | 1.0 | | 45.2 |
| architecture1 | all-MiniLM-L6-v2 | cc_news | 2.0 | 30 | 52.8 |

**Files Generated:**
- `*_summary.csv`: Primary format with Architecture, Model, Dataset, Chunk, Burst_Length, Result_ms  
- `*_detailed.csv`: Full metrics including throughput, success rates, token counts, etc.
- `smoke_test_results_*.csv`: Quick validation results

Key metrics: `result_ms` (avg latency), `throughput_chunks_per_s`, `success_rate`

## 🔍 Troubleshooting

```bash
# Check infrastructure
./run_experiments.sh test        # Test datasets only
docker ps                        # Check running services
nc -z localhost 9092             # Test Kafka
nc -z localhost 5432             # Test PostgreSQL

# Debug failed experiments
python test_experiment_setup.py  # Detailed infrastructure test
tail -f experiment_results/*.csv # Watch results in real-time
```

## 🏗️ Infrastructure Stack

```
Datasets → Kafka → Embedding Service → Vector Database
(Stream)   (Queue)     (Process)         (Store)
   ↓          ↓           ↓                ↓
CC News    text-        CQRS             pgvector
Arxiv      messages     Embedding        embeddings
Wikipedia              Generator         table
```

## 🎛️ Environment Variables

```bash
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export KAFKA_INPUT_TOPIC="text-messages"  
export KAFKA_OUTPUT_TOPIC="embeddings"
export DATABASE_HOST="localhost"
export DATABASE_NAME="embeddings_db"
export DATABASE_USER="postgres" 
export DATABASE_PASSWORD="postgres"
export EMBEDDINGS_TABLE="embeddings"
```

## 📚 Full Documentation

See `EXPERIMENT_README.md` for complete documentation, configuration options, and analysis examples.