# 📊 Benchmark Statistical Summary: 2D (Noisy Mode (std = 0.05))

> **Target Dimension:** `2D` | **Noise Level:** `0.05`

## 🏆 Win-Loss Summary
- **Total Pairwise Tests ($N$):** `20`
- **🟢 LLaMEA Statistically Significant Wins ($p < 0.05, \hat{A}_{12} < 0.5$):** **`8`** (40.0%)
- **🔴 Baseline Statistically Significant Wins ($p < 0.05, \hat{A}_{12} > 0.5$):** **`4`** (20.0%)
- **⚪ Non-Significant Differences & Exact Ties:** **`8`** (40.0%)

---
## 🌐 1. Omnibus Kruskal-Wallis H-Test (Group Differences Across Solvers)

| Problem | Function Class | H-Statistic | p-value | Significant Difference? |
| :--- | :--- | :---: | :---: | :---: |
| `Sphere (f1)` | Separable | 37.765 | 1.25e-07 | 🟢 **Yes** |
| `Discus (f11)` | High Conditioning | 16.010 | 3.01e-03 | 🟢 **Yes** |
| `Rastrigin (f15)` | Multi-Modal (Global Struct) | 41.650 | 1.97e-08 | 🟢 **Yes** |
| `Gallagher 101 Peaks (f21)` | Multi-Modal (Weak Struct) | 10.627 | 3.11e-02 | 🟢 **Yes** |
| `Rosenbrock (f8)` | Low Conditioning | 45.538 | 3.07e-09 | 🟢 **Yes** |

---
## 🔬 2. Pairwise Comparisons (LLaMEA Champion vs. Baselines)

*Two-sided Mann-Whitney U tests paired with Vargha-Delaney $\hat{A}_{12}$ effect sizes (where $\hat{A}_{12} < 0.5$ indicates LLaMEA superiority).*

| Problem | Function Class | Baseline | LLaMEA Median | Baseline Median | MW p-val | $\hat{A}_{12}$ | Magnitude | Outcome |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Sphere (f1)** | Separable | **CMAES** | 2.17e-05 | 0.00e+00 | 6.39e-05 | 1.000 | Large | 🔴 **CMAES Wins (Sig)** |
|  |  | **DE** | 2.17e-05 | 3.67e-03 | 1.83e-04 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 2.17e-05 | 2.60e-09 | 5.39e-02 | 0.767 | Large | ⚪ LLaMEA (qwen2.5-coder-7b-q4_k_m) Ahead (Non-Sig) |
|  |  | **PSO** | 2.17e-05 | 0.00e+00 | 6.39e-05 | 1.000 | Large | 🔴 **PSO Wins (Sig)** |
| **Discus (f11)** | High Conditioning | **CMAES** | 3.92e-05 | 0.00e+00 | 4.67e-01 | 0.600 | Small | ⚪ CMAES Ahead (Non-Sig) |
|  |  | **DE** | 3.92e-05 | 5.85e-03 | 1.83e-04 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 3.92e-05 | 2.14e+00 | 7.69e-04 | 0.050 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 3.92e-05 | 0.00e+00 | 2.12e-02 | 0.800 | Large | 🔴 **PSO Wins (Sig)** |
| **Rastrigin (f15)** | Multi-Modal (Global Struct) | **CMAES** | 4.97e-01 | 1.34e+00 | 1.62e-01 | 0.310 | Medium | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **DE** | 4.97e-01 | 2.35e+00 | 9.11e-03 | 0.150 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 4.97e-01 | 2.29e+01 | 1.20e-05 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 4.97e-01 | 0.00e+00 | 9.67e-03 | 0.840 | Large | 🔴 **PSO Wins (Sig)** |
| **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak Struct) | **CMAES** | 6.65e-07 | 6.72e-02 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
|  |  | **DE** | 6.65e-07 | 1.00e-05 | 3.12e-02 | 0.210 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 6.65e-07 | 1.99e+00 | 1.40e-01 | 0.300 | Medium | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **PSO** | 6.65e-07 | 0.00e+00 | 1.32e-01 | 0.700 | Medium | ⚪ PSO Ahead (Non-Sig) |
| **Rosenbrock (f8)** | Low Conditioning | **CMAES** | 0.00e+00 | 0.00e+00 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
|  |  | **DE** | 0.00e+00 | 2.36e-02 | 6.39e-05 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 0.00e+00 | 7.21e+00 | 6.39e-05 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 0.00e+00 | 0.00e+00 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |