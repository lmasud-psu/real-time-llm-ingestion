#!/bin/bash
# Download Arxiv Abstracts 2021 dataset from HuggingFace
# Similar to the CC News download script pattern

# Set HuggingFace token if needed (optional for public datasets)
# export HF_TOKEN=your_token_here

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Setting up environment..."
source venv/bin/activate
pip install huggingface_hub

# Download Arxiv dataset using Python
echo "Downloading Arxiv Abstracts 2021 dataset..."
python3 -c "
from huggingface_hub import snapshot_download
import os

print('Downloading Arxiv Abstracts 2021 dataset from HuggingFace...')
try:
    snapshot_download(
        repo_id='gfissore/arxiv-abstracts-2021',
        local_dir='./arxiv_data',
        repo_type='dataset'
    )
    print('✅ Download complete!')
    print('📁 Dataset saved to: ./arxiv_data/')
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
"

echo "Listing downloaded files..."
ls -la ./arxiv_data/