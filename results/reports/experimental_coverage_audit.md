# 📋 Experimental Matrix Coverage & Sample Imbalance Audit Report

**Generated:** `notebooks/06_experimental_audit.ipynb` | 2026-08-23 14:33:36

### 📊 High-Level Status Breakdown
- **Total Experimental Cells Planned:** `300`
- 🔴 **Missing Conditions (0 Runs):** `152` (50.7%)
- 🟡 **Partial / Interrupted Runs (<10 Runs):** `3` (1.0%)
- 🟢 **Exact Target Met (N = 10 Runs):** `145` (48.3%)
- 🔵 **Over-Sampled / Imbalanced (N > 10 Runs):** `0` (0.0%)

---

## 1. Completion Rate by Dimension

| Dimension | Total Cells | Fully Completed (N ≥ 10) | Partial (<10) | Missing (0) | Completion Rate |
|---|---|---|---|---|---|
| **2D** | 100 | 53 | 0 | 47 | 53.0% |
| **3D** | 100 | 47 | 3 | 50 | 50.0% |
| **5D** | 100 | 45 | 0 | 55 | 45.0% |

---

## 2. Sample Size Imbalance by Solver

| Solver | Category | Evaluated Cells | Missing Cells | Mean Runs (N) | Min Runs | Max Runs |
|---|---|---|---|---|---|---|
| **LLaMEA-14B / baseline** | LLaMEA-14B | 24/30 | 6 | **10.0** | 10 | 10 |
| **LLaMEA-14B / guided** | LLaMEA-14B | 23/30 | 7 | **10.0** | 10 | 10 |
| **LLaMEA-14B / thinking** | LLaMEA-14B | 21/30 | 9 | **9.3** | 2 | 10 |
| **LLaMEA-14B / vectorization** | LLaMEA-14B | 20/30 | 10 | **10.0** | 10 | 10 |
| **LLaMEA-7B / baseline** | LLaMEA-7B | 0/30 | 30 | **0.0** | 0 | 0 |
| **LLaMEA-7B / guided** | LLaMEA-7B | 0/30 | 30 | **0.0** | 0 | 0 |
| **LLaMEA-7B / thinking** | LLaMEA-7B | 0/30 | 30 | **0.0** | 0 | 0 |
| **LLaMEA-7B / vectorization** | LLaMEA-7B | 0/30 | 30 | **0.0** | 0 | 0 |
| **CMA-ES** | Classical Baseline | 30/30 | 0 | **10.0** | 10 | 10 |
| **DE** | Classical Baseline | 30/30 | 0 | **10.0** | 10 | 10 |

---

## 3. Actionable Checklist: Missing Experiments (0 Runs)

