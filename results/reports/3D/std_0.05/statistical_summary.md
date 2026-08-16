# 📊 Benchmark Statistical Summary: 3D (Noisy Mode (std = 0.05))

> **Target Dimension:** `3D` | **Noise Level:** `0.05`

## 🏆 Win-Loss Summary
- **Total Pairwise Tests ($N$):** `20`
- **🟢 LLaMEA Statistically Significant Wins ($p < 0.05, \hat{A}_{12} < 0.5$):** **`8`** (40.0%)
- **🔴 Baseline Statistically Significant Wins ($p < 0.05, \hat{A}_{12} > 0.5$):** **`1`** (5.0%)
- **⚪ Non-Significant Differences & Exact Ties:** **`11`** (55.0%)

---
## 🌐 1. Omnibus Kruskal-Wallis H-Test (Group Differences Across Solvers)

| Problem | Function Class | H-Statistic | p-value | Significant Difference? |
| :--- | :--- | :---: | :---: | :---: |
| `Sphere (f1)` | Separable | 38.397 | 9.28e-08 | 🟢 **Yes** |
| `Discus (f11)` | High Conditioning | 41.811 | 6.43e-08 | 🟢 **Yes** |
| `Rastrigin (f15)` | Multi-Modal (Global Struct) | 9.169 | 1.03e-01 | ⚪ No |
| `Gallagher 101 Peaks (f21)` | Multi-Modal (Weak Struct) | 12.462 | 2.90e-02 | 🟢 **Yes** |
| `Rosenbrock (f8)` | Low Conditioning | 20.218 | 1.14e-03 | 🟢 **Yes** |

---
## 🔬 2. Pairwise Comparisons (LLaMEA Champion vs. Baselines)

*Two-sided Mann-Whitney U tests paired with Vargha-Delaney $\hat{A}_{12}$ effect sizes (where $\hat{A}_{12} < 0.5$ indicates LLaMEA superiority).*

| Problem | Function Class | Baseline | LLaMEA Median | Baseline Median | MW p-val | $\hat{A}_{12}$ | Magnitude | Outcome |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Discus (f11)** | High Conditioning | **CMAES** | 3.13e-04 | 0.00e+00 | 2.12e-02 | 0.800 | Large | 🔴 **CMAES Wins (Sig)** |
|  |  | **DE** | 3.13e-04 | 2.28e-02 | 3.30e-04 | 0.020 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-14b-q4_k_m)** | 3.13e-04 | 1.32e-03 | 2.83e-03 | 0.100 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 3.13e-04 | 1.80e+03 | 1.20e-05 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 3.13e-04 | 3.34e-02 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
| **Rastrigin (f15)** | Multi-Modal (Global Struct) | **CMAES** | 1.99e+00 | 3.02e+00 | 1.86e-01 | 0.320 | Medium | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **DE** | 1.99e+00 | 6.40e+00 | 1.13e-02 | 0.160 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-14b-q4_k_m)** | 1.99e+00 | 7.02e-01 | 9.10e-01 | 0.480 | Negligible | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 1.99e+00 | 1.99e+00 | 3.24e-01 | 0.384 | Small | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **PSO** | 1.99e+00 | 1.49e+00 | 7.91e-01 | 0.540 | Negligible | ⚪ PSO Ahead (Non-Sig) |
| **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak Struct) | **CMAES** | 1.60e-02 | 1.09e+00 | 2.83e-03 | 0.100 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **DE** | 1.60e-02 | 8.71e-04 | 6.78e-01 | 0.560 | Negligible | ⚪ DE Ahead (Non-Sig) |
|  |  | **LLaMEA (qwen2.5-coder-14b-q4_k_m)** | 1.60e-02 | 2.29e-03 | 5.71e-01 | 0.580 | Small | ⚪ LLaMEA (qwen2.5-coder-14b-q4_k_m) Ahead (Non-Sig) |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 1.60e-02 | 6.31e-04 | 2.81e-01 | 0.625 | Small | ⚪ LLaMEA (qwen2.5-coder-7b-q4_k_m) Ahead (Non-Sig) |
|  |  | **PSO** | 1.60e-02 | 0.00e+00 | 4.67e-01 | 0.600 | Small | ⚪ PSO Ahead (Non-Sig) |
| **Rosenbrock (f8)** | Low Conditioning | **CMAES** | 3.00e-10 | 0.00e+00 | 9.68e-01 | 0.510 | Negligible | ⚪ CMAES Ahead (Non-Sig) |
|  |  | **DE** | 3.00e-10 | 1.26e-01 | 1.78e-04 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-14b-q4_k_m)** | 3.00e-10 | 1.22e+01 | 1.78e-04 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 3.00e-10 | 3.87e-01 | 1.12e-02 | 0.197 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 3.00e-10 | 3.00e-03 | 1.58e-01 | 0.310 | Medium | ⚪ LLaMEA Ahead (Non-Sig) |