# Arxiv Abstracts 2021 Dataset

This directory contains tools to download and stream the Arxiv Abstracts 2021 dataset from HuggingFace.

## Quick Start

1. Download the dataset:
```bash
./download_arxiv_simple.sh
```

2. Stream the dataset:
```python
from stream_arxiv import stream_arxiv

for chunk in stream_arxiv(token_length=1000):
    process_text(chunk)
```

## Dataset Details

- **Source**: [gfissore/arxiv-abstracts-2021](https://huggingface.co/datasets/gfissore/arxiv-abstracts-2021)
- **Format**: Compressed JSONL (JSON Lines) file
- **Size**: ~940MB compressed, ~2M papers
- **Content**: Academic paper metadata including titles and abstracts from arXiv through 2021
- **Fields**: id, submitter, authors, title, comments, journal-ref, doi, abstract, report-no, categories, versions

## Downloaded Files

After running the script, you'll have:
```
arxiv_data/
├── arxiv-abstracts.jsonl.gz    # Main dataset file (~940MB)
├── README.md                   # Dataset documentation
└── .gitattributes             # Git LFS attributes
```

## Streaming API

### Basic Usage

```python
from stream_arxiv import stream_arxiv

# Stream with default 1000 token chunks
for chunk in stream_arxiv():
    process_text(chunk)

# Stream with custom chunk size  
for chunk in stream_arxiv(token_length=500):
    process_smaller_chunk(chunk)
```

### Category Filtering

```python
from stream_arxiv import stream_arxiv_categories

# Stream only computer science papers
cs_categories = ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV']
for chunk in stream_arxiv_categories(token_length=800, categories=cs_categories):
    process_cs_paper(chunk)

# Stream physics papers
physics_categories = ['hep-ph', 'hep-th', 'astro-ph', 'cond-mat']
for chunk in stream_arxiv_categories(token_length=1000, categories=physics_categories):
    process_physics_paper(chunk)
```

### Sample Streaming

```python
from stream_arxiv import stream_arxiv_sample

# Stream a sample for testing (faster)
for chunk in stream_arxiv_sample(token_length=600, max_papers=1000):
    test_processing(chunk)
```

## Files

- `download_arxiv_simple.sh` - Downloads the dataset from HuggingFace
- `stream_arxiv.py` - Main streaming API with multiple functions
- `example_usage.py` - Usage examples and patterns
- `test_api.py` - API validation tests
- `requirements.txt` - Python dependencies for streaming
- `README.md` - This documentation

## Features

- **Memory efficient**: Streams large dataset without loading into memory
- **Token-based chunking**: Splits text based on estimated token count
- **Category filtering**: Process specific academic domains
- **Text cleaning**: Removes LaTeX artifacts and normalizes formatting
- **Progress tracking**: Shows processing status for long operations
- **Flexible APIs**: Multiple streaming functions for different use cases

## Academic Categories

Common category examples:
- **Computer Science**: cs.AI, cs.LG, cs.CL, cs.CV, cs.NE, cs.IR
- **Physics**: hep-ph, hep-th, astro-ph, cond-mat, quant-ph, nucl-th  
- **Mathematics**: math.AG, math.NT, math.CO, math.PR
- **Statistics**: stat.ML, stat.ME, stat.TH

## Dependencies

Install streaming dependencies:
```bash
pip install -r requirements.txt
```

Or use the virtual environment created by the download script:
```bash
source venv/bin/activate
```

## Usage Examples

Run the example scripts:
```bash
python3 example_usage.py    # Comprehensive examples
python3 test_api.py         # API validation tests
python3 stream_arxiv.py     # Basic functionality test
```

## Performance Notes

- The full dataset contains ~2 million papers
- Use `stream_arxiv_sample()` for testing and development
- Category filtering can significantly reduce processing time
- Progress indicators show every 10k papers for full streaming