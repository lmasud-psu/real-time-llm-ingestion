#!/bin/bash

# Multi-Dataset Experiment Runner Helper Script
# Provides easy shortcuts for common experiment configurations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPERIMENT_SCRIPT="$SCRIPT_DIR/run_multi_dataset_experiments.py"
VENV_DIR="$SCRIPT_DIR/experiment_venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}🧪 $1${NC}"
    echo "$(printf '=%.0s' {1..60})"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

activate_venv() {
    if [[ -d "$VENV_DIR" ]]; then
        source "$VENV_DIR/bin/activate"
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment not found at $VENV_DIR"
        echo "Run: python3 -m venv $VENV_DIR && source $VENV_DIR/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
}

check_infrastructure() {
    print_header "Checking Infrastructure"
    
    # Check if Kafka is running
    if nc -z localhost 9092 2>/dev/null; then
        print_success "Kafka is running on localhost:9092"
    else
        print_warning "Kafka not detected on localhost:9092"
        echo "  Start Kafka: docker-compose up -d (from kafka directory)"
    fi
    
    # Check if PostgreSQL is running (architecture3 uses port 5434)
    if nc -z localhost 5434 2>/dev/null; then
        print_success "PostgreSQL is running on localhost:5434"
    else
        print_warning "PostgreSQL not detected on localhost:5434"
        echo "  Start PostgreSQL: docker-compose up -d (from architecture3 directory)"
    fi
    
    # Test dataset imports (using virtual environment if available)
    if [[ -d "$VENV_DIR" ]]; then
        "$VENV_DIR/bin/python" "$SCRIPT_DIR/test_experiment_setup.py" > /dev/null 2>&1
    else
        python3 "$SCRIPT_DIR/test_experiment_setup.py" > /dev/null 2>&1
    fi
    
    if [[ $? -eq 0 ]]; then
        print_success "Dataset modules imported successfully"
    else
        print_error "Dataset module import failed"
        echo "  Run: ./experiment_venv/bin/python test_experiment_setup.py for details"
        exit 1
    fi
}

show_usage() {
    cat << EOF

🧪 Multi-Dataset Experiment Runner

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  setup           Setup virtual environment and dependencies
  test            Test infrastructure without Kafka/DB requirements
  smoke           Run smoke test (requires Kafka/DB)
  quick           Quick experiment (small scale, fast)
  performance     Performance test (medium scale)  
  comprehensive   Full experiment suite (all datasets, all sizes)
  burst           Burst pattern testing only
  example         Run complete example with all datasets/chunks/bursts
  help            Show this help message

Examples:
  $0 setup                    # Setup environment
  $0 test                     # Test dataset streaming
  $0 smoke                    # Test full infrastructure  
  $0 quick                    # Quick 5-minute test (prompts for arch/model)
  $0 performance              # 20-minute performance test
  $0 comprehensive            # Full 1-2 hour test suite
  $0 example                  # Complete example: all datasets/chunks/bursts

CSV Output:
  Each experiment produces two CSV files:
  - *_summary.csv: Architecture, Model, Dataset, Chunk, Burst_Length, Result_ms
  - *_detailed.csv: Full metrics including throughput, success rates, etc.

Complete CLI Examples:

1. Single Dataset with Multiple Chunk Sizes:
   python3 run_multi_dataset_experiments.py \\
     --architecture "architecture3" \\
     --model "sentence-transformers/all-MiniLM-L6-v2" \\
     --datasets cc_news \\
     --chunk-sizes 1 5 10 20 40

2. All Datasets with Burst Patterns:
   python3 run_multi_dataset_experiments.py \\
     --architecture "architecture3" \\
     --model "sentence-transformers/all-MiniLM-L6-v2" \\
     --datasets cc_news arxiv wikipedia \\
     --chunk-sizes 2 8 15 30 \\
     --burst-durations 10 30 60 \\
     --burst-interval 5 \\
     --max-chunks 50

3. Performance Testing - All Combinations:
   python3 run_multi_dataset_experiments.py \\
     --architecture "architecture3" \\
     --model "sentence-transformers/all-MiniLM-L6-v2" \\
     --datasets cc_news arxiv wikipedia \\
     --chunk-sizes 0.5 1 2 5 10 20 40 80 \\
     --burst-durations 1 5 10 15 30 45 60 \\
     --burst-interval 2 \\
     --max-chunks 100 \\
     --timeout 300

4. Quick Smoke Test:
   python3 run_multi_dataset_experiments.py \\
     --architecture "test_architecture" \\
     --model "test_model" \\
     --smoke-test

5. Large Scale Comprehensive Testing:
   python3 run_multi_dataset_experiments.py \\
     --architecture "architecture3" \\
     --model "sentence-transformers/all-MiniLM-L6-v2" \\
     --datasets cc_news arxiv wikipedia \\
     --chunk-sizes 0.5 1 2 4 8 16 32 64 80 \\
     --burst-durations 1 2 5 10 15 30 45 60 \\
     --burst-interval 3 \\
     --max-chunks 200 \\
     --timeout 600

Parameter Descriptions:
  --architecture     Target architecture (architecture1, architecture2, architecture3)
  --model           Embedding model name (HuggingFace format)
  --datasets        Space-separated list: cc_news, arxiv, wikipedia
  --chunk-sizes     Space-separated sizes in KB (0.5-80)
  --burst-durations Burst duration in seconds (1-60)
  --burst-interval  Seconds between bursts (1-10)
  --max-chunks      Maximum chunks per test (10-1000)
  --timeout         Per-test timeout in seconds (60-600)
  --smoke-test      Run minimal validation test

Environment Variables:
  KAFKA_BOOTSTRAP_SERVERS     Default: localhost:9092
  DATABASE_HOST               Default: localhost
  DATABASE_PORT               Default: 5434 (architecture3)

EOF
}

