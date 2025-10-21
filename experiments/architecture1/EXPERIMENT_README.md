# Architecture 1 Experiment Framework

This directory contains the experiment framework for Architecture 1, which implements a Kafka-based pipeline for real-time text ingestion and embedding generation.

## Architecture Overview

Architecture 1 implements a traditional streaming pipeline:

```
Data Sources → Kafka (text-messages) → Embedding Service → Kafka (embeddings) → Writer Service → PostgreSQL
```

### Pipeline Flow

1. **Text Ingestion**: Raw text data is streamed to the `text-messages` Kafka topic
2. **Embedding Generation**: The embedding service consumes from `text-messages`, generates embeddings, and produces to `embeddings` topic
3. **Persistence**: The writer service consumes from `embeddings` topic and persists to PostgreSQL database

### Key Differences from Architecture 3

- **Pipeline vs CQRS**: Uses traditional streaming pipeline instead of CQRS command handling
- **Kafka Topics**: Uses separate input (`text-messages`) and output (`embeddings`) topics
- **Database Schema**: Uses `embeddings` table with `id` field (not `text_message_id`)
- **Port Configuration**: PostgreSQL runs on port 5432 (standard)

## Quick Start

### 1. Setup Environment

```bash
# Create and setup virtual environment
./run_experiments.sh setup

# Start infrastructure (from architecture1 directory)
cd ../../architecture1
docker-compose up -d
```

### 2. Test Setup

```bash
# Test dataset streaming (no infrastructure needed)
./run_experiments.sh test

# Test full pipeline (requires Kafka + DB + services)
./run_experiments.sh smoke
```

### 3. Run Experiments

```bash
# Quick demonstration (5-10 minutes)
./run_experiments.sh quick

# Performance benchmarks (30-45 minutes)
./run_experiments.sh performance

# Complete example with all datasets
./run_experiments.sh example
```

## Experiment Configuration

### Datasets Supported

- **cc_news**: Common Crawl news articles (high volume)
- **arxiv**: Academic paper abstracts (medium volume)
- **wikipedia**: Wikipedia article excerpts (variable volume)

### Chunk Sizes

Configure text chunking in KB (converted to ~256 tokens per KB):
- `0.5KB` → ~128 tokens
- `1KB` → ~256 tokens  
- `2KB` → ~512 tokens
- `5KB` → ~1280 tokens
- `8KB` → ~2048 tokens
- `10KB` → ~2560 tokens
- `20KB` → ~5120 tokens
- `40KB` → ~10240 tokens
- `80KB` → ~20480 tokens

### Burst Patterns

Test system behavior under different load patterns:
- **Steady Rate**: Consistent message flow with small delays
- **Burst**: Rapid message bursts (5s, 15s, 30s, 45s, 60s) followed by pauses

## Command Reference

### Basic Commands

```bash
./run_experiments.sh setup         # Setup virtual environment
./run_experiments.sh test          # Test dataset streaming
./run_experiments.sh smoke         # Smoke test (minimal validation)
./run_experiments.sh quick         # Quick experiment (2 datasets, 3 sizes)
./run_experiments.sh performance   # Performance test (all datasets, 5 sizes)
./run_experiments.sh comprehensive # Full test suite (8 sizes, 5 burst patterns)
./run_experiments.sh example       # Complete demonstration
```

### Advanced Usage

```bash
# Custom experiment
./run_multi_dataset_experiments.py \
    --architecture architecture1 \
    --model "TinyLlama/TinyLlama-1.1B-Chat-v1.0" \
    --datasets cc_news arxiv \
    --chunk-sizes 1 2 5 10 20 \
    --burst-durations 30 \
    --max-chunks 50 \
    --timeout 300

# Most comprehensive test (all datasets, chunks, bursts)
./run_multi_dataset_experiments.py \
    --architecture architecture1 \
    --model "TinyLlama/TinyLlama-1.1B-Chat-v1.0" \
    --datasets cc_news arxiv wikipedia \
    --chunk-sizes 0.5 1 2 4 8 16 32 64 80 \
    --burst-durations 1 2 5 10 15 30 45 60 \
    --max-chunks 200 \
    --timeout 600

# Smoke test only
./run_multi_dataset_experiments.py --smoke-test

# Burst pattern focus
./run_experiments.sh burst
```

## Environment Configuration

### Required Services

1. **Kafka** (localhost:9092)
   - Topics: `text-messages`, `embeddings`
   - Start: `cd ../../architecture1 && docker-compose up -d`

2. **PostgreSQL** (localhost:5432)
   - Database: `embeddings_db`
   - Table: `embeddings` with `id` field
   - Start: Included in architecture1 docker-compose

3. **Embedding Service**
   - Consumes: `text-messages` topic
   - Produces: `embeddings` topic
   - Start: Included in architecture1 docker-compose

4. **Writer Service**
   - Consumes: `embeddings` topic
   - Persists: PostgreSQL `embeddings` table
   - Start: Included in architecture1 docker-compose

### Environment Variables

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_INPUT_TOPIC=text-messages
KAFKA_OUTPUT_TOPIC=embeddings

