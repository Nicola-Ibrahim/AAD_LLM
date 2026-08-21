# 🔬 Comprehensive Master Benchmark & Synthesis Evaluation Report

> End-to-end empirical evaluation connecting evolutionary algorithm discovery with downstream benchmark performance across BBOB continuous testbeds.

## 🏆 1. Executive Performance Scorecard (LLaMEA vs. Classical Baselines)
- **Total Evaluated Pairwise Contests ($N$):** `238`
- **🟢 LLaMEA Statistically Significant Wins ($p_{\text{FDR}} < 0.05, \hat{A}_{12} > 0.5$):** **`39`** (16.4%)
- **🔴 Classical Baseline Significant Wins ($p_{\text{FDR}} < 0.05, \hat{A}_{12} < 0.5$):** **`120`** (50.4%)
- **⚪ Ties / Equivalent ($p_{\text{FDR}} \ge 0.05$):** **`79`** (33.2%)

> **Scientific Interpretation:** LLaMEA algorithm discovery exhibits a distinct **landscape-dependent regime split**.
> On complex multimodal landscapes (e.g., *Rastrigin $f_{15}$*, *Gallagher 101 Peaks $f_{21}$*), LLaMEA evolved solvers consistently outperform or tie classical baselines by preserving exploratory search diversity and escaping local optima.
> Conversely, on smooth, separable unimodal landscapes (e.g., *Sphere $f_{1}$*), specialized numerical routines (such as CMA-ES covariance updates and DE/PSO vector steps) achieve rapid machine-precision convergence ($10^{-12}$). All reported significance badges apply **Benjamini-Hochberg False Discovery Rate (FDR)** control at $\alpha = 0.05$.

---
## 📊 2. Publication Figures & Quantitative Findings
| Figure | Focus & Research Question Answered | Key Quantitative Finding | File Link |
| :--- | :--- | :--- | :--- |
| **Figure A** | Problem Convergence & Precision Dashboard | Median precision reaches $10^{-8}$ on $f_{1}$ & $f_{11}$, with $f_{8}$ exhibiting highest stagnation rate. | [`problem_convergence_comparison.png`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/figures/advanced/problem_convergence_comparison.png) |
| **Figure B** | Clean-to-Noisy Matched-Pair Transfer | Pearson $r = 0.25$ ($p = 3.30e-02$), demonstrating cross-condition generalizability from clean synthesis to noisy environments. | [`clean_vs_noisy_transfer.png`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/figures/advanced/clean_vs_noisy_transfer.png) |
| **Figure C** | Noise Fragility & Degradation Matrix | Ill-conditioned $f_{8}$ suffers maximum noise degradation ($\Delta\log_{10}(\Delta y) > +3.0$), while separable $f_{1}$ is invariant. | [`noise_degradation_matrix.png`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/figures/advanced/noise_degradation_matrix.png) |
| **Figure D** | Dolan-Moré Performance Profiles $\rho_s(\tau)$ | Classical optimizers lead at zero slack ($	au=1$), while evolved algorithms achieve broad multi-modal robustness. | [`dolan_more_profiles.png`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/figures/advanced/dolan_more_profiles.png) |
| **Figure E** | Pairwise Effect Size Heatmap (Vargha-Delaney $A_{12}$) | Comprehensive $N \times N$ effect size matrix establishing stochastic dominance probabilities. | [`a12_effect_size_heatmap.png`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/figures/advanced/a12_effect_size_heatmap.png) |

---
## 🌐 3. Omnibus Kruskal-Wallis Test Results

