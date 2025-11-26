#!/usr/bin/env python3
"""
BOOM Cache Configuration Optimizer
Simplified version inspired by BOOM-Explorer paper
Optimizes L1 I-cache and D-cache configurations for multiple benchmarks
"""

import os
import json
import subprocess
import itertools
from typing import Dict, List, Tuple
import concurrent.futures
from datetime import datetime

class CacheConfig:
    """Represents a cache configuration"""
    def __init__(self, icache_sets, icache_ways, dcache_sets, dcache_ways):
        self.icache_sets = icache_sets
        self.icache_ways = icache_ways
        self.dcache_sets = dcache_sets
        self.dcache_ways = dcache_ways
    
    def __str__(self):
        return f"I$:{self.icache_sets}x{self.icache_ways} D$:{self.dcache_sets}x{self.dcache_ways}"
    
    def to_scala_config(self):
        """Generate Scala configuration code"""
        return f"""  new WithL1ICacheSets({self.icache_sets}) ++
  new WithL1ICacheWays({self.icache_ways}) ++
  new WithL1DCacheSets({self.dcache_sets}) ++
  new WithL1DCacheWays({self.dcache_ways}) ++"""
    
    def to_dict(self):
        return {
            'icache_sets': self.icache_sets,
            'icache_ways': self.icache_ways,
            'dcache_sets': self.dcache_sets,
            'dcache_ways': self.dcache_ways
        }

