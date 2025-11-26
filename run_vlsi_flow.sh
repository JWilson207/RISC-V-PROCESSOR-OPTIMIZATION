#!/bin/bash
# VLSI Flow Script for BOOM Configuration Testing
# This script runs the complete synthesis, simulation, and power analysis flow

set -e  # Exit on error

# Configuration
CONFIG_NAME=$1
BENCHMARK=$2
CHIPYARD_PATH=${CHIPYARD_PATH:-/path/to/chipyard}
WORK_DIR=$(pwd)/vlsi_runs/${CONFIG_NAME}_${BENCHMARK}

if [ -z "$CONFIG_NAME" ] || [ -z "$BENCHMARK" ]; then
    echo "Usage: $0 <config_name> <benchmark>"
    echo "Example: $0 ECE5504RocketConfig multiplication"
    exit 1
fi

echo "============================================"
echo "Running VLSI Flow"
echo "Config: $CONFIG_NAME"
echo "Benchmark: $BENCHMARK"
echo "============================================"

# Create work directory
mkdir -p $WORK_DIR
cd $WORK_DIR

# Step 1: Generate RTL
echo "[1/5] Generating RTL..."
cd $CHIPYARD_PATH
make -C sims/vcs CONFIG=$CONFIG_NAME

# Step 2: Run Simulation
echo "[2/5] Running simulation..."
BINARY_PATH=$CHIPYARD_PATH/benchmarks/riscv_bins/${BENCHMARK}.riscv

if [ ! -f "$BINARY_PATH" ]; then
    echo "Error: Benchmark binary not found: $BINARY_PATH"
    exit 1
fi

cd $CHIPYARD_PATH/sims/vcs
make run-binary CONFIG=$CONFIG_NAME BINARY=$BINARY_PATH \
    OUTPUT_DIR=$WORK_DIR | tee $WORK_DIR/simulation.log

# Step 3: Extract Performance Metrics
echo "[3/5] Extracting performance metrics..."

# Extract cycle count
CYCLES=$(grep -oP '(?<=total_cycles: )\d+' $WORK_DIR/simulation.log | tail -1)
if [ -z "$CYCLES" ]; then
    echo "Warning: Could not extract cycle count"
    CYCLES=0
fi

# Extract cache statistics (adjust grep patterns based on your output)
ICACHE_MISS=$(grep -oP '(?<=icache_miss: )\d+' $WORK_DIR/simulation.log | tail -1 || echo 0)
DCACHE_MISS=$(grep -oP '(?<=dcache_miss: )\d+' $WORK_DIR/simulation.log | tail -1 || echo 0)
CACHE_ACCESS=$(grep -oP '(?<=cache_access: )\d+' $WORK_DIR/simulation.log | tail -1 || echo 1)

# Calculate miss rate
CACHE_MISS_RATE=$(echo "scale=6; ($ICACHE_MISS + $DCACHE_MISS) / $CACHE_ACCESS" | bc)

# Step 4: Power Analysis (if using commercial tools)
echo "[4/5] Running power analysis..."

# This is a placeholder - adapt to your power analysis flow
# Example with PrimeTime:
# pt_shell -f power_analysis.tcl

# For now, we'll extract from simulation if available
POWER=$(grep -oP '(?<=power: )\d+\.\d+' $WORK_DIR/simulation.log | tail -1 || echo 0.0)

# Step 5: Generate Results
echo "[5/5] Generating results..."

cat > $WORK_DIR/results.json <<EOF
{
  "config": "$CONFIG_NAME",
  "benchmark": "$BENCHMARK",
  "cycles": $CYCLES,
  "cache_miss_rate": $CACHE_MISS_RATE,
  "icache_misses": $ICACHE_MISS,
  "dcache_misses": $DCACHE_MISS,
  "power": $POWER,
  "timestamp": "$(date -Iseconds)"
}
EOF

echo "============================================"
echo "Results Summary:"
echo "  Cycles: $CYCLES"
echo "  Cache Miss Rate: $CACHE_MISS_RATE"
echo "  Power: $POWER W"
echo "  Results saved to: $WORK_DIR/results.json"
echo "============================================"

# Return results file path for Python script to parse
echo $WORK_DIR/results.json
