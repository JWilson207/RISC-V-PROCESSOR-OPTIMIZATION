#!/bin/bash
# Helper script for common BOOM optimizer tasks

show_help() {
    cat << EOF
BOOM Cache Optimizer - Helper Script

Usage: ./helper.sh <command>

Commands:
    setup           - Run initial setup
    build           - Build all benchmarks
    test <config>   - Test a single configuration
                      Format: ICacheSets,ICacheWays,DCacheSets,DCacheWays
                      Example: ./helper.sh test 64,2,32,8
    optimize        - Run full optimization
    results         - Show latest results
    status          - Check setup status
    clean           - Clean build artifacts
    help            - Show this help message

Examples:
    ./helper.sh setup
    ./helper.sh build
    ./helper.sh test 64,2,32,8
    ./helper.sh optimize
    ./helper.sh results

EOF
}

check_setup() {
    local all_ok=1
    
    echo "Checking setup..."
    
    # Check RISC-V toolchain
    if command -v riscv64-unknown-elf-gcc &> /dev/null; then
        echo "✓ RISC-V toolchain found"
    else
        echo "✗ RISC-V toolchain not found"
        echo "  Run: source $CHIPYARD_PATH/env.sh"
        all_ok=0
    fi
    
    # Check Chipyard path
    if [ -n "$CHIPYARD_PATH" ] && [ -d "$CHIPYARD_PATH" ]; then
        echo "✓ Chipyard path: $CHIPYARD_PATH"
    else
        echo "✗ CHIPYARD_PATH not set or invalid"
        all_ok=0
    fi
    
    # Check benchmarks
    if [ -d "riscv_bins" ] && [ "$(ls -A riscv_bins/*.riscv 2>/dev/null | wc -l)" -gt 0 ]; then
        echo "✓ Benchmarks built ($(ls riscv_bins/*.riscv 2>/dev/null | wc -l) files)"
    else
        echo "✗ Benchmarks not built"
        echo "  Run: ./helper.sh build"
        all_ok=0
    fi
    
    # Check scripts
    if [ -f "boom_optimizer.py" ] && [ -x "boom_optimizer.py" ]; then
        echo "✓ Optimizer script ready"
    else
        echo "✗ Optimizer script not found or not executable"
        all_ok=0
    fi
    
    echo
    if [ $all_ok -eq 1 ]; then
        echo "✓ All checks passed! Ready to optimize."
        return 0
    else
        echo "✗ Some checks failed. Fix the issues above."
        return 1
    fi
}

cmd_setup() {
    echo "Running setup..."
    if [ -f "setup.sh" ]; then
        chmod +x setup.sh
        ./setup.sh
    else
        echo "ERROR: setup.sh not found"
        exit 1
    fi
}

cmd_build() {
    echo "Building benchmarks..."
    make clean
    make all
    echo
    echo "Built binaries:"
    ls -lh riscv_bins/*.riscv 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
}

cmd_test() {
    local config=$1
    
    if [ -z "$config" ]; then
        echo "ERROR: Configuration not specified"
        echo "Usage: ./helper.sh test <ICacheSets>,<ICacheWays>,<DCacheSets>,<DCacheWays>"
        echo "Example: ./helper.sh test 64,2,32,8"
        exit 1
    fi
    
    # Parse configuration
    IFS=',' read -r icache_sets icache_ways dcache_sets dcache_ways <<< "$config"
    
    if [ -z "$icache_sets" ] || [ -z "$icache_ways" ] || [ -z "$dcache_sets" ] || [ -z "$dcache_ways" ]; then
        echo "ERROR: Invalid configuration format"
        echo "Expected: ICacheSets,ICacheWays,DCacheSets,DCacheWays"
        exit 1
    fi
    
    echo "Testing configuration: I$: ${icache_sets}x${icache_ways}, D$: ${dcache_sets}x${dcache_ways}"
    
    if [ -z "$CHIPYARD_PATH" ]; then
        read -p "Enter Chipyard path: " CHIPYARD_PATH
        export CHIPYARD_PATH
    fi
    
    python3 test_config.py "$CHIPYARD_PATH" "$icache_sets" "$icache_ways" "$dcache_sets" "$dcache_ways"
}

cmd_optimize() {
    echo "Starting optimization..."
    echo "This will take several hours. Check optimization_results.json for progress."
    echo
    
    if ! check_setup; then
        echo
        read -p "Setup check failed. Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    python3 boom_optimizer.py | tee optimization.log
    
    echo
    echo "Optimization complete. Results saved to optimization_results.json"
}

cmd_results() {
    if [ -f "optimization_results.json" ]; then
        echo "Latest optimization results:"
        echo
        python3 << 'EOF'
import json
with open('optimization_results.json', 'r') as f:
    data = json.load(f)
    
print(f"Timestamp: {data.get('timestamp', 'N/A')}")
print(f"\nBest Configurations:")
print("-" * 60)

for benchmark, result in data.get('best_configs', {}).items():
    config = result['config']
    print(f"\n{benchmark}:")
    print(f"  I$ Config: {config['icache_sets']} sets × {config['icache_ways']} ways")
    print(f"  D$ Config: {config['dcache_sets']} sets × {config['dcache_ways']} ways")
    print(f"  Cycles: {result['cycles']:,}")
    print(f"  Miss Rate: {result['cache_miss_rate']:.4%}")
    print(f"  Power: {result['power']:.4f} W")
EOF
    else
        echo "No optimization results found."
        echo "Run: ./helper.sh optimize"
    fi
}

cmd_clean() {
    echo "Cleaning build artifacts..."
    make clean
    rm -rf build/ vlsi_runs/
    echo "✓ Clean complete"
}

# Main command dispatcher
case "${1:-help}" in
    setup)
        cmd_setup
        ;;
    build)
        cmd_build
        ;;
    test)
        cmd_test "$2"
        ;;
    optimize)
        cmd_optimize
        ;;
    results)
        cmd_results
        ;;
    status)
        check_setup
        ;;
    clean)
        cmd_clean
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
