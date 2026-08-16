# 📊 Benchmark Statistical Summary: 2D (Noisy Mode (std = 0.05))

> **Target Dimension:** `2D` | **Noise Level:** `0.05`

## 🏆 1. Win-Loss Summary (LLaMEA vs. Classical Baselines)
- **Total Comparisons against Baselines:** `15`
- **🟢 LLaMEA Statistically Significant Wins ($p < 0.05, \hat{A}_{12} < 0.5$):** **`0`** (0.0%)
- **🔴 Classical Baselines Statistically Significant Wins ($p < 0.05, \hat{A}_{12} > 0.5$):** **`0`** (0.0%)
- **⚪ Non-Significant Differences & Exact Ties:** **`15`** (100.0%)

---
## 🌐 2. Omnibus Kruskal-Wallis H-Test (Group Differences Across All Solvers)

| Problem | Function Class | Solvers | H-Statistic | p-value | Significant Difference? |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `Sphere (f1)` | Separable | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `Discus (f11)` | High Conditioning | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `Rastrigin (f15)` | Multi-Modal (Global Structure) | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `Gallagher 101 Peaks (f21)` | Multi-Modal (Weak Structure) | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `Rosenbrock (f8)` | Low Conditioning | 4 | 3.000 | 3.92e-01 | ⚪ No |

---
## 🔬 3. Pairwise Comparisons (LLaMEA Prompt Strategies vs. Classical Baselines)

| Problem | Function Class | LLaMEA Strategy | Baseline | LLaMEA Median | Baseline Median | MW p-val | A12 Effect Size | Magnitude | Outcome |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Sphere (f1)** | Separable | **LLaMEA (Baseline)** | **CMAES** | 1.66e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  | **LLaMEA (Baseline)** | **DE** | 1.66e-06 | 7.16e-04 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **LLaMEA (Baseline)** | **PSO** | 1.66e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| **Discus (f11)** | High Conditioning | **LLaMEA (Baseline)** | **CMAES** | 7.87e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  | **LLaMEA (Baseline)** | **DE** | 7.87e-06 | 3.02e-05 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **LLaMEA (Baseline)** | **PSO** | 7.87e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| **Rastrigin (f15)** | Multi-Modal (Global Structure) | **LLaMEA (Baseline)** | **CMAES** | 1.09e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  | **LLaMEA (Baseline)** | **DE** | 1.09e-06 | 5.34e-02 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **LLaMEA (Baseline)** | **PSO** | 1.09e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak Structure) | **LLaMEA (Baseline)** | **CMAES** | 5.00e-10 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  | **LLaMEA (Baseline)** | **DE** | 5.00e-10 | 1.00e-10 | 1.00e+00 | 1.000 | Large | ⚪ DE Ahead (Non-Sig) |
|  |  | **LLaMEA (Baseline)** | **PSO** | 5.00e-10 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| **Rosenbrock (f8)** | Low Conditioning | **LLaMEA (Baseline)** | **CMAES** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  |  | **LLaMEA (Baseline)** | **DE** | 0.00e+00 | 1.06e-04 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  | **LLaMEA (Baseline)** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |

---
## ⚔️ 5. Classical Baselines Inter-Comparison (CMA-ES vs. DE vs. PSO)

| Problem | Baseline A | Baseline B | Median A | Median B | MW p-val | A12 (A < B) | Magnitude | Outcome |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Sphere (f1)** | **CMAES** | **DE** | 0.00e+00 | 7.16e-04 | 1.00e+00 | 0.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  | **CMAES** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  | **DE** | **PSO** | 7.16e-04 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| **Discus (f11)** | **CMAES** | **DE** | 0.00e+00 | 3.02e-05 | 1.00e+00 | 0.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  | **CMAES** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  | **DE** | **PSO** | 3.02e-05 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| **Rastrigin (f15)** | **CMAES** | **DE** | 0.00e+00 | 5.34e-02 | 1.00e+00 | 0.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  | **CMAES** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  | **DE** | **PSO** | 5.34e-02 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| **Gallagher 101 Peaks (f21)** | **CMAES** | **DE** | 0.00e+00 | 1.00e-10 | 1.00e+00 | 0.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  | **CMAES** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  | **DE** | **PSO** | 1.00e-10 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| **Rosenbrock (f8)** | **CMAES** | **DE** | 0.00e+00 | 1.06e-04 | 1.00e+00 | 0.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  | **CMAES** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  | **DE** | **PSO** | 1.06e-04 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |