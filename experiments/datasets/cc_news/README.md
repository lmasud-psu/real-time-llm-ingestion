# CC News Dataset

This directory contains tools to download the CC News dataset from HuggingFace.

## Quick Start

Run the download script:
```bash
./download_ccnews_simple.sh
```

## Dataset Details

- **Source**: [sentence-transformers/ccnews](https://huggingface.co/datasets/sentence-transformers/ccnews)
- **Format**: Parquet files
- **Size**: ~960MB (4 parquet files of ~240MB each)
- **Content**: News articles for training sentence transformers

## Downloaded Files

After running the script, you'll have:
```
ccnews_data/
├── pair/
│   ├── train-00000-of-00004.parquet
│   ├── train-00001-of-00004.parquet
│   ├── train-00002-of-00004.parquet
│   └── train-00003-of-00004.parquet
├── README.md
└── .gitattributes
```

## Usage in Experiments

### Streaming API

Use the streaming interface for memory-efficient processing:

```python
from stream_ccnews import stream_cc_news

# Stream with default 1000 token chunks
for chunk in stream_cc_news(token_length=1000):
    # Process each chunk
    print(f"Processing chunk: {chunk[:100]}...")
    
# Stream with custom chunk size
for chunk in stream_cc_news(token_length=500):
    # Smaller chunks for different use cases
    process_text_chunk(chunk)
```

### Direct Pandas Usage

The downloaded parquet files can also be used with pandas:

```python
import pandas as pd

# Read a single parquet file
df = pd.read_parquet('ccnews_data/pair/train-00000-of-00004.parquet')

# Or read all files at once
df_all = pd.read_parquet('ccnews_data/pair/')
```

### Example Scripts

- `stream_ccnews.py` - Main streaming module with `stream_cc_news()` function
- `example_usage.py` - Demonstrates various streaming patterns
- Run examples: `python3 example_usage.py`

## Files

- `download_ccnews_simple.sh` - Downloads the dataset from HuggingFace
- `stream_ccnews.py` - Streaming API for processing chunks
- `example_usage.py` - Usage examples and patterns
- `requirements.txt` - Python dependencies for streaming
- `README.md` - This documentation

## Dependencies

Install streaming dependencies:
```bash
pip install -r requirements.txt
```

Or use the virtual environment created by the download script:
```bash
source venv/bin/activate
```