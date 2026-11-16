# Bayesian Optimization for BOOM Cache and Microarchitecture Design-Space Exploration

Course project (Jack Wilson, Muhammad Athar, Tolu Kolade). We search the configuration space of the
**Berkeley Out-of-Order Machine (BOOM)** RISC-V core in Chipyard with **Bayesian optimization**: a Gaussian
Process (RBF kernel) with Expected Improvement acquisition. The search covers L1 caches plus issue width, ROB
size and LSQ size. Each candidate is built from generated Scala config, simulated in Verilator on six riscv-tests
benchmarks, and measured with **Hardware Performance Monitor (HPM) counters** (cycles, instructions, I$/D$ misses, TLB misses).

The full write-up is in [`FinalReport.pdf`](FinalReport.pdf).

## Design space (5,184 configurations)

| Parameter | Values |
|---|---|
| L1 I-cache size / ways | 8, 16, 32 KB / 2, 4, 8 |
| L1 D-cache size / ways | 8, 16, 32 KB / 2, 4, 8 |
| Issue width | 1, 2, 3, 4 (sets fetch/decode width and issue queues) |
| ROB entries | 32, 64, 96, 128 |
| LSQ entries | 8, 16, 24, 32 |

Benchmarks: `dhrystone`, `multiplication`, `qsort`, `aes`, `convolution`, `sha256`. Objective: total cycles across all six.

## Results

The optimizer ran **15 iterations (0.29% of the design space)**. Top four configurations:

| Rank | I$ sets×ways | D$ sets×ways | Issue | ROB | LSQ | Total cycles | Avg IPC | I$ MPKI | D$ MPKI |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **16×4** | **64×4** | **4** | **64** | **16** | **732,661** | **2.391** | **0.039** | **0.155** |
| 2 | 16×4 | 32×2 | 3 | 96 | 8 | 973,079 | 1.801 | 0.040 | 0.327 |
| 3 | 64×8 | 64×8 | 1 | 32 | 32 | 1,925,098 | 0.879 | 0.033 | 0.083 |
| 4 | 64×8 | 64×2 | 1 | 32 | 32 | 1,927,261 | 0.878 | 0.033 | 0.233 |

The best configuration uses **62% fewer cycles** than the weakest one evaluated. Speedups over baseline per benchmark:
SHA256 4.0×, AES 2.99×, Dhrystone 2.82×, Convolution ~2.62×, Multiplication ~1.63×, Qsort 0.91× (slower).

Key findings:
- **Issue width dominates.** 4-issue beats 1-issue by 2.6× even with an 8× smaller I-cache.
- **Small I-caches are enough.** A 4 KB I-cache stays below 0.04 MPKI.
- **D-cache misses are mostly conflict misses.** The 32-set D-cache missed 111% more than the 64-set one.

## Repository layout

| Path | What it is |
|---|---|
| `design_space.json` | Cache parameter ranges, benchmarks, metric weights, Chipyard path |
| `boom_optimizer.py` | Early design-space explorer: enumerates cache configs and samples a diverse subset (MicroAL-style) |
| `test_config.py` | Tests one cache configuration: rewrites the Scala config, runs all benchmarks in Verilator, saves `test_results_*.json` |
| `extract_metrics.py` | Parses cycles, instructions and pass/fail from a simulation `.out` file |
| `run_vlsi_flow.sh` | Simulation and metric-extraction flow for one config + benchmark |
| `helper.sh` | Wrapper: `status`, `build`, `test`, `optimize`, `results`, `clean` |
| `Makefile`, `build/`, `riscv_bins/` | Cross-compiles benchmarks with `riscv64-unknown-elf-gcc`; compiled binaries |
| `test_results_64x2_32x8.json` | Sample single-configuration run |

## Reproduce

**Environment:** [Chipyard](https://github.com/ucb-bar/chipyard) with Verilator and the RISC-V toolchain
(`source <chipyard>/env.sh`), plus Python 3 with scikit-learn and scipy. The scripts rewrite the
`WithL1ICacheSets/Ways` and `WithL1DCacheSets/Ways` lines of the target config in
`generators/chipyard/src/main/scala/config/` and keep a `.backup`.

```bash
export CHIPYARD_PATH=/path/to/chipyard   # also set "chipyard_path" in design_space.json
./helper.sh status                       # check toolchain, path and binaries
./helper.sh test 64,2,32,8               # one config: I$ sets,ways,D$ sets,ways
./helper.sh optimize                     # run the optimizer -> optimization_results.json
```
