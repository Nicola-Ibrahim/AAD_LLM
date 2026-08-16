# 📊 Benchmark Statistical Summary: 3D (Clean Mode (std = 0.0))

> **Target Dimension:** `3D` | **Noise Level:** `0.0`

## 🏆 Win-Loss Summary
- **Total Pairwise Tests ($N$):** `25`
- **🟢 LLaMEA Statistically Significant Wins ($p < 0.05, \hat{A}_{12} < 0.5$):** **`8`** (32.0%)
- **🔴 Baseline Statistically Significant Wins ($p < 0.05, \hat{A}_{12} > 0.5$):** **`5`** (20.0%)
- **⚪ Non-Significant Differences & Exact Ties:** **`12`** (48.0%)

---
## 🌐 1. Omnibus Kruskal-Wallis H-Test (Group Differences Across Solvers)

| Problem | Function Class | H-Statistic | p-value | Significant Difference? |
| :--- | :--- | :---: | :---: | :---: |
| `Sphere (f1)` | Separable | 35.327 | 1.29e-06 | 🟢 **Yes** |
| `Discus (f11)` | High Conditioning | 57.330 | 4.32e-11 | 🟢 **Yes** |
| `Rastrigin (f15)` | Multi-Modal (Global Struct) | 40.424 | 1.23e-07 | 🟢 **Yes** |
| `Gallagher 101 Peaks (f21)` | Multi-Modal (Weak Struct) | 23.844 | 2.33e-04 | 🟢 **Yes** |
| `Rosenbrock (f8)` | Low Conditioning | 57.863 | 3.36e-11 | 🟢 **Yes** |

---
## 🔬 2. Pairwise Comparisons (LLaMEA Champion vs. Baselines)

*Two-sided Mann-Whitney U tests paired with Vargha-Delaney $\hat{A}_{12}$ effect sizes (where $\hat{A}_{12} < 0.5$ indicates LLaMEA superiority).*

| Problem | Function Class | Baseline | LLaMEA Median | Baseline Median | MW p-val | $\hat{A}_{12}$ | Magnitude | Outcome |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Sphere (f1)** | Separable | **CMAES** | 0.00e+00 | 0.00e+00 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
|  |  | **DE** | 0.00e+00 | 0.00e+00 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
|  |  | **LLaMEA (qwen2.5-coder-14b-q4_k_m)** | 0.00e+00 | 0.00e+00 | 3.68e-01 | 0.450 | Negligible | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 0.00e+00 | 7.91e-06 | 1.71e-03 | 0.175 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 0.00e+00 | 0.00e+00 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
| **Discus (f11)** | High Conditioning | **CMAES** | 0.00e+00 | 0.00e+00 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
|  |  | **DE** | 0.00e+00 | 5.13e-03 | 6.39e-05 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-14b-q4_k_m)** | 0.00e+00 | 9.86e-07 | 1.49e-02 | 0.250 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 0.00e+00 | 1.90e+05 | 8.19e-06 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 0.00e+00 | 0.00e+00 | 1.00e+00 | 0.500 | Negligible | ⚪ Exact Tie |
| **Rastrigin (f15)** | Multi-Modal (Global Struct) | **CMAES** | 3.29e-02 | 1.99e+00 | 1.68e-04 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **DE** | 3.29e-02 | 2.49e+00 | 2.82e-03 | 0.100 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-14b-q4_k_m)** | 3.29e-02 | 8.05e+01 | 1.83e-04 | 0.000 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 3.29e-02 | 9.17e+01 | 1.77e-05 | 0.005 | Large | 🟢 **LLaMEA Wins (Sig)** |
|  |  | **PSO** | 3.29e-02 | 9.95e-01 | 1.39e-01 | 0.300 | Medium | ⚪ LLaMEA Ahead (Non-Sig) |
| **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak Struct) | **CMAES** | 1.94e+00 | 1.40e+00 | 1.61e-01 | 0.690 | Medium | ⚪ CMAES Ahead (Non-Sig) |
|  |  | **DE** | 1.94e+00 | 4.57e-08 | 2.20e-03 | 0.910 | Large | 🔴 **DE Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-14b-q4_k_m)** | 1.94e+00 | 4.84e+00 | 3.07e-01 | 0.360 | Medium | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 1.94e+00 | 4.16e-02 | 1.64e-02 | 0.775 | Large | 🔴 **LLaMEA (qwen2.5-coder-7b-q4_k_m) Wins (Sig)** |
|  |  | **PSO** | 1.94e+00 | 6.92e-01 | 4.42e-03 | 0.880 | Large | 🔴 **PSO Wins (Sig)** |
| **Rosenbrock (f8)** | Low Conditioning | **CMAES** | 7.31e+03 | 0.00e+00 | 6.39e-05 | 1.000 | Large | 🔴 **CMAES Wins (Sig)** |
|  |  | **DE** | 7.31e+03 | 3.35e-09 | 1.82e-04 | 1.000 | Large | 🔴 **DE Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-14b-q4_k_m)** | 7.31e+03 | 1.32e+02 | 9.11e-03 | 0.850 | Large | 🔴 **LLaMEA (qwen2.5-coder-14b-q4_k_m) Wins (Sig)** |
|  |  | **LLaMEA (qwen2.5-coder-7b-q4_k_m)** | 7.31e+03 | 5.37e+01 | 7.78e-03 | 0.805 | Large | 🔴 **LLaMEA (qwen2.5-coder-7b-q4_k_m) Wins (Sig)** |
|  |  | **PSO** | 7.31e+03 | 0.00e+00 | 6.39e-05 | 1.000 | Large | 🔴 **PSO Wins (Sig)** |