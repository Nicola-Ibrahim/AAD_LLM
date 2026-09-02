# 📋 Experimental Matrix Coverage & Sample Imbalance Audit Report

**Generated:** `notebooks/04_audit.ipynb` | 2026-08-29 17:47:14

### 📊 High-Level Status Breakdown
- **Total Experimental Cells Planned:** `600`
- 🔴 **Missing Conditions (0 Runs):** `128` (21.3%)
- 🟡 **Partial / Interrupted Runs (<20 Runs):** `0` (0.0%)
- 🟢 **Exact Target Met (N = 20 Runs):** `472` (78.7%)
- 🔵 **Over-Sampled / Imbalanced (N > 20 Runs):** `0` (0.0%)

---

## 1. Completion Rate by Dimension

| Dimension | Total Cells | Fully Completed (N ≥ 20) | Partial (<20) | Missing (0) | Completion Rate |
|---|---|---|---|---|---|
| **2D** | 150 | 126 | 0 | 24 | 84.0% |
| **3D** | 150 | 137 | 0 | 13 | 91.3% |
| **5D** | 150 | 139 | 0 | 11 | 92.7% |
| **10D** | 150 | 70 | 0 | 80 | 46.7% |

---

## 2. Sample Size Imbalance by Solver

| Solver | Category | Evaluated Cells | Missing Cells | Mean Runs (N) | Min Runs | Max Runs |
|---|---|---|---|---|---|---|
| **Baseline / CMAES** | Baseline | 40/40 | 0 | **20.0** | 20 | 20 |
| **Baseline / DE** | Baseline | 40/40 | 0 | **20.0** | 20 | 20 |
| **Baseline / PSO** | Baseline | 40/40 | 0 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-14B / baseline** | Qwen2.5-Coder-14B | 40/40 | 0 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-14B / guided** | Qwen2.5-Coder-14B | 40/40 | 0 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-14B / thinking** | Qwen2.5-Coder-14B | 40/40 | 0 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-14B / vectorization** | Qwen2.5-Coder-14B | 40/40 | 0 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-3B / baseline** | Qwen2.5-Coder-3B | 21/40 | 19 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-3B / guided** | Qwen2.5-Coder-3B | 16/40 | 24 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-3B / thinking** | Qwen2.5-Coder-3B | 19/40 | 21 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-3B / vectorization** | Qwen2.5-Coder-3B | 17/40 | 23 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-7B / baseline** | Qwen2.5-Coder-7B | 30/40 | 10 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-7B / guided** | Qwen2.5-Coder-7B | 29/40 | 11 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-7B / thinking** | Qwen2.5-Coder-7B | 30/40 | 10 | **20.0** | 20 | 20 |
| **Qwen2.5-Coder-7B / vectorization** | Qwen2.5-Coder-7B | 30/40 | 10 | **20.0** | 20 | 20 |

---

## 3. Actionable Checklist: Missing Experiments (0 Runs)