class DesignSpaceExplorer:
    """Main optimizer class"""
    
    def __init__(self, config_file='design_space.json'):
        self.load_config(config_file)
        self.results = []
        self.best_configs = {}
        
    def load_config(self, config_file):
        """Load design space configuration"""
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.params = config['parameters']
        self.benchmarks = config['benchmarks']
        self.chipyard_path = config['chipyard_path']
        self.num_parallel = config.get('num_parallel_jobs', 4)
        self.max_evaluations = config.get('max_evaluations', 50)
        
        # Metrics to optimize (from your image)
        self.optimize_metrics = config.get('optimize_metrics', ['cycles', 'cache_miss'])
        
    def is_valid_config(self, config: CacheConfig) -> bool:
        """Check if configuration meets constraints"""
        # Total I-cache size <= 32KB (assuming 64B line size)
        icache_size = config.icache_sets * config.icache_ways * 64
        if icache_size > 32768:
            return False
        
        # Total D-cache size <= 32KB
        dcache_size = config.dcache_sets * config.dcache_ways * 64
        if dcache_size > 32768:
            return False
        
        return True
    
    def generate_design_space(self) -> List[CacheConfig]:
        """Generate all valid cache configurations"""
        configs = []
        
        for icache_sets in self.params['L1ICacheSets']:
            for icache_ways in self.params['L1ICacheWays']:
                for dcache_sets in self.params['L1DCacheSets']:
                    for dcache_ways in self.params['L1DCacheWays']:
                        config = CacheConfig(icache_sets, icache_ways, 
                                           dcache_sets, dcache_ways)
                        if self.is_valid_config(config):
                            configs.append(config)
        
        print(f"Generated {len(configs)} valid configurations")
        return configs
    
    def smart_sample_configs(self, configs: List[CacheConfig], n_samples: int) -> List[CacheConfig]:
        """
        Smart sampling inspired by MicroAL from the paper
        Samples diverse configurations across the design space
        """
        if len(configs) <= n_samples:
            return configs
        
        # Strategy: Sample configurations that maximize diversity
        # Group by I-cache size (similar to clustering by DecodeWidth in paper)
        icache_groups = {}
        for config in configs:
            key = config.icache_sets * config.icache_ways
            if key not in icache_groups:
                icache_groups[key] = []
            icache_groups[key].append(config)
        
        # Sample proportionally from each group
        sampled = []
        samples_per_group = max(1, n_samples // len(icache_groups))
        
        for group in icache_groups.values():
            # Sample evenly from each group
            step = max(1, len(group) // samples_per_group)
            sampled.extend(group[::step][:samples_per_group])
        
        # If we need more samples, add from largest groups
        while len(sampled) < n_samples:
            largest_group = max(icache_groups.values(), key=len)
            for config in largest_group:
                if config not in sampled:
                    sampled.append(config)
                    if len(sampled) >= n_samples:
                        break
        
        return sampled[:n_samples]
    
    def update_scala_config(self, config: CacheConfig):
        """Update the Scala configuration file"""
        config_path = os.path.join(self.chipyard_path, 
                                   'generators/chipyard/src/main/scala/config/ECE5504RocketConfigs.scala')
        
        # Read current config
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Replace cache configuration lines
        # Find the ECE5504RocketConfig class
        import re
        pattern = r'(class ECE5504RocketConfig extends Config\(\s*)(new WithL1ICacheSets\(\d+\)[^\)]+\+\+\s*new WithL1ICacheWays\(\d+\)[^\)]+\+\+\s*new WithL1DCacheSets\(\d+\)[^\)]+\+\+\s*new WithL1DCacheWays\(\d+\)[^\)]+\+\+)'
        
        new_config = config.to_scala_config()
        replacement = r'\1' + new_config
        
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Write back
        with open(config_path, 'w') as f:
            f.write(new_content)
        
        print(f"Updated config to: {config}")
    
    def run_vlsi_flow(self, config: CacheConfig, benchmark: str) -> Dict:
        """
        Run VLSI flow for a configuration and benchmark
        Returns metrics: cycles, cache_miss_rate, power
        """
        print(f"Evaluating {config} on {benchmark}...")
        
        # Update Scala configuration
        self.update_scala_config(config)
        
        # Run synthesis and simulation
        # This is a placeholder - adapt to your actual VLSI flow
        result = {
            'config': config.to_dict(),
            'benchmark': benchmark,
            'cycles': 0,
            'cache_miss_rate': 0.0,
            'power': 0.0,
            'status': 'pending'
        }
        
        try:
            # TODO: Replace with your actual VLSI flow commands
            # Example workflow:
            # 1. cd to chipyard
            # 2. make rtl (generate RTL)
            # 3. Run synthesis with Genus
            # 4. Run simulation with VCS
            # 5. Run power analysis with PrimeTime
            
            # Placeholder for demonstration
            result['cycles'] = self._run_simulation(config, benchmark)
            result['cache_miss_rate'] = self._get_cache_miss_rate(config, benchmark)
            result['power'] = self._get_power(config, benchmark)
            result['status'] = 'completed'
            
        except Exception as e:
            print(f"Error evaluating {config} on {benchmark}: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
        
        return result
    
    def _run_simulation(self, config: CacheConfig, benchmark: str) -> int:
        """Run VCS simulation and extract cycle count"""
        # Placeholder - implement your actual simulation flow
        # This should:
        # 1. Compile the BOOM design with current config
        # 2. Run the benchmark
        # 3. Extract cycle count from simulation output
        
        # Example command structure:
        # cd $CHIPYARD_PATH
        # make run-binary CONFIG=ECE5504RocketConfig BINARY=$PWD/benchmarks/{benchmark}.riscv
        
        return 60000  # Placeholder
    
    def _get_cache_miss_rate(self, config: CacheConfig, benchmark: str) -> float:
        """Extract cache miss rate from simulation"""
        # Placeholder - extract from simulation logs or performance counters
        return 0.05  # Placeholder
    
    def _get_power(self, config: CacheConfig, benchmark: str) -> float:
        """Extract power from PrimeTime analysis"""
        # Placeholder - run PrimeTime and extract power
        return 0.06  # Placeholder
    
    def evaluate_configs_parallel(self, configs: List[CacheConfig]) -> List[Dict]:
        """Evaluate multiple configurations in parallel"""
        all_results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_parallel) as executor:
            futures = []
            for config in configs:
                for benchmark in self.benchmarks:
                    future = executor.submit(self.run_vlsi_flow, config, benchmark)
                    futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                all_results.append(result)
                self.results.append(result)
        
        return all_results
    
    def calculate_score(self, result: Dict) -> float:
        """
        Calculate optimization score for a result
        Lower is better (minimizing cycles and cache misses)
        """
        # Normalize and weight different metrics
        # Adjust weights based on your priorities
        weights = {
            'cycles': 0.6,
            'cache_miss_rate': 0.3,
            'power': 0.1
        }
        
        # Normalize to baseline (first configuration)
        baseline_cycles = 65000  # From your image
        baseline_miss = 0.10
        baseline_power = 0.06
        
        score = (weights['cycles'] * (result['cycles'] / baseline_cycles) +
                weights['cache_miss_rate'] * (result['cache_miss_rate'] / baseline_miss) +
                weights['power'] * (result['power'] / baseline_power))
        
        return score
    
    def find_best_configs(self):
        """Find best configuration for each benchmark"""
        for benchmark in self.benchmarks:
            benchmark_results = [r for r in self.results 
                               if r['benchmark'] == benchmark and r['status'] == 'completed']
            
            if not benchmark_results:
                continue
            
            # Find configuration with lowest score
            best = min(benchmark_results, key=self.calculate_score)
            self.best_configs[benchmark] = best
            
            print(f"\nBest config for {benchmark}:")
            print(f"  Configuration: {best['config']}")
            print(f"  Cycles: {best['cycles']}")
            print(f"  Cache Miss Rate: {best['cache_miss_rate']:.4f}")
            print(f"  Power: {best['power']:.4f}")
    
    def save_results(self, filename='optimization_results.json'):
        """Save all results to file"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'all_results': self.results,
            'best_configs': self.best_configs
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults saved to {filename}")
    
    def run_optimization(self):
        """Main optimization loop"""
        print("=== BOOM Cache Configuration Optimizer ===\n")
        
        # Generate design space
        all_configs = self.generate_design_space()
        
        # Smart sampling (MicroAL-inspired)
        selected_configs = self.smart_sample_configs(all_configs, self.max_evaluations)
        print(f"Selected {len(selected_configs)} configurations to evaluate\n")
        
        # Evaluate configurations
        print("Starting evaluation...")
        self.evaluate_configs_parallel(selected_configs)
        
        # Find best configurations
        print("\n=== Finding Best Configurations ===")
        self.find_best_configs()
        
        # Save results
        self.save_results()
        
        print("\n=== Optimization Complete ===")

def main():
    explorer = DesignSpaceExplorer('design_space.json')
    explorer.run_optimization()

if __name__ == '__main__':
    main()
