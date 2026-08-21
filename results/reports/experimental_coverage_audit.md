# 📋 Experimental Matrix Coverage & Sample Imbalance Audit Report

**Generated:** `notebooks/04_experimental_audit.ipynb` | 2026-08-21 16:32:06

### 📊 High-Level Status Breakdown
- **Total Experimental Cells Planned:** `240`
- 🔴 **Missing Conditions (0 Runs):** `21` (8.8%)
- 🟡 **Partial / Interrupted Runs (<10 Runs):** `2` (0.8%)
- 🟢 **Exact Target Met (N = 10 Runs):** `175` (72.9%)
- 🔵 **Over-Sampled / Imbalanced (N > 10 Runs):** `42` (17.5%)

---

## 1. Completion Rate by Dimension

| Dimension | Total Cells | Fully Completed (N ≥ 10) | Partial (<10) | Missing (0) | Completion Rate |
|---|---|---|---|---|---|
| **2D** | 80 | 79 | 1 | 0 | 100.0% |
| **3D** | 80 | 79 | 0 | 1 | 98.8% |
| **5D** | 80 | 59 | 1 | 20 | 75.0% |

---

## 2. Sample Size Imbalance by Solver

| Solver | Category | Evaluated Cells | Missing Cells | Mean Runs (N) | Min Runs | Max Runs |
|---|---|---|---|---|---|---|
| **LLaMEA-14B / baseline** | LLaMEA-14B | 30/30 | 0 | **48.8** | 33 | 66 |
| **LLaMEA-14B / guided** | LLaMEA-14B | 28/30 | 2 | **10.0** | 10 | 10 |
| **LLaMEA-14B / thinking** | LLaMEA-14B | 30/30 | 0 | **10.0** | 10 | 10 |
| **LLaMEA-14B / vectorization** | LLaMEA-14B | 30/30 | 0 | **10.0** | 10 | 10 |
| **LLaMEA-7B / baseline** | LLaMEA-7B | 20/30 | 10 | **15.7** | 9 | 20 |
| **CMA-ES** | Classical Baseline | 27/30 | 3 | **10.0** | 10 | 10 |
| **DE** | Classical Baseline | 27/30 | 3 | **10.0** | 10 | 10 |
| **PSO** | Classical Baseline | 27/30 | 3 | **9.8** | 5 | 10 |

---

## 3. Actionable Checklist: Missing Experiments (0 Runs)

| # | Dimension | Noise Regime | Problem Name | Problem Class | Solver | Action Required |
|---|---|---|---|---|---|---|
| 1 | 3D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **LLaMEA-14B / guided** | 🔴 **Execute N=10 Runs** |
| 2 | 5D | σ=0.0 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 3 | 5D | σ=0.0 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 4 | 5D | σ=0.0 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 5 | 5D | σ=0.0 | Rastrigin (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 6 | 5D | σ=0.0 | Gallagher (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 7 | 5D | σ=0.05 | Sphere (f1) | Separable | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 8 | 5D | σ=0.05 | Rosenbrock (f8) | Low Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 9 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 10 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **CMA-ES** | 🔴 **Execute N=10 Runs** |
| 11 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **DE** | 🔴 **Execute N=10 Runs** |
| 12 | 5D | σ=0.05 | Discus (f11) | High Conditioning | **PSO** | 🔴 **Execute N=10 Runs** |
| 13 | 5D | σ=0.05 | Rastrigin (f15) | Multi-Modal (Global) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 14 | 5D | σ=0.05 | Rastrigin (f15) | Multi-Modal (Global) | **CMA-ES** | 🔴 **Execute N=10 Runs** |
| 15 | 5D | σ=0.05 | Rastrigin (f15) | Multi-Modal (Global) | **DE** | 🔴 **Execute N=10 Runs** |
| 16 | 5D | σ=0.05 | Rastrigin (f15) | Multi-Modal (Global) | **PSO** | 🔴 **Execute N=10 Runs** |
| 17 | 5D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **LLaMEA-14B / guided** | 🔴 **Execute N=10 Runs** |
| 18 | 5D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **LLaMEA-7B / baseline** | 🔴 **Execute N=10 Runs** |
| 19 | 5D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **CMA-ES** | 🔴 **Execute N=10 Runs** |
| 20 | 5D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **DE** | 🔴 **Execute N=10 Runs** |
| 21 | 5D | σ=0.05 | Gallagher (f21) | Multi-Modal (Weak) | **PSO** | 🔴 **Execute N=10 Runs** |

---

## 4. Actionable Checklist: Partial / Interrupted Experiments (< 10 Runs)

| # | Dimension | Noise Regime | Problem Name | Solver | Completed Runs | Remaining to Target (10 - N) |
|---|---|---|---|---|---|---|
| 1 | 2D | σ=0.05 | Sphere (f1) | **LLaMEA-7B / baseline** | ⚠️ 9/10 | 🟡 **Run +1 more** |
| 2 | 5D | σ=0.05 | Rosenbrock (f8) | **PSO** | ⚠️ 5/10 | 🟡 **Run +5 more** |