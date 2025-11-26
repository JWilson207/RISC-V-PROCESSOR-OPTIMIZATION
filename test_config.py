#!/usr/bin/env python3
"""
Simple Configuration Tester
Test a single cache configuration on all benchmarks
Useful for manual testing before running full optimization
"""

import sys
import os
import json
import subprocess
from datetime import datetime

class SimpleConfigTester:
    def __init__(self, icache_sets, icache_ways, dcache_sets, dcache_ways):
        self.config = {
            'icache_sets': icache_sets,
            'icache_ways': icache_ways,
            'dcache_sets': dcache_sets,
            'dcache_ways': dcache_ways
        }
        self.results = []
    
    def update_scala_config(self, chipyard_path):
        """Update ECE5504RocketConfigs.scala with new configuration"""
        config_file = os.path.join(chipyard_path, 
            'generators/chipyard/src/main/scala/config/ECE5504RocketConfigs.scala')
        
        # Backup original
        backup_file = config_file + '.backup'
        if not os.path.exists(backup_file):
            subprocess.run(['cp', config_file, backup_file])
            print(f"Created backup: {backup_file}")
        
        # Read file
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Create new config lines
        new_config = f"""  new WithL1ICacheSets({self.config['icache_sets']}) ++
  new WithL1ICacheWays({self.config['icache_ways']}) ++
  new WithL1DCacheSets({self.config['dcache_sets']}) ++
  new WithL1DCacheWays({self.config['dcache_ways']}) ++"""
        
        # Replace using simple string replacement
        # Find the section between "class ECE5504RocketConfig" and "new ECE5504AbstractRocketConfig"
        import re
        pattern = r'(class ECE5504RocketConfig extends Config\(\s*new WithL1ICacheSets\(\d+\) \+\+\s*new WithL1ICacheWays\(\d+\) \+\+\s*new WithL1DCacheSets\(\d+\) \+\+\s*new WithL1DCacheWays\(\d+\) \+\+)'
        
        if re.search(pattern, content):
            new_content = re.sub(pattern, 
                                f'class ECE5504RocketConfig extends Config(\n{new_config}',
                                content)
            
            with open(config_file, 'w') as f:
                f.write(new_content)
            
            print(f"Updated config:")
            print(f"  I-cache: {self.config['icache_sets']} sets × {self.config['icache_ways']} ways")
            print(f"  D-cache: {self.config['dcache_sets']} sets × {self.config['dcache_ways']} ways")
            return True
        else:
            print("ERROR: Could not find ECE5504RocketConfig class in Scala file")
            print("Please manually edit the file or check the pattern")
            return False
    
    def test_benchmark(self, chipyard_path, benchmark):
        """Test configuration on a single benchmark"""
        print(f"\n{'='*50}")
        print(f"Testing benchmark: {benchmark}")
        print(f"{'='*50}")
        
        # Path to benchmark binary - use .riscv from riscv-tests
        bench_dir = f"{chipyard_path}/toolchains/riscv-tools/riscv-tests/benchmarks"
        binary_path = f"{bench_dir}/{benchmark}.riscv"
        
        if not os.path.exists(binary_path):
            print(f"ERROR: Benchmark binary not found: {binary_path}")
            print(f"Build it with: cd {bench_dir} && make {benchmark}.riscv")
            return None
        
        # Run simulation
        print(f"Running simulation...")
        
        try:
            # Use Verilator
            sim_type = "verilator"
            sim_dir = os.path.join(chipyard_path, f'sims/{sim_type}')
            
            # Run simulation
            print("Running benchmark...")
            run_cmd = f"cd {sim_dir} && make run-binary CONFIG=ECE5504RocketConfig BINARY={binary_path}"
            result = subprocess.run(run_cmd, shell=True, capture_output=True, text=True)
            
            # Read the .OUT file - this is where cycle counts and instruction traces are
            out_file = f"{sim_dir}/output/chipyard.harness.TestHarness.ECE5504RocketConfig/{benchmark}.out"
            
            cycles = 0
            instructions = 0
            ipc = 0.0
            status = 'unknown'
            
            if os.path.exists(out_file):
                with open(out_file, 'r') as f:
                    out_content = f.read()
                
                # Extract cycles
                cycles = self._extract_metric(out_content, r'Completed after\s+(\d+)\s+simulation cycles', default=0)
                
                # Count instructions (C0: lines)
                lines = out_content.split('\n')
                instructions = len([l for l in lines if l.strip().startswith('C0:')])
                
                # Calculate IPC
                if cycles > 0:
                    ipc = instructions / cycles
                
                # Check status
                if '*** PASSED ***' in out_content:
                    status = 'PASSED'
                elif '*** FAILED ***' in out_content:
                    status = 'FAILED'
            else:
                print(f"Warning: Output file not found: {out_file}")
            
            result_dict = {
                'benchmark': benchmark,
                'cycles': cycles,
                'instructions': instructions,
                'ipc': ipc,
                'cache_miss_rate': 0.0,  # Not available in basic Verilator output
                'status': status
            }
            
            print(f"\nResults:")
            print(f"  Status: {status}")
            print(f"  Cycles: {cycles:,}")
            print(f"  Instructions: {instructions:,}")
            print(f"  IPC: {ipc:.3f}")
            if cycles == 0:
                print(f"  ⚠ Warning: Cycle count is 0. Check: {out_file}")
            
            self.results.append(result_dict)
            return result_dict
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Simulation failed: {e}")
            result_dict = {
                'benchmark': benchmark,
                'status': 'failed',
                'error': str(e)
            }
            self.results.append(result_dict)
            return result_dict
        except subprocess.TimeoutExpired:
            print(f"ERROR: Simulation timed out (>300s)")
            result_dict = {
                'benchmark': benchmark,
                'status': 'timeout',
                'error': 'Simulation exceeded 5 minutes'
            }
            self.results.append(result_dict)
            return result_dict
    
    def _extract_metric(self, text, pattern, default=0):
        """Extract metric from simulation output"""
        import re
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
        return default
    
    def test_all_benchmarks(self, chipyard_path, benchmarks):
        """Test configuration on all benchmarks"""
        print(f"\n{'='*60}")
        print(f"Testing Configuration on All Benchmarks")
        print(f"{'='*60}\n")
        print(f"Configuration:")
        print(f"  I$ Sets: {self.config['icache_sets']}, Ways: {self.config['icache_ways']}")
        print(f"  D$ Sets: {self.config['dcache_sets']}, Ways: {self.config['dcache_ways']}")
        
        # Default benchmarks if none provided
        if not benchmarks:
            benchmarks = ['dhrystone', 'multiplication', 'qsort', 'aes', 'convolution', 'sha256']
        
        for benchmark in benchmarks:
            self.test_benchmark(chipyard_path, benchmark)
        
        # Summary
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Print summary of all results"""
        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}\n")
        
        successful = [r for r in self.results if r['status'] == 'success']
        
        if not successful:
            print("No successful tests")
            return
        
        print(f"{'Benchmark':<20} {'Cycles':>15} {'Miss Rate':>12}")
        print("-" * 50)
        
        total_cycles = 0
        for result in successful:
            print(f"{result['benchmark']:<20} {result['cycles']:>15,} {result['cache_miss_rate']:>11.4%}")
            total_cycles += result['cycles']
        
        avg_cycles = total_cycles / len(successful)
        print("-" * 50)
        print(f"{'Average':<20} {avg_cycles:>15,.0f}")
    
    def save_results(self):
        """Save results to JSON file"""
        output = {
            'config': self.config,
            'timestamp': datetime.now().isoformat(),
            'results': self.results
        }
        
        filename = f"test_results_{self.config['icache_sets']}x{self.config['icache_ways']}_" \
                  f"{self.config['dcache_sets']}x{self.config['dcache_ways']}.json"
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults saved to: {filename}")

def main():
    if len(sys.argv) != 6:
        print("Usage: python3 test_config.py <chipyard_path> <icache_sets> <icache_ways> <dcache_sets> <dcache_ways>")
        print("\nExample:")
        print("  python3 test_config.py /home/user/chipyard 64 2 32 8")
        print("\nThis tests I-cache: 64 sets × 2 ways, D-cache: 32 sets × 8 ways")
        sys.exit(1)
    
    chipyard_path = sys.argv[1]
    icache_sets = int(sys.argv[2])
    icache_ways = int(sys.argv[3])
    dcache_sets = int(sys.argv[4])
    dcache_ways = int(sys.argv[5])
    
    # Validate inputs
    if not os.path.exists(chipyard_path):
        print(f"ERROR: Chipyard path not found: {chipyard_path}")
        sys.exit(1)
    
    # BOOM-compatible benchmarks from riscv-tests
    benchmarks = ['dhrystone', 'multiplication', 'qsort', 'aes', 'convolution', 'sha256']
    
    # Create tester
    tester = SimpleConfigTester(icache_sets, icache_ways, dcache_sets, dcache_ways)
    
    # Update configuration
    if not tester.update_scala_config(chipyard_path):
        sys.exit(1)
    
    # Test all benchmarks
    tester.test_all_benchmarks(chipyard_path, benchmarks)

if __name__ == '__main__':
    main()