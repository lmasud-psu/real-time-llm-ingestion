#!/bin/bash
# Download Wikipedia dataset from Wikimedia HuggingFace
# Similar to the CC News and Arxiv download script pattern

# Set HuggingFace token if needed (optional for public datasets)
# export HF_TOKEN=your_token_here

# Configuration - you can modify these
LANGUAGE=${1:-"en"}  # Default to English, can pass language as first argument
DATE=${2:-"20231101"}  # Default to latest available date, can pass date as second argument

echo "📖 Downloading Wikipedia dataset for language: ${LANGUAGE}, date: ${DATE}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Setting up environment..."
source venv/bin/activate
pip install huggingface_hub

# Download Wikipedia dataset using Python
echo "Downloading Wikipedia dataset..."
pip install datasets pyarrow

python3 -c "
import os
import tempfile
from datasets import load_dataset

language = '${LANGUAGE}'
date = '${DATE}'
subset_name = f'{date}.{language}'

print(f'Downloading Wikipedia dataset subset: {subset_name}')

# Set custom cache directory to avoid permission issues
cache_dir = os.path.join(os.getcwd(), '.cache')
os.makedirs(cache_dir, exist_ok=True)
os.environ['HF_HOME'] = cache_dir

try:
    # Load the dataset subset with custom cache
    dataset = load_dataset(
        'wikimedia/wikipedia', 
        subset_name, 
        split='train',
        cache_dir=cache_dir
    )
    
    # Save to local directory
    os.makedirs('./wikipedia_data', exist_ok=True)
    dataset.save_to_disk(f'./wikipedia_data/{subset_name}')
    
    print('✅ Download complete!')
    print(f'📁 Dataset saved to: ./wikipedia_data/{subset_name}/')
    print(f'🏷️  Language: {language}')
    print(f'📅 Date: {date}')
    print(f'📊 Total articles: {len(dataset):,}')
    
    # Show sample
    if len(dataset) > 0:
        sample = dataset[0]
        print(f'\\n📄 Sample article:')
        print(f'   Title: {sample[\"title\"]}')
        print(f'   Text length: {len(sample[\"text\"])} chars')
        print(f'   URL: {sample[\"url\"]}')
        
except Exception as e:
    print(f'❌ Error: {e}')
    print(f'💡 Make sure the language code \"{language}\" and date \"{date}\" are valid.')
    print('   Available languages: en, es, fr, de, zh, ja, ar, etc.')
    print('   Available dates: 20231101, 20220301, etc.')
    print('   Check: https://huggingface.co/datasets/wikimedia/wikipedia')
    exit(1)
"

echo "Listing downloaded files..."
ls -la ./wikipedia_data/