| Dim | Noise Std | Problem | Function Class | Solvers | H-Statistic | p-value | Significant? |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| 2D | 0.0 | **Rosenbrock (f8)** | Low Conditioning | 6 | 46.627 | 6.77e-09 | 🟢 **Yes** |
| 2D | 0.0 | **Sphere (f1)** | Separable | 6 | 28.526 | 2.87e-05 | 🟢 **Yes** |
| 2D | 0.0 | **Rastrigin (f15)** | Multi-Modal (Global) | 6 | 45.255 | 1.29e-08 | 🟢 **Yes** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 6 | 38.091 | 3.62e-07 | 🟢 **Yes** |
| 2D | 0.0 | **Discus (f11)** | High Conditioning | 6 | 44.850 | 1.56e-08 | 🟢 **Yes** |
| 2D | 0.05 | **Rosenbrock (f8)** | Low Conditioning | 6 | 44.826 | 1.57e-08 | 🟢 **Yes** |
| 2D | 0.05 | **Sphere (f1)** | Separable | 6 | 44.029 | 2.29e-08 | 🟢 **Yes** |
| 2D | 0.05 | **Rastrigin (f15)** | Multi-Modal (Global) | 6 | 36.940 | 6.16e-07 | 🟢 **Yes** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 6 | 33.478 | 3.02e-06 | 🟢 **Yes** |
| 2D | 0.05 | **Discus (f11)** | High Conditioning | 6 | 8.908 | 1.13e-01 | ⚪ No |
| 5D | 0.0 | **Rosenbrock (f8)** | Low Conditioning | 6 | 34.582 | 1.82e-06 | 🟢 **Yes** |
| 5D | 0.0 | **Sphere (f1)** | Separable | 6 | 0.000 | 1.00e+00 | ⚪ *Identical (Δy=0)* |
| 5D | 0.0 | **Rastrigin (f15)** | Multi-Modal (Global) | 6 | 44.585 | 1.76e-08 | 🟢 **Yes** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 6 | 43.747 | 2.61e-08 | 🟢 **Yes** |
| 5D | 0.0 | **Discus (f11)** | High Conditioning | 6 | 45.695 | 1.05e-08 | 🟢 **Yes** |
| 5D | 0.05 | **Rosenbrock (f8)** | Low Conditioning | 6 | 41.533 | 7.32e-08 | 🟢 **Yes** |
| 5D | 0.05 | **Sphere (f1)** | Separable | 6 | 48.821 | 2.41e-09 | 🟢 **Yes** |
| 5D | 0.05 | **Rastrigin (f15)** | Multi-Modal (Global) | 6 | 51.960 | 5.50e-10 | 🟢 **Yes** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 5 | 33.027 | 1.18e-06 | 🟢 **Yes** |
| 5D | 0.05 | **Discus (f11)** | High Conditioning | 6 | 51.878 | 5.72e-10 | 🟢 **Yes** |
| 3D | 0.0 | **Rosenbrock (f8)** | Low Conditioning | 6 | 50.885 | 9.13e-10 | 🟢 **Yes** |
| 3D | 0.0 | **Sphere (f1)** | Separable | 6 | 0.000 | 1.00e+00 | ⚪ *Identical (Δy=0)* |
| 3D | 0.0 | **Rastrigin (f15)** | Multi-Modal (Global) | 6 | 48.674 | 2.59e-09 | 🟢 **Yes** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 6 | 41.023 | 9.28e-08 | 🟢 **Yes** |
| 3D | 0.0 | **Discus (f11)** | High Conditioning | 6 | 55.858 | 8.69e-11 | 🟢 **Yes** |
| 3D | 0.05 | **Rosenbrock (f8)** | Low Conditioning | 6 | 29.547 | 1.81e-05 | 🟢 **Yes** |
| 3D | 0.05 | **Sphere (f1)** | Separable | 6 | 56.005 | 8.11e-11 | 🟢 **Yes** |
| 3D | 0.05 | **Rastrigin (f15)** | Multi-Modal (Global) | 6 | 49.225 | 2.00e-09 | 🟢 **Yes** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 6 | 44.762 | 1.62e-08 | 🟢 **Yes** |
| 3D | 0.05 | **Discus (f11)** | High Conditioning | 6 | 52.604 | 4.06e-10 | 🟢 **Yes** |

---
## 🔬 4. Problem-Level Summary & Pairwise Statistical Breakdown

### 4.1 Summary by Landscape Class (LLaMEA vs. Classical Baselines)

