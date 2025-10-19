#!/usr/bin/env python3
"""
Demo script showing the exact CSV output format from experiments.
Creates sample CSV data to demonstrate the expected structure.
"""

import csv
import sys
from pathlib import Path

def create_demo_csv():
    """Create a demo CSV file showing the exact format."""
    
    # Sample data matching the requested format
    demo_data = [
        ["Architecture", "Model", "Dataset", "Chunk", "Burst_Length", "Result_ms"],
        ["architecture1", "sentence-transformers/all-MiniLM-L6-v2", "cc_news", 1.0, "", 45.2],
        ["architecture1", "sentence-transformers/all-MiniLM-L6-v2", "cc_news", 2.0, 30, 52.8],
        ["architecture1", "sentence-transformers/all-MiniLM-L6-v2", "cc_news", 5.0, "", 38.1],
        ["architecture1", "sentence-transformers/all-MiniLM-L6-v2", "cc_news", 10.0, 60, 41.7],
        ["architecture1", "sentence-transformers/all-MiniLM-L6-v2", "arxiv", 1.0, "", 62.4],
        ["architecture1", "sentence-transformers/all-MiniLM-L6-v2", "arxiv", 2.0, 30, 58.9],
        ["architecture1", "sentence-transformers/all-MiniLM-L6-v2", "arxiv", 5.0, "", 55.2],
        ["architecture1", "sentence-transformers/all-MiniLM-L6-v2", "wikipedia", 1.0, "", 35.8],
        ["architecture1", "sentence-transformers/all-MiniLM-L6-v2", "wikipedia", 2.0, 30, 33.1],
        ["architecture1", "sentence-transformers/all-MiniLM-L6-v2", "wikipedia", 5.0, "", 29.6],
        ["architecture2", "text-embedding-ada-002", "cc_news", 1.0, "", 42.1],
        ["architecture2", "text-embedding-ada-002", "cc_news", 2.0, 30, 39.5],
        ["architecture2", "text-embedding-ada-002", "arxiv", 1.0, "", 58.7],
        ["architecture2", "text-embedding-ada-002", "wikipedia", 1.0, "", 32.4],
    ]
    
    output_file = "demo_experiment_results.csv"
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(demo_data)
    
    print(f"📄 Demo CSV created: {output_file}")
    return output_file

def show_csv_format():
    """Show the CSV format and explain each column."""
    
    print("📋 Experiment CSV Format")
    print("=" * 50)
    
    format_info = [
        ("Architecture", "The architecture being tested (user input)", "architecture1, architecture2, etc."),
        ("Model", "The embedding model being used (user input)", "sentence-transformers/all-MiniLM-L6-v2"),
        ("Dataset", "Which dataset is being streamed", "cc_news, arxiv, wikipedia"),
        ("Chunk", "Chunk size in kilobytes", "0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 80.0"),
        ("Burst_Length", "Burst duration in seconds (empty if no burst)", "30, 60 (or empty for regular streaming)"),
        ("Result_ms", "Average latency in milliseconds (primary metric)", "45.2, 52.8, etc.")
    ]
    
    for column, description, examples in format_info:
        print(f"\n{column}:")
        print(f"  Description: {description}")
        print(f"  Examples: {examples}")
    
    print(f"\n💡 Key Points:")
    print("• Architecture and Model are required inputs for all experiments")
    print("• Burst_Length is empty for non-burst experiments") 
    print("• Result_ms is the primary performance metric (average latency)")
    print("• Each row represents one experiment configuration")
    print("• Both summary and detailed CSV files are generated")

def main():
    """Main demo function."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--create-demo":
        demo_file = create_demo_csv()
        print(f"\n📊 Sample CSV data created in: {demo_file}")
        
        # Show first few rows
        print("\n🔍 Sample rows:")
        with open(demo_file, 'r') as f:
            for i, line in enumerate(f):
                if i < 5:  # Show first 5 rows
                    print(f"  {line.strip()}")
        print("  ...")
        
    else:
        show_csv_format()
        print(f"\n🚀 To create a demo CSV file:")
        print(f"  python3 {sys.argv[0]} --create-demo")
        
        print(f"\n🧪 To run actual experiments:")
        print("  ./run_experiments.sh smoke                    # Quick test")
        print("  ./run_experiments.sh quick                    # 5-minute test") 
        print("  python3 run_multi_dataset_experiments.py \\")
        print("    --architecture 'my_arch' \\")
        print("    --model 'my_model' \\")
        print("    --datasets cc_news \\")
        print("    --chunk-sizes 1 5 10")

if __name__ == '__main__':
    main()