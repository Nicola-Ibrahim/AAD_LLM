# 📋 Experimental Matrix Coverage & Sample Imbalance Audit Report

**Generated:** `notebooks/06_experimental_audit.ipynb` | 2026-08-24 22:37:08

### 📊 High-Level Status Breakdown
- **Total Experimental Cells Planned:** `330`
- 🔴 **Missing Conditions (0 Runs):** `2` (0.6%)
- 🟡 **Partial / Interrupted Runs (<10 Runs):** `0` (0.0%)
- 🟢 **Exact Target Met (N = 10 Runs):** `328` (99.4%)
- 🔵 **Over-Sampled / Imbalanced (N > 10 Runs):** `0` (0.0%)

---

## 1. Completion Rate by Dimension

| Dimension | Total Cells | Fully Completed (N ≥ 10) | Partial (<10) | Missing (0) | Completion Rate |
|---|---|---|---|---|---|
| **2D** | 110 | 110 | 0 | 0 | 100.0% |
| **3D** | 110 | 110 | 0 | 0 | 100.0% |
| **5D** | 110 | 108 | 0 | 2 | 98.2% |

---

## 2. Sample Size Imbalance by Solver

| Solver | Category | Evaluated Cells | Missing Cells | Mean Runs (N) | Min Runs | Max Runs |
|---|---|---|---|---|---|---|
| **Baseline / CMAES** | Classical Baseline | 30/30 | 0 | **10.0** | 10 | 10 |
| **Baseline / DE** | Classical Baseline | 30/30 | 0 | **10.0** | 10 | 10 |
| **Baseline / PSO** | Classical Baseline | 30/30 | 0 | **10.0** | 10 | 10 |
| **LLaMEA-14B / baseline** | LLaMEA-14B | 30/30 | 0 | **10.0** | 10 | 10 |
| **LLaMEA-14B / guided** | LLaMEA-14B | 29/30 | 1 | **10.0** | 10 | 10 |
| **LLaMEA-14B / thinking** | LLaMEA-14B | 30/30 | 0 | **10.0** | 10 | 10 |
| **LLaMEA-14B / vectorization** | LLaMEA-14B | 30/30 | 0 | **10.0** | 10 | 10 |
| **LLaMEA-7B / baseline** | LLaMEA-7B | 30/30 | 0 | **10.0** | 10 | 10 |
| **LLaMEA-7B / guided** | LLaMEA-7B | 29/30 | 1 | **10.0** | 10 | 10 |
| **LLaMEA-7B / thinking** | LLaMEA-7B | 30/30 | 0 | **10.0** | 10 | 10 |
| **LLaMEA-7B / vectorization** | LLaMEA-7B | 30/30 | 0 | **10.0** | 10 | 10 |

---

## 3. Actionable Checklist: Missing Experiments (0 Runs)

| # | Dimension | Noise Regime | Problem Name | Problem Class | Solver | Action Required |
|---|---|---|---|---|---|---|
| 1 | 5D | σ=0.05 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | **LLaMEA-7B / guided** | 🔴 **Execute N=10 Runs** |
| 2 | 5D | σ=0.05 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | **LLaMEA-14B / guided** | 🔴 **Execute N=10 Runs** |

---

## 4. Actionable Checklist: Partial / Interrupted Experiments (< 10 Runs)

🎉 **No partial runs detected!**