# Command implementations
cmd_setup() {
    print_header "Setting up experiment environment"
    
    cd "$SCRIPT_DIR"
    
    # Create virtual environment
    if [[ ! -d "$VENV_DIR" ]]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    fi
    
    # Activate and install dependencies
    activate_venv
    
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    print_success "Setup complete!"
    echo ""
    echo "Next steps:"
    echo "  1. $0 test        # Test dataset streaming"
    echo "  2. $0 smoke       # Test full infrastructure"
    echo "  3. $0 quick       # Run quick experiment"
}

cmd_test() {
    print_header "Testing experiment infrastructure"
    activate_venv
    python3 "$SCRIPT_DIR/test_experiment_setup.py"
}

cmd_smoke() {
    print_header "Running smoke test"
    check_infrastructure
    activate_venv
    
    python3 "$EXPERIMENT_SCRIPT" \
        --architecture "test_architecture" \
        --model "test_model" \
        --smoke-test
    
    if [[ $? -eq 0 ]]; then
        print_success "Smoke test passed! Infrastructure is ready."
    else
        print_error "Smoke test failed. Check infrastructure setup."
        exit 1
    fi
}

cmd_quick() {
    print_header "Running quick experiment"
    check_infrastructure
    activate_venv
    
    # Get architecture and model from user or use defaults
    read -p "Architecture name [architecture3]: " arch
    arch=${arch:-architecture3}
    
    read -p "Model name [sentence-transformers/all-MiniLM-L6-v2]: " model  
    model=${model:-sentence-transformers/all-MiniLM-L6-v2}
    
    print_warning "Quick test: 2 datasets, 3 chunk sizes, no burst, 10 chunks max"
    
    python3 "$EXPERIMENT_SCRIPT" \
        --architecture "$arch" \
        --model "$model" \
        --datasets cc_news wikipedia \
        --chunk-sizes 1 5 10 \
        --no-burst \
        --max-chunks 10 \
        --timeout 180
    
    print_success "Quick experiment completed!"
}

cmd_performance() {
    print_header "Running performance experiment"
    check_infrastructure
    activate_venv
    
    # Get architecture and model from user or use defaults
    read -p "Architecture name [architecture3]: " arch
    arch=${arch:-architecture3}
    
    read -p "Model name [sentence-transformers/all-MiniLM-L6-v2]: " model  
    model=${model:-sentence-transformers/all-MiniLM-L6-v2}
    
    print_warning "Performance test: All datasets, 5 chunk sizes, with burst, 30 chunks max"
    
    python3 "$EXPERIMENT_SCRIPT" \
        --architecture "$arch" \
        --model "$model" \
        --datasets cc_news arxiv wikipedia \
        --chunk-sizes 1 2 5 10 20 \
        --burst-durations 30 \
        --burst-interval 5 \
        --max-chunks 30 \
        --timeout 300
    
    print_success "Performance experiment completed!"
}

