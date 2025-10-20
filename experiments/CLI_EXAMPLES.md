# Multi-Dataset Experiment CLI Examples

This document provides comprehensive CLI examples for running multi-dataset ingestion experiments with various chunk sizes and burst patterns.

## Quick Start

```bash
# Setup environment
./run_experiments.sh setup

# Test infrastructure
./run_experiments.sh test

# Run complete example (recommended first run)
./run_experiments.sh example
```

## Complete CLI Examples

### 1. Single Dataset Testing

Test one dataset with multiple chunk sizes:

```bash
python3 run_multi_dataset_experiments.py \
  --architecture "architecture3" \
  --model "sentence-transformers/all-MiniLM-L6-v2" \
  --datasets cc_news \
  --chunk-sizes 1 5 10 20 40
```

### 2. All Datasets with Burst Patterns

Test all three datasets with burst patterns:

```bash
python3 run_multi_dataset_experiments.py \
  --architecture "architecture3" \
  --model "sentence-transformers/all-MiniLM-L6-v2" \
  --datasets cc_news arxiv wikipedia \
  --chunk-sizes 2 8 15 30 \
  --burst-durations 10 30 60 \
  --burst-interval 5 \
  --max-chunks 50
```

### 3. Performance Testing - All Combinations

Comprehensive performance testing:

```bash
python3 run_multi_dataset_experiments.py \
  --architecture "architecture3" \
  --model "sentence-transformers/all-MiniLM-L6-v2" \
  --datasets cc_news arxiv wikipedia \
  --chunk-sizes 0.5 1 2 5 10 20 40 80 \
  --burst-durations 1 5 10 15 30 45 60 \
  --burst-interval 2 \
  --max-chunks 100 \
  --timeout 300
```

### 4. Quick Smoke Test

Minimal validation test:

```bash
python3 run_multi_dataset_experiments.py \
  --architecture "test_architecture" \
  --model "test_model" \
  --smoke-test
```

### 5. Large Scale Comprehensive Testing

Maximum coverage testing (1-2 hours):

```bash
python3 run_multi_dataset_experiments.py \
  --architecture "architecture3" \
  --model "sentence-transformers/all-MiniLM-L6-v2" \
  --datasets cc_news arxiv wikipedia \
  --chunk-sizes 0.5 1 2 4 8 16 32 64 80 \
  --burst-durations 1 2 5 10 15 30 45 60 \
  --burst-interval 3 \
  --max-chunks 200 \
  --timeout 600
```

## Helper Script Commands

### Quick Commands

```bash
# Quick 5-minute test
./run_experiments.sh quick

# Performance test (20 minutes)
./run_experiments.sh performance

# Full comprehensive suite (1-2 hours)
./run_experiments.sh comprehensive

# Burst pattern testing only
./run_experiments.sh burst

# Complete example with all datasets/chunks/bursts (30-45 minutes)
./run_experiments.sh example
```

## Parameter Reference

| Parameter | Description | Examples |
|-----------|-------------|----------|
| `--architecture` | Target architecture | `architecture1`, `architecture2`, `architecture3` |
| `--model` | Embedding model name | `sentence-transformers/all-MiniLM-L6-v2` |
| `--datasets` | Space-separated dataset list | `cc_news arxiv wikipedia` |
| `--chunk-sizes` | Chunk sizes in KB | `0.5 1 2 5 10 20 40 80` |
| `--burst-durations` | Burst duration in seconds | `1 5 10 15 30 45 60` |
| `--burst-interval` | Seconds between bursts | `1 2 3 5 10` |
| `--max-chunks` | Maximum chunks per test | `10 50 100 200 1000` |
| `--timeout` | Per-test timeout in seconds | `60 120 300 600` |
| `--smoke-test` | Run minimal validation | (flag, no value) |

## Dataset Information

| Dataset | Format | Description | Typical Size |
|---------|--------|-------------|--------------|
| `cc_news` | Parquet | Common Crawl News articles | ~1MB chunks |
| `arxiv` | JSONL.GZ | Academic paper abstracts | ~500KB chunks |
| `wikipedia` | Arrow/Mock | Wikipedia article content | ~2MB chunks |

