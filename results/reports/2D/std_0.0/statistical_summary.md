# 📊 Benchmark Statistical Summary: 2D (Clean Mode (std = 0.0))

> **Target Dimension:** `2D` | **Noise Level:** `0.0`

## 🏆 Win-Loss Summary
- **Total Pairwise Tests ($N$):** `20`
- **🟢 LLaMEA Statistically Significant Wins ($p < 0.05, \hat{A}_{12} < 0.5$):** **`6`** (30.0%)
- **🔴 Baseline Statistically Significant Wins ($p < 0.05, \hat{A}_{12} > 0.5$):** **`4`** (20.0%)
- **⚪ Non-Significant Differences & Exact Ties:** **`10`** (50.0%)

---
## 🌐 1. Omnibus Kruskal-Wallis H-Test (Group Differences Across Solvers)

| Problem | Function Class | H-Statistic | p-value | Significant Difference? |
| :--- | :--- | :---: | :---: | :---: |
| `Sphere (f1)` | Separable | 48.205 | 8.55e-10 | 🟢 **Yes** |
| `Discus (f11)` | High Conditioning | 35.248 | 4.13e-07 | 🟢 **Yes** |
| `Rastrigin (f15)` | Multi-Modal (Global Struct) | 27.268 | 1.75e-05 | 🟢 **Yes** |
| `Gallagher 101 Peaks (f21)` | Multi-Modal (Weak Struct) | 9.735 | 4.51e-02 | 🟢 **Yes** |
| `Rosenbrock (f8)` | Low Conditioning | 41.576 | 2.04e-08 | 🟢 **Yes** |

---
## 🔬 2. Pairwise Comparisons (LLaMEA Champion vs. Baselines)

*Two-sided Mann-Whitney U tests paired with Vargha-Delaney $\hat{A}_{12}$ effect sizes (where $\hat{A}_{12} < 0.5$ indicates LLaMEA superiority).*

| Problem | Function Class | Baseline | LLaMEA Median | Baseline Median | MW p-val | $\hat{A}_{12}$ | Magnitude | Outcome |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Sphere (f1)** | Separable | **CMAES** | 0.00e+00 | 0.00e+00 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
|  |  | **DE** | 0.00e+00 | 0.00e+00 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 0.00e+00 | 1.55e+00 | 6.39e-05 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 0.00e+00 | 0.00e+00 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
| **Discus (f11)** | High Conditioning | **CMAES** | 0.00e+00 | 0.00e+00 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
|  |  | **DE** | 0.00e+00 | 1.13e-03 | 6.39e-05 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 0.00e+00 | 1.47e+01 | 6.39e-05 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 0.00e+00 | 0.00e+00 | 7.67e-02 | 0.350 | Medium | ⚪ LLaMEA Ahead (Non-Sig) |
| **Rastrigin (f15)** | Multi-Modal (Global Struct) | **CMAES** | 5.25e-03 | 1.53e+00 | 2.57e-02 | 0.200 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **DE** | 5.25e-03 | 9.95e-01 | 1.40e-01 | 0.300 | Medium | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 5.25e-03 | 1.95e+00 | 1.14e-02 | 0.210 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 5.25e-03 | 0.00e+00 | 6.39e-05 | 1.000 | Large | 🔴 **PSO Wins (Sig)** |
| **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak Struct) | **CMAES** | 9.02e-01 | 4.62e-01 | 3.32e-01 | 0.625 | Small | ⚪ CMAES Ahead (Non-Sig) |
|  |  | **DE** | 9.02e-01 | 9.81e-07 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 9.02e-01 | 2.78e+00 | 2.27e-02 | 0.200 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 9.02e-01 | 3.46e-01 | 3.31e-01 | 0.625 | Small | ⚪ PSO Ahead (Non-Sig) |
| **Rosenbrock (f8)** | Low Conditioning | **CMAES** | 8.47e+03 | 0.00e+00 | 5.51e-05 | 1.000 | Large | 🔴 **CMAES Wins (Sig)** |
|  |  | **DE** | 8.47e+03 | 4.00e-10 | 1.59e-04 | 1.000 | Large | 🔴 **DE Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 8.47e+03 | 7.74e+01 | 3.60e-03 | 0.885 | Large | 🔴 **LLaMEA (qwen2.5-coder-7b-q4_k_m) Wins (Sig)** |
|  |  | **PSO** | 8.47e+03 | 0.00e+00 | 5.51e-05 | 1.000 | Large | 🔴 **PSO Wins (Sig)** |