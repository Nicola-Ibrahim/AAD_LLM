# 📊 Comprehensive Benchmark & Statistical Analysis Report

> **Master Roll-Up Report** evaluating **LLaMEA Prompt Strategies** against classical optimizers (**CMA-ES**, **DE**, **PSO**).

## 🏆 1. Executive Summary & Win-Loss Metrics (LLaMEA vs. Classical Baselines)
- **Total Pairwise Tests ($N$):** `57`
- **🟢 LLaMEA Statistically Significant Wins ($p < 0.05, \hat{A}_{12} < 0.5$):** **`0`** (0.0%)
- **🔴 Classical Baselines Statistically Significant Wins ($p < 0.05, \hat{A}_{12} > 0.5$):** **`0`** (0.0%)
- **⚪ Non-Significant Differences & Exact Ties:** **`57`** (100.0%)

---
## 🌐 2. Omnibus Kruskal-Wallis H-Test (Group Differences Across All Solvers)

| Dim | Noise Std | Problem | Function Class | Solvers | H-Statistic | p-value | Significant Difference? |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| `2D` | `0.0` | `Sphere (f1)` | Separable | 4 | nan | nan | ⚪ No |
| `2D` | `0.0` | `Discus (f11)` | High Conditioning | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `2D` | `0.0` | `Rastrigin (f15)` | Multi-Modal (Global Structure) | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `2D` | `0.0` | `Gallagher 101 Peaks (f21)` | Multi-Modal (Weak Structure) | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `2D` | `0.0` | `Rosenbrock (f8)` | Low Conditioning | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `2D` | `0.05` | `Sphere (f1)` | Separable | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `2D` | `0.05` | `Discus (f11)` | High Conditioning | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `2D` | `0.05` | `Rastrigin (f15)` | Multi-Modal (Global Structure) | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `2D` | `0.05` | `Gallagher 101 Peaks (f21)` | Multi-Modal (Weak Structure) | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `2D` | `0.05` | `Rosenbrock (f8)` | Low Conditioning | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `3D` | `0.0` | `Sphere (f1)` | Separable | 4 | nan | nan | ⚪ No |
| `3D` | `0.0` | `Discus (f11)` | High Conditioning | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `3D` | `0.0` | `Rastrigin (f15)` | Multi-Modal (Global Structure) | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `3D` | `0.0` | `Gallagher 101 Peaks (f21)` | Multi-Modal (Weak Structure) | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `3D` | `0.0` | `Rosenbrock (f8)` | Low Conditioning | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `3D` | `0.05` | `Sphere (f1)` | Separable | 3 | 2.000 | 3.68e-01 | ⚪ No |
| `3D` | `0.05` | `Discus (f11)` | High Conditioning | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `3D` | `0.05` | `Rastrigin (f15)` | Multi-Modal (Global Structure) | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `3D` | `0.05` | `Gallagher 101 Peaks (f21)` | Multi-Modal (Weak Structure) | 4 | 3.000 | 3.92e-01 | ⚪ No |
| `3D` | `0.05` | `Rosenbrock (f8)` | Low Conditioning | 4 | 3.000 | 3.92e-01 | ⚪ No |

---
## 🔬 3. Complete Pairwise Evaluation Matrix (LLaMEA Prompt Strategies vs. Baselines)

| Dim | Noise Std | Problem | Function Class | LLaMEA Strategy | Baseline | LLaMEA Median | Baseline Median | MW p-val | A12 Effect Size | Magnitude | Outcome |
| :---: | :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `2D` | `0.0` | **Sphere (f1)** | Separable | **LLaMEA (Baseline)** | **CMAES** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
| `2D` | `0.0` | **Discus (f11)** | High Conditioning | **LLaMEA (Baseline)** | **CMAES** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 0.00e+00 | 8.22e-05 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
| `2D` | `0.0` | **Rastrigin (f15)** | Multi-Modal (Global Structure) | **LLaMEA (Baseline)** | **CMAES** | 7.15e-04 | 9.95e-01 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 7.15e-04 | 3.46e-08 | 1.00e+00 | 1.000 | Large | ⚪ DE Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 7.15e-04 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| `2D` | `0.0` | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak Structure) | **LLaMEA (Baseline)** | **CMAES** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 0.00e+00 | 1.20e-09 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
| `2D` | `0.0` | **Rosenbrock (f8)** | Low Conditioning | **LLaMEA (Baseline)** | **CMAES** | 1.19e+02 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 1.19e+02 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ DE Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 1.19e+02 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| `2D` | `0.05` | **Sphere (f1)** | Separable | **LLaMEA (Baseline)** | **CMAES** | 1.66e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 1.66e-06 | 7.16e-04 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 1.66e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| `2D` | `0.05` | **Discus (f11)** | High Conditioning | **LLaMEA (Baseline)** | **CMAES** | 7.87e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 7.87e-06 | 3.02e-05 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 7.87e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| `2D` | `0.05` | **Rastrigin (f15)** | Multi-Modal (Global Structure) | **LLaMEA (Baseline)** | **CMAES** | 1.09e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 1.09e-06 | 5.34e-02 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 1.09e-06 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| `2D` | `0.05` | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak Structure) | **LLaMEA (Baseline)** | **CMAES** | 5.00e-10 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 5.00e-10 | 1.00e-10 | 1.00e+00 | 1.000 | Large | ⚪ DE Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 5.00e-10 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| `2D` | `0.05` | **Rosenbrock (f8)** | Low Conditioning | **LLaMEA (Baseline)** | **CMAES** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 0.00e+00 | 1.06e-04 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
| `3D` | `0.0` | **Sphere (f1)** | Separable | **LLaMEA (Baseline)** | **CMAES** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
| `3D` | `0.0` | **Discus (f11)** | High Conditioning | **LLaMEA (Baseline)** | **CMAES** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 0.00e+00 | 1.55e-06 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
| `3D` | `0.0` | **Rastrigin (f15)** | Multi-Modal (Global Structure) | **LLaMEA (Baseline)** | **CMAES** | 3.19e-03 | 9.95e-01 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 3.19e-03 | 1.00e-06 | 1.00e+00 | 1.000 | Large | ⚪ DE Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 3.19e-03 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| `3D` | `0.0` | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak Structure) | **LLaMEA (Baseline)** | **CMAES** | 4.00e-10 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 4.00e-10 | 1.17e-08 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 4.00e-10 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| `3D` | `0.0` | **Rosenbrock (f8)** | Low Conditioning | **LLaMEA (Baseline)** | **CMAES** | 3.09e+03 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 3.09e+03 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ DE Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 3.09e+03 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| `3D` | `0.05` | **Discus (f11)** | High Conditioning | **LLaMEA (Baseline)** | **CMAES** | 3.31e-05 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 3.31e-05 | 6.09e-04 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 3.31e-05 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| `3D` | `0.05` | **Rastrigin (f15)** | Multi-Modal (Global Structure) | **LLaMEA (Baseline)** | **CMAES** | 1.86e-03 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 1.86e-03 | 2.30e+00 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 1.86e-03 | 9.95e-01 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
| `3D` | `0.05` | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak Structure) | **LLaMEA (Baseline)** | **CMAES** | 1.17e-04 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ CMAES Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 1.17e-04 | 2.16e-06 | 1.00e+00 | 1.000 | Large | ⚪ DE Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 1.17e-04 | 0.00e+00 | 1.00e+00 | 1.000 | Large | ⚪ PSO Ahead (Non-Sig) |
| `3D` | `0.05` | **Rosenbrock (f8)** | Low Conditioning | **LLaMEA (Baseline)** | **CMAES** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |
|  |  |  |  | **LLaMEA (Baseline)** | **DE** | 0.00e+00 | 1.31e-02 | 1.00e+00 | 0.000 | Large | ⚪ LLaMEA Ahead (Non-Sig) |
|  |  |  |  | **LLaMEA (Baseline)** | **PSO** | 0.00e+00 | 0.00e+00 | nan | 0.500 | Negligible | ⚪ Exact Tie |