| # | Dimension | Noise Regime | Problem Name | Problem Class | Solver | Action Required |
|---|---|---|---|---|---|---|
| 1 | 2D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 2 | 2D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 3 | 2D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 4 | 2D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 5 | 2D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 6 | 2D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 7 | 2D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 8 | 2D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 9 | 2D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 10 | 2D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 11 | 2D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 12 | 2D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 13 | 2D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 14 | 2D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 15 | 2D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 16 | 2D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 17 | 2D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / baseline** | 🔴 **Execute N=10 Runs** |
| 18 | 2D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / guided** | 🔴 **Execute N=10 Runs** |
| 19 | 2D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / thinking** | 🔴 **Execute N=10 Runs** |
| 20 | 2D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / vectorization** | 🔴 **Execute N=10 Runs** |
| 21 | 2D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 22 | 2D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 23 | 2D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 24 | 2D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 25 | 2D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 26 | 2D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 27 | 2D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 28 | 2D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 29 | 2D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 30 | 2D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 31 | 2D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 32 | 2D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 33 | 2D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 34 | 2D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 35 | 2D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 36 | 2D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 37 | 2D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 38 | 2D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 39 | 2D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 40 | 2D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 41 | 2D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / guided** | 🔴 **Execute N=10 Runs** |
| 42 | 2D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / thinking** | 🔴 **Execute N=10 Runs** |
| 43 | 2D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / vectorization** | 🔴 **Execute N=10 Runs** |
| 44 | 2D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 45 | 2D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 46 | 2D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 47 | 2D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 48 | 3D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 49 | 3D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 50 | 3D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 51 | 3D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 52 | 3D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 53 | 3D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 54 | 3D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 55 | 3D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 56 | 3D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 57 | 3D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 58 | 3D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 59 | 3D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 60 | 3D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-14B / vectorization** | 🔴 **Execute N=10 Runs** |
| 61 | 3D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 62 | 3D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 63 | 3D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 64 | 3D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 65 | 3D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / baseline** | 🔴 **Execute N=10 Runs** |
| 66 | 3D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / thinking** | 🔴 **Execute N=10 Runs** |
| 67 | 3D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / vectorization** | 🔴 **Execute N=10 Runs** |
| 68 | 3D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 69 | 3D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 70 | 3D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 71 | 3D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 72 | 3D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 73 | 3D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 74 | 3D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 75 | 3D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 76 | 3D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 77 | 3D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 78 | 3D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 79 | 3D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 80 | 3D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 81 | 3D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 82 | 3D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 83 | 3D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 84 | 3D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-14B / thinking** | 🔴 **Execute N=10 Runs** |
| 85 | 3D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-14B / vectorization** | 🔴 **Execute N=10 Runs** |
| 86 | 3D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 87 | 3D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 88 | 3D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 89 | 3D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 90 | 3D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / baseline** | 🔴 **Execute N=10 Runs** |
| 91 | 3D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / guided** | 🔴 **Execute N=10 Runs** |
| 92 | 3D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / thinking** | 🔴 **Execute N=10 Runs** |
| 93 | 3D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / vectorization** | 🔴 **Execute N=10 Runs** |
| 94 | 3D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 95 | 3D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 96 | 3D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 97 | 3D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 98 | 5D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 99 | 5D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 100 | 5D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 101 | 5D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 102 | 5D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 103 | 5D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 104 | 5D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 105 | 5D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 106 | 5D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 107 | 5D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 108 | 5D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 109 | 5D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 110 | 5D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-14B / baseline** | 🔴 **Execute N=10 Runs** |
| 111 | 5D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-14B / guided** | 🔴 **Execute N=10 Runs** |
| 112 | 5D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-14B / thinking** | 🔴 **Execute N=10 Runs** |
| 113 | 5D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-14B / vectorization** | 🔴 **Execute N=10 Runs** |
| 114 | 5D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 115 | 5D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 116 | 5D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 117 | 5D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 118 | 5D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / guided** | 🔴 **Execute N=10 Runs** |
| 119 | 5D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / thinking** | 🔴 **Execute N=10 Runs** |
| 120 | 5D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / vectorization** | 🔴 **Execute N=10 Runs** |
| 121 | 5D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 122 | 5D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 123 | 5D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 124 | 5D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 125 | 5D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 126 | 5D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 127 | 5D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 128 | 5D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 129 | 5D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 130 | 5D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 131 | 5D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 132 | 5D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 133 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 134 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 135 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 136 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 137 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-14B / baseline** | 🔴 **Execute N=10 Runs** |
| 138 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-14B / guided** | 🔴 **Execute N=10 Runs** |
| 139 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-14B / thinking** | 🔴 **Execute N=10 Runs** |
| 140 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-14B / vectorization** | 🔴 **Execute N=10 Runs** |
| 141 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 142 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 143 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 144 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |
| 145 | 5D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / baseline** | 🔴 **Execute N=10 Runs** |
| 146 | 5D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / guided** | 🔴 **Execute N=10 Runs** |
| 147 | 5D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / thinking** | 🔴 **Execute N=10 Runs** |
| 148 | 5D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / vectorization** | 🔴 **Execute N=10 Runs** |
| 149 | 5D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 150 | 5D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 151 | 5D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / thinking** | 🔴 **Execute N=10 Runs** |
| 152 | 5D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-7B / vectorization** | 🔴 **Execute N=10 Runs** |

---

## 4. Actionable Checklist: Partial / Interrupted Experiments (< 10 Runs)

| # | Dimension | Noise Regime | Problem Name | Solver | Completed Runs | Remaining to Target (10 - N) |
|---|---|---|---|---|---|---|
| 1 | 3D | σ=0.0 | Discus (f11) | **LLaMEA-14B / thinking** | ⚠️ 6/10 | 🟡 **Run +4 more** |
| 2 | 3D | σ=0.0 | Rastrigin Multi-Modal (f15) | **LLaMEA-14B / thinking** | ⚠️ 2/10 | 🟡 **Run +8 more** |
| 3 | 3D | σ=0.05 | Discus (f11) | **LLaMEA-14B / thinking** | ⚠️ 7/10 | 🟡 **Run +3 more** |