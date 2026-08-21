# 📋 Experimental Matrix Coverage & Sample Imbalance Audit Report

**Generated:** `notebooks/04_experimental_audit.ipynb` | 2026-08-21 20:57:42

### 📊 High-Level Status Breakdown
- **Total Experimental Cells Planned:** `240`
- 🔴 **Missing Conditions (0 Runs):** `38` (15.8%)
- 🟡 **Partial / Interrupted Runs (<10 Runs):** `2` (0.8%)
- 🟢 **Exact Target Met (N = 10 Runs):** `200` (83.3%)
- 🔵 **Over-Sampled / Imbalanced (N > 10 Runs):** `0` (0.0%)

---

## 1. Completion Rate by Dimension

| Dimension | Total Cells | Fully Completed (N ≥ 10) | Partial (<10) | Missing (0) | Completion Rate |
|---|---|---|---|---|---|
| **2D** | 80 | 71 | 0 | 9 | 88.8% |
| **3D** | 80 | 70 | 1 | 9 | 88.8% |
| **5D** | 80 | 59 | 1 | 20 | 75.0% |

---

## 2. Sample Size Imbalance by Solver

| Solver | Category | Evaluated Cells | Missing Cells | Mean Runs (N) | Min Runs | Max Runs |
|---|---|---|---|---|---|---|
| **LLaMEA-14B / baseline** | LLaMEA-14B | 30/30 | 0 | **10.0** | 10 | 10 |
| **LLaMEA-14B / guided** | LLaMEA-14B | 29/30 | 1 | **10.0** | 10 | 10 |
| **LLaMEA-14B / thinking** | LLaMEA-14B | 30/30 | 0 | **10.0** | 10 | 10 |
| **LLaMEA-14B / vectorization** | LLaMEA-14B | 30/30 | 0 | **10.0** | 10 | 10 |
| **LLaMEA-7B / baseline** | LLaMEA-7B | 2/30 | 28 | **5.5** | 1 | 10 |
| **CMA-ES** | Classical Baseline | 27/30 | 3 | **10.0** | 10 | 10 |
| **DE** | Classical Baseline | 27/30 | 3 | **10.0** | 10 | 10 |
| **PSO** | Classical Baseline | 27/30 | 3 | **9.8** | 5 | 10 |

---

## 3. Actionable Checklist: Missing Experiments (0 Runs)

| # | Dimension | Noise Regime | Problem Name | Problem Class | Solver | Action Required |
|---|---|---|---|---|---|---|
| 1 | 2D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 2 | 2D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 3 | 2D | σ=0.0 | Rastrigin (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 4 | 2D | σ=0.0 | Gallagher (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 5 | 2D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 6 | 2D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 7 | 2D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 8 | 2D | σ=0.05 | Rastrigin (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 9 | 2D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 10 | 3D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 11 | 3D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 12 | 3D | σ=0.0 | Rastrigin (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 13 | 3D | σ=0.0 | Gallagher (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 14 | 3D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 15 | 3D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 16 | 3D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 17 | 3D | σ=0.05 | Rastrigin (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 18 | 3D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 19 | 5D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 20 | 5D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 21 | 5D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 22 | 5D | σ=0.0 | Rastrigin (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 23 | 5D | σ=0.0 | Gallagher (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 24 | 5D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 25 | 5D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 26 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 27 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **CMA-ES** | 🔴 **Execute N=10 Runs** |
| 28 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **DE** | 🔴 **Execute N=10 Runs** |
| 29 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **PSO** | 🔴 **Execute N=10 Runs** |
| 30 | 5D | σ=0.05 | Rastrigin (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 31 | 5D | σ=0.05 | Rastrigin (f15) | Multi-Modal (Global) | **CMA-ES** | 🔴 **Execute N=10 Runs** |
| 32 | 5D | σ=0.05 | Rastrigin (f15) | Multi-Modal (Global) | **DE** | 🔴 **Execute N=10 Runs** |
| 33 | 5D | σ=0.05 | Rastrigin (f15) | Multi-Modal (Global) | **PSO** | 🔴 **Execute N=10 Runs** |
| 34 | 5D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **LLaMEA-14B / guided** | 🔴 **Execute N=10 Runs** |
| 35 | 5D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 36 | 5D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **CMA-ES** | 🔴 **Execute N=10 Runs** |
| 37 | 5D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **DE** | 🔴 **Execute N=10 Runs** |
| 38 | 5D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **PSO** | 🔴 **Execute N=10 Runs** |

---

## 4. Actionable Checklist: Partial / Interrupted Experiments (< 10 Runs)

| # | Dimension | Noise Regime | Problem Name | Solver | Completed Runs | Remaining to Target (10 - N) |
|---|---|---|---|---|---|---|
| 1 | 3D | σ=0.0 | Sphere (f1) | **LLaMEA-7B / baseline** | ⚠️ 1/10 | 🟡 **Run +9 more** |
| 2 | 5D | σ=0.05 | Rosenbrock (f8) | **PSO** | ⚠️ 5/10 | 🟡 **Run +5 more** |