| # | Dimension | Noise Regime | Problem Name | Problem Class | Solver | Action Required |
|---|---|---|---|---|---|---|
| 1 | 2D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 2 | 2D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 3 | 2D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 4 | 2D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 5 | 2D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 6 | 2D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 7 | 2D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 8 | 2D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 9 | 2D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 10 | 2D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 11 | 2D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 12 | 2D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 13 | 2D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 14 | 2D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 15 | 2D | σ=0.05 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 16 | 2D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 17 | 2D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 18 | 2D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 19 | 2D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 20 | 2D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 21 | 2D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 22 | 2D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 23 | 2D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 24 | 2D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 25 | 3D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 26 | 3D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 27 | 3D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 28 | 3D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 29 | 3D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 30 | 3D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 31 | 3D | σ=0.05 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 32 | 3D | σ=0.05 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 33 | 3D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 34 | 3D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 35 | 3D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 36 | 3D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 37 | 3D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 38 | 5D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 39 | 5D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 40 | 5D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 41 | 5D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 42 | 5D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 43 | 5D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 44 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 45 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 46 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 47 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-7B / guided** | 🔴 **Execute N=20 Runs** |
| 48 | 5D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 49 | 10D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 50 | 10D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 51 | 10D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 52 | 10D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 53 | 10D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-7B / baseline** | 🔴 **Execute N=20 Runs** |
| 54 | 10D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-7B / guided** | 🔴 **Execute N=20 Runs** |
| 55 | 10D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-7B / thinking** | 🔴 **Execute N=20 Runs** |
| 56 | 10D | σ=0.0 | Sphere (f1) | Separable | **Qwen2.5-Coder-7B / vectorization** | 🔴 **Execute N=20 Runs** |
| 57 | 10D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 58 | 10D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 59 | 10D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 60 | 10D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 61 | 10D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-7B / baseline** | 🔴 **Execute N=20 Runs** |
| 62 | 10D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-7B / guided** | 🔴 **Execute N=20 Runs** |
| 63 | 10D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-7B / thinking** | 🔴 **Execute N=20 Runs** |
| 64 | 10D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-7B / vectorization** | 🔴 **Execute N=20 Runs** |
| 65 | 10D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 66 | 10D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 67 | 10D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 68 | 10D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 69 | 10D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-7B / baseline** | 🔴 **Execute N=20 Runs** |
| 70 | 10D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-7B / guided** | 🔴 **Execute N=20 Runs** |
| 71 | 10D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-7B / thinking** | 🔴 **Execute N=20 Runs** |
| 72 | 10D | σ=0.0 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-7B / vectorization** | 🔴 **Execute N=20 Runs** |
| 73 | 10D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 74 | 10D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 75 | 10D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 76 | 10D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 77 | 10D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-7B / baseline** | 🔴 **Execute N=20 Runs** |
| 78 | 10D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-7B / guided** | 🔴 **Execute N=20 Runs** |
| 79 | 10D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-7B / thinking** | 🔴 **Execute N=20 Runs** |
| 80 | 10D | σ=0.0 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-7B / vectorization** | 🔴 **Execute N=20 Runs** |
| 81 | 10D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 82 | 10D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 83 | 10D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 84 | 10D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 85 | 10D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-7B / baseline** | 🔴 **Execute N=20 Runs** |
| 86 | 10D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-7B / guided** | 🔴 **Execute N=20 Runs** |
| 87 | 10D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-7B / thinking** | 🔴 **Execute N=20 Runs** |
| 88 | 10D | σ=0.0 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-7B / vectorization** | 🔴 **Execute N=20 Runs** |
| 89 | 10D | σ=0.05 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 90 | 10D | σ=0.05 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 91 | 10D | σ=0.05 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 92 | 10D | σ=0.05 | Sphere (f1) | Separable | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 93 | 10D | σ=0.05 | Sphere (f1) | Separable | **Qwen2.5-Coder-7B / baseline** | 🔴 **Execute N=20 Runs** |
| 94 | 10D | σ=0.05 | Sphere (f1) | Separable | **Qwen2.5-Coder-7B / guided** | 🔴 **Execute N=20 Runs** |
| 95 | 10D | σ=0.05 | Sphere (f1) | Separable | **Qwen2.5-Coder-7B / thinking** | 🔴 **Execute N=20 Runs** |
| 96 | 10D | σ=0.05 | Sphere (f1) | Separable | **Qwen2.5-Coder-7B / vectorization** | 🔴 **Execute N=20 Runs** |
| 97 | 10D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 98 | 10D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 99 | 10D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 100 | 10D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 101 | 10D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-7B / baseline** | 🔴 **Execute N=20 Runs** |
| 102 | 10D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-7B / guided** | 🔴 **Execute N=20 Runs** |
| 103 | 10D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-7B / thinking** | 🔴 **Execute N=20 Runs** |
| 104 | 10D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **Qwen2.5-Coder-7B / vectorization** | 🔴 **Execute N=20 Runs** |
| 105 | 10D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 106 | 10D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 107 | 10D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 108 | 10D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 109 | 10D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-7B / baseline** | 🔴 **Execute N=20 Runs** |
| 110 | 10D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-7B / guided** | 🔴 **Execute N=20 Runs** |
| 111 | 10D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-7B / thinking** | 🔴 **Execute N=20 Runs** |
| 112 | 10D | σ=0.05 | Discus (f11) | High Conditioning | **Qwen2.5-Coder-7B / vectorization** | 🔴 **Execute N=20 Runs** |
| 113 | 10D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 114 | 10D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 115 | 10D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 116 | 10D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 117 | 10D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-7B / baseline** | 🔴 **Execute N=20 Runs** |
| 118 | 10D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-7B / guided** | 🔴 **Execute N=20 Runs** |
| 119 | 10D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-7B / thinking** | 🔴 **Execute N=20 Runs** |
| 120 | 10D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **Qwen2.5-Coder-7B / vectorization** | 🔴 **Execute N=20 Runs** |
| 121 | 10D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / baseline** | 🔴 **Execute N=20 Runs** |
| 122 | 10D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / guided** | 🔴 **Execute N=20 Runs** |
| 123 | 10D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / thinking** | 🔴 **Execute N=20 Runs** |
| 124 | 10D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-3B / vectorization** | 🔴 **Execute N=20 Runs** |
| 125 | 10D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-7B / baseline** | 🔴 **Execute N=20 Runs** |
| 126 | 10D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-7B / guided** | 🔴 **Execute N=20 Runs** |
| 127 | 10D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-7B / thinking** | 🔴 **Execute N=20 Runs** |
| 128 | 10D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **Qwen2.5-Coder-7B / vectorization** | 🔴 **Execute N=20 Runs** |

---

## 4. Actionable Checklist: Partial / Interrupted Experiments (< 20 Runs)

🎉 **No partial runs detected!**