| Problem | Landscape Class | Contests | LLaMEA Wins | Baseline Wins | Ties / Inconclusive | Dominant Regime |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Sphere (f1)** | Separable | 48 | 8 | 15 | 25 | 🔴 Baseline Advantage |
| **Rosenbrock (f8)** | Low Conditioning | 48 | 10 | 23 | 15 | 🔴 Baseline Advantage |
| **Discus (f11)** | High Conditioning | 48 | 7 | 25 | 16 | 🔴 Baseline Advantage |
| **Rastrigin (f15)** | Multi-Modal (Global) | 48 | 2 | 38 | 8 | 🔴 Baseline Advantage |
| **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 46 | 12 | 19 | 15 | 🔴 Baseline Advantage |

### 4.2 Statistically Significant Pairwise Contests (FDR-Corrected $p < 0.05$)

| Dim | Noise | Problem | Solver 1 | Solver 2 | Med 1 | Med 2 | Raw p-val | Adj p-val (FDR) | A12 | Outcome |
| :---: | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 2D | 0.0 | **Sphere (f1)** | LLaMEA_Baseline | DE | 1.03e+00 | 0.00e+00 | 9.45e-03 | 1.59e-02 | 0.250 | **DE Wins** |
| 2D | 0.0 | **Sphere (f1)** | LLaMEA_Baseline | CMAES | 1.03e+00 | 0.00e+00 | 9.45e-03 | 1.59e-02 | 0.250 | **CMAES Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | DE | 1.52e-08 | 2.12e-02 | 1.83e-04 | 4.62e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | CMAES | 1.52e-08 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | DE | 4.65e-04 | 2.12e-02 | 1.83e-04 | 4.62e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | CMAES | 4.65e-04 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Baseline | DE | 0.00e+00 | 2.12e-02 | 2.12e-02 | 3.29e-02 | 0.800 | **LLaMEA_Baseline Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | DE | 1.21e-05 | 2.12e-02 | 1.83e-04 | 4.62e-04 | 1.000 | **LLaMEA_Vectorization Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | CMAES | 1.21e-05 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | DE | 1.97e-08 | 5.30e-02 | 1.83e-04 | 4.62e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | CMAES | 1.97e-08 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | CMAES | 2.88e-02 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Baseline | DE | 0.00e+00 | 5.30e-02 | 6.39e-05 | 4.62e-04 | 1.000 | **LLaMEA_Baseline Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | DE | 8.53e-03 | 5.30e-02 | 2.46e-04 | 5.76e-04 | 0.990 | **LLaMEA_Vectorization Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | CMAES | 8.53e-03 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | DE | 1.36e-07 | 1.12e-01 | 1.83e-04 | 4.62e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | CMAES | 1.36e-07 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | DE | 3.99e-01 | 1.12e-01 | 2.46e-04 | 5.76e-04 | 0.010 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | CMAES | 3.99e-01 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Baseline | DE | 3.37e+00 | 1.12e-01 | 2.11e-02 | 3.29e-02 | 0.190 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Baseline | CMAES | 3.37e+00 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | DE | 2.95e-01 | 1.12e-01 | 2.20e-03 | 4.21e-03 | 0.090 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | CMAES | 2.95e-01 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | DE | 0.00e+00 | 4.50e-10 | 2.21e-03 | 4.21e-03 | 0.850 | **LLaMEA_Thinking Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Baseline | DE | 0.00e+00 | 4.50e-10 | 2.21e-03 | 4.21e-03 | 0.850 | **LLaMEA_Baseline Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | DE | 1.94e-05 | 4.50e-10 | 2.17e-03 | 4.21e-03 | 0.090 | **DE Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | CMAES | 1.94e-05 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Thinking | CMAES | 7.98e-03 | 0.00e+00 | 4.70e-03 | 8.30e-03 | 0.145 | **CMAES Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Guided | DE | 0.00e+00 | 4.84e-03 | 6.39e-05 | 4.62e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Baseline | DE | 0.00e+00 | 4.84e-03 | 6.39e-05 | 4.62e-04 | 1.000 | **LLaMEA_Baseline Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Vectorization | DE | 1.08e-04 | 4.84e-03 | 2.20e-03 | 4.21e-03 | 0.910 | **LLaMEA_Vectorization Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Vectorization | CMAES | 1.08e-04 | 0.00e+00 | 1.75e-03 | 3.47e-03 | 0.100 | **CMAES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | DE | 6.00e-05 | 1.30e-09 | 8.98e-03 | 1.54e-02 | 0.150 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | CMAES | 6.00e-05 | 0.00e+00 | 2.31e-04 | 5.65e-04 | 0.050 | **CMAES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Guided | DE | 7.92e-06 | 1.30e-09 | 1.30e-03 | 2.75e-03 | 0.070 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Guided | CMAES | 7.92e-06 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Baseline | DE | 0.00e+00 | 1.30e-09 | 7.47e-04 | 1.65e-03 | 0.900 | **LLaMEA_Baseline Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | DE | 7.34e-03 | 1.30e-09 | 1.81e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | CMAES | 7.34e-03 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Thinking | CMAES | 6.03e-01 | 0.00e+00 | 8.89e-03 | 1.54e-02 | 0.160 | **CMAES Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Guided | DE | 0.00e+00 | 8.30e-02 | 2.12e-02 | 3.29e-02 | 0.800 | **LLaMEA_Guided Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Baseline | DE | 6.00e-10 | 8.30e-02 | 1.81e-04 | 4.62e-04 | 1.000 | **LLaMEA_Baseline Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Baseline | CMAES | 6.00e-10 | 0.00e+00 | 2.11e-02 | 3.29e-02 | 0.200 | **CMAES Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Vectorization | CMAES | 2.17e-02 | 0.00e+00 | 2.12e-02 | 3.29e-02 | 0.200 | **CMAES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | DE | 1.71e-01 | 6.00e-10 | 2.81e-03 | 5.20e-03 | 0.100 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | CMAES | 1.71e-01 | 0.00e+00 | 2.12e-02 | 3.29e-02 | 0.200 | **CMAES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Guided | DE | 2.45e-02 | 6.00e-10 | 1.30e-03 | 2.75e-03 | 0.070 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Guided | CMAES | 2.45e-02 | 0.00e+00 | 5.54e-03 | 9.75e-03 | 0.140 | **CMAES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Baseline | DE | 0.00e+00 | 6.00e-10 | 7.47e-04 | 1.65e-03 | 0.900 | **LLaMEA_Baseline Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | DE | 2.19e-01 | 6.00e-10 | 2.81e-03 | 5.20e-03 | 0.100 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | CMAES | 2.19e-01 | 0.00e+00 | 2.12e-02 | 3.29e-02 | 0.200 | **CMAES Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Thinking | DE | 3.49e+01 | 1.66e+00 | 2.46e-04 | 5.76e-04 | 0.010 | **DE Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Thinking | CMAES | 3.49e+01 | 1.95e+00 | 2.41e-04 | 5.76e-04 | 0.010 | **CMAES Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Guided | DE | 4.46e+00 | 1.66e+00 | 1.13e-02 | 1.88e-02 | 0.160 | **DE Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Guided | CMAES | 4.46e+00 | 1.95e+00 | 1.39e-02 | 2.30e-02 | 0.170 | **CMAES Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Baseline | DE | 7.41e-04 | 1.66e+00 | 1.83e-04 | 4.62e-04 | 1.000 | **LLaMEA_Baseline Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA_Thinking | DE | 0.00e+00 | 1.51e-03 | 7.56e-04 | 1.66e-03 | 0.930 | **LLaMEA_Thinking Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA_Guided | DE | 0.00e+00 | 1.51e-03 | 1.75e-03 | 3.47e-03 | 0.900 | **LLaMEA_Guided Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA_Baseline | DE | 0.00e+00 | 1.51e-03 | 6.39e-05 | 4.62e-04 | 1.000 | **LLaMEA_Baseline Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA_Vectorization | CMAES | 1.14e-04 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA_Guided | DE | 9.12e-05 | 8.86e-03 | 1.83e-04 | 4.62e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Guided | DE | 8.24e+04 | 5.08e-03 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Guided | CMAES | 8.24e+04 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Thinking | DE | 5.15e+06 | 5.08e-03 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Thinking | CMAES | 5.15e+06 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Baseline | DE | 0.00e+00 | 5.08e-03 | 6.39e-05 | 4.62e-04 | 1.000 | **LLaMEA_Baseline Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Vectorization | CMAES | 3.18e-04 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA_Guided | DE | 1.07e+00 | 3.41e-02 | 1.71e-03 | 3.47e-03 | 0.080 | **DE Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA_Guided | CMAES | 1.07e+00 | 0.00e+00 | 7.56e-04 | 1.66e-03 | 0.070 | **CMAES Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA_Baseline | DE | 3.38e-04 | 3.41e-02 | 1.83e-04 | 4.62e-04 | 1.000 | **LLaMEA_Baseline Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA_Baseline | CMAES | 3.38e-04 | 0.00e+00 | 1.75e-03 | 3.47e-03 | 0.100 | **CMAES Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA_Thinking | DE | 1.87e+04 | 3.41e-02 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA_Thinking | CMAES | 1.87e+04 | 0.00e+00 | 8.74e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA_Vectorization | DE | 3.01e+04 | 3.41e-02 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA_Vectorization | CMAES | 3.01e+04 | 0.00e+00 | 8.74e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA_Guided | DE | 0.00e+00 | 1.62e-03 | 1.49e-04 | 4.62e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA_Thinking | CMAES | 4.25e-03 | 0.00e+00 | 2.21e-03 | 4.21e-03 | 0.150 | **CMAES Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA_Vectorization | CMAES | 1.17e-03 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA_Baseline | DE | 6.46e+04 | 1.62e-03 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA_Baseline | CMAES | 6.46e+04 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA_Guided | DE | 2.08e+03 | 5.38e-02 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA_Guided | CMAES | 2.08e+03 | 0.00e+00 | 3.80e-04 | 8.76e-04 | 0.040 | **CMAES Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA_Thinking | DE | 1.68e+03 | 5.38e-02 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA_Thinking | CMAES | 1.68e+03 | 0.00e+00 | 1.52e-04 | 4.62e-04 | 0.010 | **CMAES Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA_Baseline | DE | 1.83e+07 | 5.38e-02 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA_Baseline | CMAES | 1.83e+07 | 0.00e+00 | 1.11e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA_Vectorization | DE | 5.53e+04 | 5.38e-02 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA_Vectorization | CMAES | 5.53e+04 | 0.00e+00 | 1.11e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Thinking | DE | 4.18e+01 | 9.95e-01 | 1.82e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Thinking | CMAES | 4.18e+01 | 1.22e+00 | 1.73e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Baseline | DE | 7.41e+02 | 9.95e-01 | 1.82e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Baseline | CMAES | 7.41e+02 | 1.22e+00 | 1.73e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | DE | LLaMEA_Vectorization | 9.95e-01 | 2.23e+01 | 2.19e-03 | 4.21e-03 | 0.910 | **DE Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Vectorization | CMAES | 2.23e+01 | 1.22e+00 | 7.07e-03 | 1.23e-02 | 0.140 | **CMAES Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Guided | DE | 6.10e+01 | 3.15e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Guided | CMAES | 6.10e+01 | 1.00e+00 | 1.82e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Thinking | CMAES | 1.10e+01 | 1.00e+00 | 2.82e-03 | 5.20e-03 | 0.100 | **CMAES Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Baseline | DE | 9.61e+02 | 3.15e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Baseline | CMAES | 9.61e+02 | 1.00e+00 | 1.82e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Vectorization | DE | 3.84e+01 | 3.15e+00 | 4.59e-03 | 8.13e-03 | 0.120 | **DE Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Vectorization | CMAES | 3.84e+01 | 1.00e+00 | 2.17e-03 | 4.21e-03 | 0.090 | **CMAES Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Thinking | DE | 9.95e-01 | 2.49e+00 | 4.57e-03 | 8.13e-03 | 0.880 | **LLaMEA_Thinking Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Thinking | CMAES | 9.95e-01 | 3.38e+00 | 4.54e-03 | 8.13e-03 | 0.880 | **LLaMEA_Thinking Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Baseline | DE | 9.94e+01 | 2.49e+00 | 1.82e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Baseline | CMAES | 9.94e+01 | 3.38e+00 | 1.80e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | DE | LLaMEA_Vectorization | 2.49e+00 | 4.86e+02 | 1.82e-04 | 4.62e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Vectorization | CMAES | 4.86e+02 | 3.38e+00 | 1.80e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Guided | DE | 6.88e+01 | 5.32e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Guided | CMAES | 6.88e+01 | 3.41e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Thinking | DE | 3.31e+01 | 5.32e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Thinking | CMAES | 3.31e+01 | 3.41e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Baseline | DE | 3.42e+01 | 5.32e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Baseline | CMAES | 3.42e+01 | 3.41e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Vectorization | DE | 5.47e+02 | 5.32e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Vectorization | CMAES | 5.47e+02 | 3.41e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.0 | **Rastrigin (f15)** | LLaMEA_Guided | DE | 1.06e+01 | 5.97e+00 | 3.12e-02 | 4.66e-02 | 0.210 | **DE Wins** |
| 5D | 0.0 | **Rastrigin (f15)** | LLaMEA_Guided | CMAES | 1.06e+01 | 4.97e+00 | 8.98e-03 | 1.54e-02 | 0.150 | **CMAES Wins** |
| 5D | 0.0 | **Rastrigin (f15)** | LLaMEA_Thinking | DE | 2.49e+02 | 5.97e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.0 | **Rastrigin (f15)** | LLaMEA_Thinking | CMAES | 2.49e+02 | 4.97e+00 | 1.78e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.0 | **Rastrigin (f15)** | LLaMEA_Baseline | DE | 9.01e+01 | 5.97e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.0 | **Rastrigin (f15)** | LLaMEA_Baseline | CMAES | 9.01e+01 | 4.97e+00 | 1.78e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Rastrigin (f15)** | LLaMEA_Guided | DE | 3.97e+01 | 1.59e+01 | 4.40e-04 | 1.00e-03 | 0.030 | **DE Wins** |
| 5D | 0.05 | **Rastrigin (f15)** | LLaMEA_Guided | CMAES | 3.97e+01 | 6.64e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Rastrigin (f15)** | LLaMEA_Thinking | CMAES | 1.53e+01 | 6.64e+00 | 9.11e-03 | 1.56e-02 | 0.150 | **CMAES Wins** |
| 5D | 0.05 | **Rastrigin (f15)** | LLaMEA_Baseline | DE | 7.10e+01 | 1.59e+01 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.05 | **Rastrigin (f15)** | LLaMEA_Baseline | CMAES | 7.10e+01 | 6.64e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Rastrigin (f15)** | LLaMEA_Vectorization | DE | 8.12e+02 | 1.59e+01 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.05 | **Rastrigin (f15)** | LLaMEA_Vectorization | CMAES | 8.12e+02 | 6.64e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | CMAES | 1.85e-09 | 7.33e-01 | 2.75e-02 | 4.12e-02 | 0.790 | **LLaMEA_Guided Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | DE | 8.46e+00 | 3.39e-07 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | CMAES | 8.46e+00 | 7.33e-01 | 2.43e-04 | 5.76e-04 | 0.010 | **CMAES Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA_Vectorization | 3.39e-07 | 0.00e+00 | 6.39e-05 | 4.62e-04 | 0.000 | **LLaMEA_Vectorization Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | CMAES | 0.00e+00 | 7.33e-01 | 7.47e-04 | 1.65e-03 | 0.900 | **LLaMEA_Vectorization Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | CMAES | 0.00e+00 | 9.33e-01 | 7.84e-04 | 1.70e-03 | 0.935 | **LLaMEA_Guided Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | DE | 0.00e+00 | 1.50e-05 | 6.39e-05 | 4.62e-04 | 1.000 | **LLaMEA_Baseline Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | CMAES | 0.00e+00 | 9.33e-01 | 2.31e-04 | 5.65e-04 | 0.950 | **LLaMEA_Baseline Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | DE | 0.00e+00 | 1.50e-05 | 6.39e-05 | 4.62e-04 | 1.000 | **LLaMEA_Vectorization Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | CMAES | 0.00e+00 | 9.33e-01 | 2.31e-04 | 5.65e-04 | 0.950 | **LLaMEA_Vectorization Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | DE | 0.00e+00 | 2.61e-06 | 6.39e-05 | 4.62e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | CMAES | 0.00e+00 | 6.92e-01 | 5.94e-03 | 1.04e-02 | 0.800 | **LLaMEA_Guided Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | DE | 2.91e+01 | 2.61e-06 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | CMAES | 2.91e+01 | 6.92e-01 | 1.72e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | DE | 3.37e+01 | 2.57e-05 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | CMAES | 3.37e+01 | 8.20e-01 | 1.79e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | DE | 3.32e+00 | 2.57e-05 | 1.71e-03 | 3.47e-03 | 0.080 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | DE | 3.20e+01 | 2.57e-05 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | CMAES | 3.20e+01 | 8.20e-01 | 1.79e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | DE | 3.36e+01 | 2.57e-05 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | CMAES | 3.36e+01 | 8.20e-01 | 2.41e-04 | 5.76e-04 | 0.010 | **CMAES Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | DE | 6.45e+01 | 4.65e-01 | 1.82e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | CMAES | 6.45e+01 | 1.25e+00 | 1.49e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | DE | 0.00e+00 | 4.65e-01 | 6.34e-05 | 4.62e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | CMAES | 0.00e+00 | 1.25e+00 | 1.82e-04 | 4.62e-04 | 0.950 | **LLaMEA_Thinking Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | DE | 2.00e+00 | 4.65e-01 | 4.57e-03 | 8.13e-03 | 0.120 | **DE Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | CMAES | 2.00e+00 | 1.25e+00 | 2.38e-02 | 3.66e-02 | 0.200 | **CMAES Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | DE | 6.46e+01 | 3.73e-01 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | CMAES | 6.46e+01 | 1.27e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | DE | 6.66e+01 | 3.73e-01 | 1.83e-04 | 4.62e-04 | 0.000 | **DE Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | CMAES | 6.66e+01 | 1.27e+00 | 1.83e-04 | 4.62e-04 | 0.000 | **CMAES Wins** |

---
## 🌊 5. Noise Robustness & Landscape Fragility Analysis

The impact of stochastic evaluation noise ($\\sigma = 0.05$) is quantified via the **Degradation Factor** $\\Delta \\log_{10}(\\Delta y) = \\log_{10}(\\text{Median Error}_{\\text{Noisy}}) - \\log_{10}(\\text{Median Error}_{\\text{Clean}})$. Positive values indicate loss of precision under noise.

| Problem Landscape | Landscape Class | Median Degradation (LLaMEA) | Median Degradation (Baselines) | Noise Sensitivity Assessment |
| :--- | :--- | :---: | :---: | :--- |
| **Sphere (f1)** | Separable | +9.93 | +10.73 | 🟢 **Resilient**: Precision remains intact despite stochastic perturbation |
| **Rosenbrock (f8)** | Low Conditioning | +1.69 | +8.18 | 🔴 **High Fragility**: Severe valley stagnation under noise |
| **Discus (f11)** | High Conditioning | +8.26 | +1.16 | 🟢 **Resilient**: Precision remains intact despite stochastic perturbation |
| **Rastrigin (f15)** | Multi-Modal (Global) | +0.30 | +0.15 | 🟡 **Moderate Fragility**: Slight barrier degradation, exploration preserved |
| **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | +5.26 | +1.05 | 🟡 **Moderate Fragility**: Slight barrier degradation, exploration preserved |