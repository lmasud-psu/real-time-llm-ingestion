#!/bin/bash

# Multi-Dataset Experiment Runner Helper Script for Architecture 1
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
        echo "  Start Kafka: docker-compose up -d (from architecture1 directory)"
    fi
    
    # Check if PostgreSQL is running (architecture1 uses port 5432)
    if nc -z localhost 5432 2>/dev/null; then
        print_success "PostgreSQL is running on localhost:5432"
    else
        print_warning "PostgreSQL not detected on localhost:5432"
        echo "  Start PostgreSQL: docker-compose up -d (from architecture1 directory)"
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

🧪 Multi-Dataset Experiment Runner for Architecture 1

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
  $0 performance              # Medium test (prompts for arch/model)
  $0 comprehensive            # Full test suite (prompts for arch/model)
  $0 example                  # Complete example: all datasets/chunks/bursts

Architecture 1 Pipeline:
  Data → text-messages topic → Embedding Service → embeddings topic → Writer Service → PostgreSQL

Environment Variables:
  KAFKA_BOOTSTRAP_SERVERS     Default: localhost:9092
  KAFKA_INPUT_TOPIC           Default: text-messages
  KAFKA_OUTPUT_TOPIC          Default: embeddings
  DATABASE_HOST               Default: localhost
  DATABASE_PORT               Default: 5432 (architecture1)
  DATABASE_NAME               Default: embeddings_db
  DATABASE_USER               Default: postgres
  DATABASE_PASSWORD           Default: password
  DATABASE_TABLE              Default: embeddings

Options (for experiments):
  --datasets        Space-separated list: cc_news, arxiv, wikipedia
  --chunk-sizes     Space-separated list in KB: 1.0 5.0 10.0
  --burst-durations Space-separated list in seconds: 10 30 60
  --max-chunks      Maximum chunks per experiment (10-1000)
  --timeout         Per-test timeout in seconds (60-600)
  --smoke-test      Run minimal validation test

EOF
}

# Command implementations
cmd_setup() {
    print_header "Setting up experiment environment"
    
    cd "$SCRIPT_DIR"
    
    if [[ ! -d "$VENV_DIR" ]]; then
        print_warning "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"
    
    print_warning "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Environment setup complete!"
    print_warning "Infrastructure setup:"
    echo "  1. Start Kafka: cd ../.. && docker-compose up -d (from architecture1 directory)"
    echo "  2. Start services: embedding service and writer service"
    echo "  3. $0 test       # Test dataset streaming"
}

cmd_test() {
    print_header "Testing experiment infrastructure"
    
    if [[ ! -d "$VENV_DIR" ]]; then
        print_error "Virtual environment not found at $VENV_DIR"
        echo "Run: $0 setup"
        exit 1
    fi
    
    "$VENV_DIR/bin/python" "$SCRIPT_DIR/test_experiment_setup.py"
}

cmd_smoke() {
    print_header "Running smoke test"
    check_infrastructure
    
    if [[ ! -d "$VENV_DIR" ]]; then
        print_error "Virtual environment not found at $VENV_DIR"
        echo "Run: $0 setup"
        exit 1
    fi
    
    "$VENV_DIR/bin/python" "$EXPERIMENT_SCRIPT" \
        --architecture "architecture1" \
        --model "sentence-transformers/all-MiniLM-L6-v2" \
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
    
    if [[ ! -d "$VENV_DIR" ]]; then
        print_error "Virtual environment not found at $VENV_DIR"
        echo "Run: $0 setup"
        exit 1
    fi
    
    # Get model from user or use default
    read -p "Model name [sentence-transformers/all-MiniLM-L6-v2]: " model  
    model=${model:-sentence-transformers/all-MiniLM-L6-v2}
    
    print_warning "Quick test: 2 datasets, 3 chunk sizes, no burst, 10 chunks max"
    
    "$VENV_DIR/bin/python" "$EXPERIMENT_SCRIPT" \
        --architecture "architecture1" \
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
    
    if [[ ! -d "$VENV_DIR" ]]; then
        print_error "Virtual environment not found at $VENV_DIR"
        echo "Run: $0 setup"
        exit 1
    fi
    
    # Get model from user or use default
    read -p "Model name [sentence-transformers/all-MiniLM-L6-v2]: " model  
    model=${model:-sentence-transformers/all-MiniLM-L6-v2}
    
    print_warning "Performance test: All datasets, 5 chunk sizes, with burst, 30 chunks max"
    
    "$VENV_DIR/bin/python" "$EXPERIMENT_SCRIPT" \
        --architecture "architecture1" \
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
    
    if [[ ! -d "$VENV_DIR" ]]; then
        print_error "Virtual environment not found at $VENV_DIR"
        echo "Run: $0 setup"
        exit 1
    fi
    
    # Get model from user
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
    
    "$VENV_DIR/bin/python" "$EXPERIMENT_SCRIPT" \
        --architecture "architecture1" \
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
    
    if [[ ! -d "$VENV_DIR" ]]; then
        print_error "Virtual environment not found at $VENV_DIR"
        echo "Run: $0 setup"
        exit 1
    fi
    
    # Get model from user
    read -p "Model name [sentence-transformers/all-MiniLM-L6-v2]: " model  
    model=${model:-sentence-transformers/all-MiniLM-L6-v2}
    
    print_warning "Burst test: Focus on burst patterns with various durations"
    
    "$VENV_DIR/bin/python" "$EXPERIMENT_SCRIPT" \
        --architecture "architecture1" \
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
    
    print_warning "This example demonstrates the full capabilities of Architecture 1 experiment framework."
    echo
    echo "What this will test:"
    echo "  • Pipeline: Data → text-messages → Embedding Service → embeddings → Writer Service → PostgreSQL"
    echo "  • All 3 datasets: CC News, Arxiv, Wikipedia"
    echo "  • Multiple chunk sizes: 1KB, 5KB, 10KB"
    echo "  • Both steady-rate and burst patterns"
    echo "  • End-to-end latency measurement"
    echo
    
    print_warning "Complete Example: Testing all 3 datasets with comprehensive chunk sizes and burst patterns"
    
    echo "  • Datasets: CC News, Arxiv, Wikipedia"
    echo "  • Chunk sizes: 0.5KB, 1KB, 2KB, 5KB, 10KB, 20KB, 40KB"
    echo "  • Burst durations: 5s, 15s, 30s, 60s"
    echo "  • Expected runtime: 30-45 minutes"
    echo
    
    read -p "Continue with example? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    
    check_infrastructure
    
    "$VENV_DIR/bin/python" "$EXPERIMENT_SCRIPT" \
        --architecture "architecture1" \
        --model "sentence-transformers/all-MiniLM-L6-v2" \
        --datasets cc_news arxiv wikipedia \
        --chunk-sizes 0.5 1 2 5 10 20 40 \
        --burst-durations 5 15 30 60 \
        --burst-interval 3 \
        --max-chunks 80 \
        --timeout 300
    
    print_success "Complete example finished!"
    echo
    echo "📊 Check the experiment_results/ directory for detailed CSV outputs"
    echo "💡 Try: $0 comprehensive    # For full experiment suite"
}

# Main command dispatcher
case "${1:-help}" in
    "setup")
        cmd_setup
        ;;
    "test")
        cmd_test
        ;;
    "smoke")
        cmd_smoke
        ;;
    "quick")
        cmd_quick
        ;;
    "performance")
        cmd_performance
        ;;
    "comprehensive")
        cmd_comprehensive
        ;;
    "burst")
        cmd_burst
        ;;
    "example")
        cmd_example
        ;;
    "help"|*)
        show_usage
        ;;
esac