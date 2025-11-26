#!/usr/bin/env python3
"""
Extract comprehensive metrics from Verilator simulation output
Extracts: cycles, instructions, cache misses, etc.
"""

import os
import sys
import re

def extract_all_metrics(out_file):
    """Extract all available metrics from .out file"""
    
    if not os.path.exists(out_file):
        print(f"ERROR: File not found: {out_file}")
        return None
    
    with open(out_file, 'r') as f:
        content = f.read()
    
    metrics = {}
    
    # Extract cycle count
    match = re.search(r'Completed after\s+(\d+)\s+simulation cycles', content)
    if match:
        metrics['cycles'] = int(match.group(1))
    else:
        metrics['cycles'] = 0
    
    # Count total instructions (C0: lines between setStats)
    lines = content.split('\n')
    instr_count = 0
    counting = False
    
    for line in lines:
        # Look for setStats markers (writes to CSR)
        if 'write_csr' in line or 'csrw' in line:
            counting = not counting  # Toggle on/off
        elif counting and line.strip().startswith('C0:'):
            instr_count += 1
    
    metrics['instructions'] = instr_count
    
    # Calculate IPC (Instructions Per Cycle)
    if metrics['cycles'] > 0:
        metrics['ipc'] = metrics['instructions'] / metrics['cycles']
    else:
        metrics['ipc'] = 0.0
    
    # Look for cache stats (might be in some outputs)
    cache_miss = re.search(r'I\$.*miss.*?(\d+)', content, re.IGNORECASE)
    if cache_miss:
        metrics['icache_misses'] = int(cache_miss.group(1))
    
    cache_miss = re.search(r'D\$.*miss.*?(\d+)', content, re.IGNORECASE)
    if cache_miss:
        metrics['dcache_misses'] = int(cache_miss.group(1))
    
    # Check for PASSED/FAILED
    if '*** PASSED ***' in content:
        metrics['status'] = 'PASSED'
    elif '*** FAILED ***' in content:
        metrics['status'] = 'FAILED'
    else:
        metrics['status'] = 'UNKNOWN'
    
    return metrics

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_metrics.py <benchmark_name> [chipyard_path]")
        print("Example: python3 extract_metrics.py aes")
        sys.exit(1)
    
    benchmark = sys.argv[1]
    chipyard_path = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('CHIPYARD_PATH', '/home/jackvw/rocket/chipyard-c')
    
    out_file = f"{chipyard_path}/sims/verilator/output/chipyard.harness.TestHarness.ECE5504RocketConfig/{benchmark}.out"
    
    print(f"Extracting metrics from: {out_file}")
    print()
    
    metrics = extract_all_metrics(out_file)
    
    if metrics:
        print(f"{'='*50}")
        print(f"Results for {benchmark}:")
        print(f"{'='*50}")
        print(f"Status:        {metrics['status']}")
        print(f"Cycles:        {metrics['cycles']:,}")
        print(f"Instructions:  {metrics['instructions']:,}")
        print(f"IPC:           {metrics['ipc']:.3f}")
        
        if 'icache_misses' in metrics:
            print(f"I$ Misses:     {metrics['icache_misses']:,}")
        if 'dcache_misses' in metrics:
            print(f"D$ Misses:     {metrics['dcache_misses']:,}")
        
        print(f"{'='*50}")
    else:
        print(f"✗ Failed to extract metrics")

if __name__ == '__main__':
    main()