# Database Configuration  
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=embeddings_db
DATABASE_USER=postgres
DATABASE_PASSWORD=password
DATABASE_TABLE=embeddings
```

## Results and Metrics

### Measurement Points

Architecture 1 measures latency across the full pipeline:

1. **Text Ingestion**: Time to publish to `text-messages` topic
2. **Embedding Generation**: Time for embedding service to process and publish to `embeddings` topic
3. **Database Persistence**: Time for writer service to persist to PostgreSQL

### Output Files

Results are saved in `experiment_results/` directory:

- `experiment_results_YYYYMMDD_HHMMSS.csv`: Detailed per-experiment results
- `experiment_results_YYYYMMDD_HHMMSS_summary.csv`: Aggregated statistics by dataset
- `smoke_test_results_YYYYMMDD_HHMMSS.csv`: Smoke test validation results

### Key Metrics

- **Throughput**: Chunks/second and tokens/second
- **Latency**: End-to-end milliseconds per chunk
- **Success Rate**: Percentage of messages successfully persisted
- **Pipeline Health**: Individual stage monitoring (Kafka → DB)

## Troubleshooting

### Common Issues

1. **"Connection failed"**
   - Check Kafka is running: `nc -z localhost 9092`
   - Check PostgreSQL is running: `nc -z localhost 5432`
   - Verify services: `docker-compose ps`

2. **"Dataset module import failed"**
   - Run: `./run_experiments.sh setup`
   - Check virtual environment: `ls experiment_venv/`

3. **"No chunks generated"**
   - Check dataset files in `../datasets/`
   - Verify dataset streaming: `./run_experiments.sh test`

4. **"Timeout waiting for embeddings"**
   - Check embedding service logs: `docker-compose logs embedding-service`
   - Verify topic creation: Check Kafka UI or logs

5. **"Database persistence failed"**
   - Check writer service logs: `docker-compose logs writer-service`
   - Verify database schema and permissions

### Debug Commands

```bash
# Check infrastructure
./run_experiments.sh test

# Test with minimal data
./run_multi_dataset_experiments.py \
    --smoke-test \
    --max-chunks 3 \
    --timeout 60

# Check service logs
cd ../../architecture1
docker-compose logs embedding-service
docker-compose logs writer-service
docker-compose logs postgres
```

## Performance Optimization

### Recommended Configurations

**Development/Testing:**
```bash
./run_experiments.sh quick
# - 2 datasets, 3 chunk sizes
# - 10 chunks max per test
# - ~5-10 minutes total
```

**Performance Benchmarking:**
```bash
./run_experiments.sh performance  
# - All datasets, 5 chunk sizes (1KB, 2KB, 5KB, 10KB, 20KB)
# - Burst duration: 30s with 5s interval
# - 30 chunks max per test
# - ~30-45 minutes total
```

**Comprehensive Analysis:**
```bash
./run_experiments.sh comprehensive
# - All datasets, 8 chunk sizes (0.5KB to 80KB)
# - Burst durations: 30s, 60s with 5s interval
# - 50 chunks max per test  
# - 1-2 hours total
```

**Maximum Scale Testing:**
```bash
# Most comprehensive test possible
./run_multi_dataset_experiments.py \
    --architecture architecture1 \
    --model "TinyLlama/TinyLlama-1.1B-Chat-v1.0" \
    --datasets cc_news arxiv wikipedia \
    --chunk-sizes 0.5 1 2 4 8 16 32 64 80 \
    --burst-durations 1 2 5 10 15 30 45 60 \
    --max-chunks 200 \
    --timeout 600
# - All 3 datasets, 9 chunk sizes, 8 burst patterns
# - 216 total experiment combinations
# - 200 chunks max per test
# - 4-6 hours total runtime
```

### Scaling Considerations

- **Chunk Size**: Larger chunks reduce message count but increase processing time
- **Burst Patterns**: Test system resilience under load spikes
- **Timeout Values**: Adjust based on expected embedding generation time
- **Max Chunks**: Balance between statistical significance and execution time

## Integration with Other Architectures

This framework uses the same API and output format as Architecture 3, enabling:

- **Comparative Analysis**: Direct performance comparison between architectures
- **Dataset Compatibility**: Same streaming modules and chunk generation
- **Result Format**: Compatible CSV outputs for cross-architecture analysis
- **Metric Standards**: Consistent measurement methodology

## Development

### Adding New Datasets

1. Create streaming module in `../datasets/new_dataset/`
2. Add import to `run_multi_dataset_experiments.py`
3. Add dataset choice to argument parser
4. Test with `./run_experiments.sh test`

### Custom Metrics

Extend `ExperimentResult` dataclass in `run_multi_dataset_experiments.py` to add:
- Custom latency measurements
- Pipeline stage breakdowns
- Resource utilization metrics
- Error categorization

### Architecture Variants

To create Architecture 1 variants:
1. Copy this directory structure
2. Modify connection parameters (topics, database schema)
3. Update pipeline monitoring logic
4. Adjust documentation references

---

**Next Steps:**
1. Run `./run_experiments.sh setup` to initialize environment
2. Start Architecture 1 services: `cd ../../architecture1 && docker-compose up -d`
3. Verify setup: `./run_experiments.sh smoke`
4. Begin experiments: `./run_experiments.sh example`