cmd_comprehensive() {
    print_header "Running comprehensive experiment suite"
    check_infrastructure
    activate_venv
    
    # Get architecture and model from user
    read -p "Architecture name [architecture3]: " arch
    arch=${arch:-architecture3}
    
    read -p "Model name [sentence-transformers/all-MiniLM-L6-v2]: " model  
    model=${model:-sentence-transformers/all-MiniLM-L6-v2}
    
    print_warning "Comprehensive test: All datasets, all chunk sizes, full burst testing"
    echo "This may take 1-2 hours to complete!"
    
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    
    python3 "$EXPERIMENT_SCRIPT" \
        --architecture "$arch" \
        --model "$model" \
        --datasets cc_news arxiv wikipedia \
        --chunk-sizes 0.5 1 2 5 10 20 40 80 \
        --burst-durations 30 60 \
        --burst-interval 5 \
        --max-chunks 50 \
        --timeout 300
    
    print_success "Comprehensive experiment completed!"
}

cmd_burst() {
    print_header "Running burst pattern experiment"
    check_infrastructure
    activate_venv
    
    # Get architecture and model from user
    read -p "Architecture name [architecture3]: " arch
    arch=${arch:-architecture3}
    
    read -p "Model name [sentence-transformers/all-MiniLM-L6-v2]: " model  
    model=${model:-sentence-transformers/all-MiniLM-L6-v2}
    
    print_warning "Burst test: Focus on burst patterns with various durations"
    
    python3 "$EXPERIMENT_SCRIPT" \
        --architecture "$arch" \
        --model "$model" \
        --datasets cc_news arxiv \
        --chunk-sizes 2 8 20 \
        --burst-durations 15 30 45 60 \
        --burst-interval 3 \
        --max-chunks 40 \
        --timeout 240
    
    print_success "Burst experiment completed!"
}

cmd_example() {
    print_header "Running Complete Example: All Datasets, Chunks, and Burst Patterns"
    check_infrastructure
    activate_venv
    
    # Get architecture and model from user
    read -p "Architecture name [architecture3]: " arch
    arch=${arch:-architecture3}
    
    read -p "Model name [sentence-transformers/all-MiniLM-L6-v2]: " model  
    model=${model:-sentence-transformers/all-MiniLM-L6-v2}
    
    print_warning "Complete Example: Testing all 3 datasets with comprehensive chunk sizes and burst patterns"
    echo "This will test:"
    echo "  • Datasets: CC News, Arxiv, Wikipedia"
    echo "  • Chunk sizes: 0.5KB, 1KB, 2KB, 5KB, 10KB, 20KB, 40KB"
    echo "  • Burst durations: 5s, 15s, 30s, 60s"
    echo "  • Expected runtime: 30-45 minutes"
    echo ""
    
    read -p "Continue with complete example? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Example cancelled."
        exit 0
    fi
    
    python3 "$EXPERIMENT_SCRIPT" \
        --architecture "$arch" \
        --model "$model" \
        --datasets cc_news arxiv wikipedia \
        --chunk-sizes 0.5 1 2 5 10 20 40 \
        --burst-durations 5 15 30 60 \
        --burst-interval 3 \
        --max-chunks 80 \
        --timeout 300
    
    print_success "Complete example experiment finished!"
    echo ""
    print_header "Results Summary"
    echo "Check the generated CSV files for detailed results:"
    echo "  • *_summary.csv: Architecture, Model, Dataset, Chunk, Burst_Length, Result_ms"
    echo "  • *_detailed.csv: Full metrics with throughput and success rates"
    echo ""
    echo "This example demonstrates:"
    echo "  ✅ Multi-dataset ingestion (CC News, Arxiv, Wikipedia)" 
    echo "  ✅ Variable chunk sizes (0.5KB to 40KB)"
    echo "  ✅ Burst pattern testing (5s to 60s durations)"
    echo "  ✅ Performance measurement and CSV output"
}

# Main command dispatcher
case "${1:-help}" in
    setup)
        cmd_setup
        ;;
    test)
        cmd_test
        ;;
    smoke)
        cmd_smoke
        ;;
    quick)
        cmd_quick
        ;;
    performance)
        cmd_performance
        ;;
    comprehensive)
        cmd_comprehensive
        ;;
    burst)
        cmd_burst
        ;;
    example)
        cmd_example
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac