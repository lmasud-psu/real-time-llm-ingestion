# Architecture3 Multi-Dataset Experiments

This directory contains the multi-dataset ingestion experiment tools that were moved from `experiments/` to be architecture-specific.

## Files Moved Here
- `run_multi_dataset_experiments.py` - Main multi-dataset experiment runner
- `run_experiments.sh` - Helper script with predefined experiment configurations
- `test_experiment_setup.py` - Dataset import validation script
- `experiment_venv/` - Python virtual environment for experiments
- `EXPERIMENT_README.md` - Detailed experiment documentation
- `requirements.txt` - Python dependencies

## Configuration
This experiment setup is configured for Architecture3 with:
- **Database**: PostgreSQL on localhost:5434, database `realtime_llm`
- **Table**: `text_embeddings` (CQRS-style table name)
- **Embedding Service**: CQRS-based embedding processor (`cqrs_embedding_gen_svc`)
- **Default Architecture**: `architecture3` in all interactive prompts

## Quick Start
```bash
cd /home/latif/doctoral/real-time-llm-ingestion/architecture3

# Setup virtual environment
source experiment_venv/bin/activate  # or create: python3 -m venv experiment_venv
pip install -r requirements.txt

# Test setup
python test_experiment_setup.py

# Run quick test
./run_experiments.sh quick

# Run full experiment suite
./run_experiments.sh comprehensive
```

## Dataset Access
The experiments access datasets from the shared `../experiments/datasets/` directory, so the dataset files remain in their original location.

For detailed documentation, see `EXPERIMENT_README.md`.