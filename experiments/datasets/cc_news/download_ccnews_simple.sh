#!/bin/bash
# Download CC News dataset from HuggingFace
# Similar to the Wikipedia download script pattern

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

# Download CC News dataset using Python
echo "Downloading CC News dataset..."
python3 -c "
from huggingface_hub import snapshot_download
import os

print('Downloading CC News dataset from HuggingFace...')
try:
    snapshot_download(
        repo_id='sentence-transformers/ccnews',
        local_dir='./ccnews_data',
        repo_type='dataset'
    )
    print('✅ Download complete!')
    print('📁 Dataset saved to: ./ccnews_data/')
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
"

echo "Listing downloaded files..."
ls -la ./ccnews_data/