## Output Files

Each experiment generates two CSV files:

### Summary CSV Format
```
Architecture,Model,Dataset,Chunk,Burst_Length,Result_ms
architecture3,sentence-transformers/all-MiniLM-L6-v2,cc_news,1,10,1250
architecture3,sentence-transformers/all-MiniLM-L6-v2,arxiv,1,10,1180
```

### Detailed CSV Format
Includes additional metrics:
- Throughput (chunks/second)
- Success rate (%)
- Average processing time
- Error counts
- Memory usage

## Common Use Cases

### Development Testing
```bash
# Quick validation
./run_experiments.sh smoke

# Small scale testing
python3 run_multi_dataset_experiments.py \
  --architecture "architecture3" \
  --model "sentence-transformers/all-MiniLM-L6-v2" \
  --datasets cc_news \
  --chunk-sizes 1 5 \
  --max-chunks 10
```

### Performance Benchmarking
```bash
# Medium scale benchmark
python3 run_multi_dataset_experiments.py \
  --architecture "architecture3" \
  --model "sentence-transformers/all-MiniLM-L6-v2" \
  --datasets cc_news arxiv wikipedia \
  --chunk-sizes 1 5 10 20 \
  --burst-durations 10 30 \
  --max-chunks 50
```

### Research Experiments
```bash
# Large scale research
python3 run_multi_dataset_experiments.py \
  --architecture "architecture3" \
  --model "sentence-transformers/all-MiniLM-L6-v2" \
  --datasets cc_news arxiv wikipedia \
  --chunk-sizes 0.5 1 2 4 8 16 32 64 80 \
  --burst-durations 1 2 5 10 15 30 45 60 \
  --burst-interval 3 \
  --max-chunks 200 \
  --timeout 600
```

## Environment Setup

### Prerequisites
- Python 3.8+
- Docker and Docker Compose
- PostgreSQL with pgvector
- Apache Kafka

### Infrastructure Commands
```bash
# Start PostgreSQL
cd ../pgvector && docker-compose up -d

# Start Kafka  
cd ../kafka && docker-compose up -d

# Start specific architecture
cd ../architecture3 && docker-compose up -d
```

### Environment Variables
```bash
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export DATABASE_HOST="localhost" 
export DATABASE_PORT="5432"  # or 5434 for architecture3
```

## Troubleshooting

### Common Issues

1. **Infrastructure not running**
   ```bash
   ./run_experiments.sh test  # Check infrastructure
   ```

2. **Database connection errors**
   - Check if PostgreSQL is running: `nc -z localhost 5432`
   - For architecture3, use port 5434: `nc -z localhost 5434`

3. **Kafka connection errors**
   - Check if Kafka is running: `nc -z localhost 9092`
   - Restart Kafka: `cd ../kafka && docker-compose restart`

4. **Dataset streaming errors**
   ```bash
   python3 test_experiment_setup.py  # Test datasets only
   ```

### Performance Tips

1. **Reduce timeouts for faster testing**
   ```bash
   --timeout 60  # For quick tests
   ```

2. **Limit chunk count for development**
   ```bash
   --max-chunks 10  # Small tests
   ```

3. **Use smoke test for validation**
   ```bash
   --smoke-test  # Minimal validation
   ```

## Example Workflows

### Daily Development Workflow
```bash
# 1. Validate setup
./run_experiments.sh test

# 2. Quick smoke test
./run_experiments.sh smoke

# 3. Small development test
python3 run_multi_dataset_experiments.py \
  --architecture "architecture3" \
  --model "sentence-transformers/all-MiniLM-L6-v2" \
  --datasets cc_news \
  --chunk-sizes 1 5 \
  --max-chunks 5
```

### Weekly Performance Testing
```bash
# Run comprehensive performance suite
./run_experiments.sh performance
```

### Research Data Collection
```bash
# Full comprehensive testing
./run_experiments.sh comprehensive

# Or custom large-scale testing
./run_experiments.sh example
```