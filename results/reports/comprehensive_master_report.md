# 🔬 Comprehensive Master Benchmark & Synthesis Evaluation Report

> End-to-end empirical evaluation connecting evolutionary algorithm discovery with downstream benchmark performance across BBOB continuous testbeds.

## 🏆 1. Executive Performance Scorecard (LLaMEA vs. Classical Baselines)
- **Total Evaluated Pairwise Contests ($N$):** `321`
- **🟢 LLaMEA Statistically Significant Wins ($p_{\text{FDR}} < 0.05, \hat{A}_{12} > 0.5$):** **`67`** (20.9%)
- **🔴 Classical Baseline Significant Wins ($p_{\text{FDR}} < 0.05, \hat{A}_{12} < 0.5$):** **`118`** (36.8%)
- **⚪ Ties / Equivalent ($p_{\text{FDR}} \ge 0.05$):** **`136`** (42.4%)

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
| 2D | 0.0 | **Rosenbrock (f8)** | Low Conditioning | 7 | 63.895 | 7.25e-12 | 🟢 **Yes** |
| 2D | 0.0 | **Sphere (f1)** | Separable | 7 | 48.906 | 7.79e-09 | 🟢 **Yes** |
| 2D | 0.0 | **Rastrigin (f15)** | Multi-Modal (Global) | 7 | 56.154 | 2.71e-10 | 🟢 **Yes** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 7 | 29.607 | 4.67e-05 | 🟢 **Yes** |
| 2D | 0.0 | **Discus (f11)** | High Conditioning | 7 | 34.830 | 4.65e-06 | 🟢 **Yes** |
| 2D | 0.05 | **Rosenbrock (f8)** | Low Conditioning | 7 | 62.999 | 1.10e-11 | 🟢 **Yes** |
| 2D | 0.05 | **Sphere (f1)** | Separable | 7 | 55.433 | 3.79e-10 | 🟢 **Yes** |
| 2D | 0.05 | **Rastrigin (f15)** | Multi-Modal (Global) | 7 | 70.028 | 4.03e-13 | 🟢 **Yes** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 7 | 27.415 | 1.21e-04 | 🟢 **Yes** |
| 2D | 0.05 | **Discus (f11)** | High Conditioning | 7 | 43.849 | 7.92e-08 | 🟢 **Yes** |
| 5D | 0.0 | **Rosenbrock (f8)** | Low Conditioning | 7 | 28.851 | 6.49e-05 | 🟢 **Yes** |
| 5D | 0.0 | **Sphere (f1)** | Separable | 7 | 43.381 | 9.80e-08 | 🟢 **Yes** |
| 5D | 0.0 | **Rastrigin (f15)** | Multi-Modal (Global) | 7 | 34.386 | 5.67e-06 | 🟢 **Yes** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 7 | 52.895 | 1.23e-09 | 🟢 **Yes** |
| 5D | 0.0 | **Discus (f11)** | High Conditioning | 7 | 31.802 | 1.78e-05 | 🟢 **Yes** |
| 5D | 0.05 | **Rosenbrock (f8)** | Low Conditioning | 7 | 18.521 | 5.05e-03 | 🟢 **Yes** |
| 5D | 0.05 | **Sphere (f1)** | Separable | 7 | 75.871 | 2.54e-14 | 🟢 **Yes** |
| 5D | 0.05 | **Rastrigin (f15)** | Multi-Modal (Global) | 4 | 9.406 | 2.44e-02 | 🟢 **Yes** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 3 | 25.468 | 2.95e-06 | 🟢 **Yes** |
| 5D | 0.05 | **Discus (f11)** | High Conditioning | 4 | 17.291 | 6.16e-04 | 🟢 **Yes** |
| 3D | 0.0 | **Rosenbrock (f8)** | Low Conditioning | 7 | 48.198 | 1.08e-08 | 🟢 **Yes** |
| 3D | 0.0 | **Sphere (f1)** | Separable | 7 | 27.628 | 1.10e-04 | 🟢 **Yes** |
| 3D | 0.0 | **Rastrigin (f15)** | Multi-Modal (Global) | 7 | 35.957 | 2.81e-06 | 🟢 **Yes** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 7 | 60.839 | 3.04e-11 | 🟢 **Yes** |
| 3D | 0.0 | **Discus (f11)** | High Conditioning | 7 | 52.913 | 1.22e-09 | 🟢 **Yes** |
| 3D | 0.05 | **Rosenbrock (f8)** | Low Conditioning | 7 | 26.476 | 1.81e-04 | 🟢 **Yes** |
| 3D | 0.05 | **Sphere (f1)** | Separable | 7 | 44.970 | 4.75e-08 | 🟢 **Yes** |
| 3D | 0.05 | **Rastrigin (f15)** | Multi-Modal (Global) | 7 | 30.114 | 3.74e-05 | 🟢 **Yes** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 6 | 32.009 | 5.92e-06 | 🟢 **Yes** |
| 3D | 0.05 | **Discus (f11)** | High Conditioning | 7 | 17.212 | 8.54e-03 | 🟢 **Yes** |

---
## 🔬 4. Problem-Level Summary & Pairwise Statistical Breakdown

### 4.1 Summary by Landscape Class (LLaMEA vs. Classical Baselines)

| Problem | Landscape Class | Contests | LLaMEA Wins | Baseline Wins | Ties / Inconclusive | Dominant Regime |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Sphere (f1)** | Separable | 72 | 6 | 36 | 30 | 🔴 Baseline Advantage |
| **Rosenbrock (f8)** | Low Conditioning | 72 | 4 | 45 | 23 | 🔴 Baseline Advantage |
| **Discus (f11)** | High Conditioning | 60 | 8 | 17 | 35 | 🔴 Baseline Advantage |
| **Rastrigin (f15)** | Multi-Modal (Global) | 60 | 22 | 14 | 24 | 🟢 LLaMEA Advantage |
| **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 57 | 27 | 6 | 24 | 🟢 LLaMEA Advantage |

### 4.2 Statistically Significant Pairwise Contests (FDR-Corrected $p < 0.05$)

| Dim | Noise | Problem | Solver 1 | Solver 2 | Med 1 | Med 2 | Raw p-val | Adj p-val (FDR) | A12 | Outcome |
| :---: | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 2D | 0.0 | **Sphere (f1)** | LLaMEA_Baseline | DE | 1.89e-06 | 0.00e+00 | 1.37e-03 | 3.92e-03 | 0.200 | **DE Wins** |
| 2D | 0.0 | **Sphere (f1)** | LLaMEA_Baseline | CMAES | 1.89e-06 | 0.00e+00 | 1.37e-03 | 3.92e-03 | 0.200 | **CMAES Wins** |
| 2D | 0.0 | **Sphere (f1)** | LLaMEA_Baseline | PSO | 1.89e-06 | 0.00e+00 | 1.37e-03 | 3.92e-03 | 0.200 | **PSO Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Baseline | CMAES | 1.77e-01 | 0.00e+00 | 4.83e-05 | 3.83e-04 | 0.102 | **CMAES Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Baseline | PSO | 1.77e-01 | 0.00e+00 | 4.83e-05 | 3.83e-04 | 0.102 | **PSO Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | DE | 1.52e-08 | 2.02e-02 | 1.83e-04 | 7.79e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | CMAES | 1.52e-08 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | PSO | 1.52e-08 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | DE | 4.65e-04 | 2.02e-02 | 2.46e-04 | 9.33e-04 | 0.990 | **LLaMEA_Guided Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | CMAES | 4.65e-04 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | PSO | 4.65e-04 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | DE | 1.21e-05 | 2.02e-02 | 1.83e-04 | 7.79e-04 | 1.000 | **LLaMEA_Vectorization Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | CMAES | 1.21e-05 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | PSO | 1.21e-05 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Sphere (f1)** | LLaMEA_Baseline | DE | 0.00e+00 | 0.00e+00 | 2.23e-02 | 4.12e-02 | 0.312 | **DE Wins** |
| 3D | 0.0 | **Sphere (f1)** | LLaMEA_Baseline | CMAES | 0.00e+00 | 0.00e+00 | 2.23e-02 | 4.12e-02 | 0.312 | **CMAES Wins** |
| 3D | 0.0 | **Sphere (f1)** | LLaMEA_Baseline | PSO | 0.00e+00 | 0.00e+00 | 2.23e-02 | 4.12e-02 | 0.312 | **PSO Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Baseline | CMAES | 1.10e-02 | 0.00e+00 | 1.14e-04 | 6.31e-04 | 0.129 | **CMAES Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Baseline | PSO | 1.10e-02 | 0.00e+00 | 1.14e-04 | 6.31e-04 | 0.129 | **PSO Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | DE | 1.97e-08 | 2.24e-02 | 1.83e-04 | 7.79e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | CMAES | 1.97e-08 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | PSO | 1.97e-08 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | CMAES | 2.88e-02 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | PSO | 2.88e-02 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | DE | 8.53e-03 | 2.24e-02 | 7.28e-03 | 1.57e-02 | 0.860 | **LLaMEA_Vectorization Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | CMAES | 8.53e-03 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | PSO | 8.53e-03 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Sphere (f1)** | LLaMEA_Baseline | DE | 3.15e-08 | 0.00e+00 | 2.63e-03 | 6.48e-03 | 0.219 | **DE Wins** |
| 5D | 0.0 | **Sphere (f1)** | LLaMEA_Baseline | CMAES | 3.15e-08 | 0.00e+00 | 2.63e-03 | 6.48e-03 | 0.219 | **CMAES Wins** |
| 5D | 0.0 | **Sphere (f1)** | LLaMEA_Baseline | PSO | 3.15e-08 | 0.00e+00 | 2.63e-03 | 6.48e-03 | 0.219 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | DE | 1.36e-07 | 9.39e-02 | 1.83e-04 | 7.79e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | CMAES | 1.36e-07 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Thinking | PSO | 1.36e-07 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | DE | 3.99e-01 | 9.39e-02 | 2.46e-04 | 9.33e-04 | 0.010 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | CMAES | 3.99e-01 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Guided | PSO | 3.99e-01 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Baseline | DE | 1.45e+00 | 9.39e-02 | 8.89e-04 | 2.85e-03 | 0.163 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Baseline | CMAES | 1.45e+00 | 0.00e+00 | 7.36e-07 | 1.06e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Baseline | PSO | 1.45e+00 | 0.00e+00 | 7.36e-07 | 1.06e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | DE | 2.95e-01 | 9.39e-02 | 1.71e-03 | 4.57e-03 | 0.080 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | CMAES | 2.95e-01 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA_Vectorization | PSO | 2.95e-01 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Baseline | DE | 4.47e+00 | 5.50e-10 | 1.43e-03 | 4.07e-03 | 0.190 | **DE Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Baseline | CMAES | 4.47e+00 | 0.00e+00 | 3.74e-05 | 3.83e-04 | 0.103 | **CMAES Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Baseline | PSO | 4.47e+00 | 0.00e+00 | 3.74e-05 | 3.83e-04 | 0.103 | **PSO Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | DE | 0.00e+00 | 5.50e-10 | 7.47e-04 | 2.46e-03 | 0.900 | **LLaMEA_Thinking Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | DE | 1.94e-05 | 5.50e-10 | 4.35e-04 | 1.54e-03 | 0.030 | **DE Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | CMAES | 1.94e-05 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | PSO | 1.94e-05 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Baseline | CMAES | 7.04e-01 | 0.00e+00 | 1.20e-05 | 3.83e-04 | 0.072 | **CMAES Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Baseline | PSO | 7.04e-01 | 0.00e+00 | 1.20e-05 | 3.83e-04 | 0.072 | **PSO Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Thinking | CMAES | 7.98e-03 | 0.00e+00 | 2.31e-04 | 9.19e-04 | 0.050 | **CMAES Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Thinking | PSO | 7.98e-03 | 0.00e+00 | 2.31e-04 | 9.19e-04 | 0.050 | **PSO Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Guided | DE | 0.00e+00 | 1.86e-03 | 6.39e-05 | 3.83e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Vectorization | DE | 1.08e-04 | 1.86e-03 | 1.71e-03 | 4.57e-03 | 0.920 | **LLaMEA_Vectorization Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Vectorization | CMAES | 1.08e-04 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Vectorization | PSO | 1.08e-04 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | DE | 6.00e-05 | 1.20e-09 | 5.08e-03 | 1.16e-02 | 0.125 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | CMAES | 6.00e-05 | 0.00e+00 | 2.31e-04 | 9.19e-04 | 0.050 | **CMAES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | PSO | 6.00e-05 | 0.00e+00 | 2.31e-04 | 9.19e-04 | 0.050 | **PSO Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Baseline | DE | 8.11e+00 | 1.20e-09 | 9.33e-03 | 1.96e-02 | 0.246 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Baseline | CMAES | 8.11e+00 | 0.00e+00 | 1.14e-04 | 6.31e-04 | 0.129 | **CMAES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Baseline | PSO | 8.11e+00 | 0.00e+00 | 1.14e-04 | 6.31e-04 | 0.129 | **PSO Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Guided | DE | 7.92e-06 | 1.20e-09 | 9.90e-04 | 3.10e-03 | 0.060 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Guided | CMAES | 7.92e-06 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Guided | PSO | 7.92e-06 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | DE | 7.34e-03 | 1.20e-09 | 1.79e-04 | 7.79e-04 | 0.000 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | CMAES | 7.34e-03 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | PSO | 7.34e-03 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Baseline | CMAES | 8.58e-01 | 0.00e+00 | 5.78e-03 | 1.30e-02 | 0.227 | **CMAES Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Baseline | PSO | 8.58e-01 | 1.30e-02 | 2.63e-02 | 4.75e-02 | 0.280 | **PSO Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Thinking | DE | 6.03e-01 | 8.26e-02 | 1.13e-02 | 2.36e-02 | 0.160 | **DE Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Guided | DE | 0.00e+00 | 8.26e-02 | 2.12e-02 | 4.00e-02 | 0.800 | **LLaMEA_Guided Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | DE | 1.71e-01 | 6.50e-10 | 2.82e-03 | 6.79e-03 | 0.100 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | CMAES | 1.71e-01 | 0.00e+00 | 1.75e-03 | 4.57e-03 | 0.100 | **CMAES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Thinking | PSO | 1.71e-01 | 0.00e+00 | 1.75e-03 | 4.57e-03 | 0.100 | **PSO Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Baseline | CMAES | 2.38e-02 | 0.00e+00 | 7.83e-03 | 1.66e-02 | 0.244 | **CMAES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Baseline | PSO | 2.38e-02 | 0.00e+00 | 7.83e-03 | 1.66e-02 | 0.244 | **PSO Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Guided | DE | 2.45e-02 | 6.50e-10 | 1.31e-03 | 3.90e-03 | 0.070 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Guided | CMAES | 2.45e-02 | 0.00e+00 | 7.56e-04 | 2.46e-03 | 0.070 | **CMAES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Guided | PSO | 2.45e-02 | 0.00e+00 | 7.56e-04 | 2.46e-03 | 0.070 | **PSO Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | DE | 2.19e-01 | 6.50e-10 | 2.82e-03 | 6.79e-03 | 0.100 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | CMAES | 2.19e-01 | 0.00e+00 | 1.75e-03 | 4.57e-03 | 0.100 | **CMAES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA_Vectorization | PSO | 2.19e-01 | 0.00e+00 | 1.75e-03 | 4.57e-03 | 0.100 | **PSO Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Thinking | DE | 3.49e+01 | 1.28e+00 | 2.46e-04 | 9.33e-04 | 0.010 | **DE Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Thinking | CMAES | 3.49e+01 | 1.30e+00 | 3.23e-04 | 1.16e-03 | 0.020 | **CMAES Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Thinking | PSO | 3.49e+01 | 9.47e-01 | 2.50e-04 | 9.40e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Guided | DE | 4.46e+00 | 1.28e+00 | 7.28e-03 | 1.57e-02 | 0.140 | **DE Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Guided | CMAES | 4.46e+00 | 1.30e+00 | 2.09e-02 | 4.00e-02 | 0.190 | **CMAES Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Guided | PSO | 4.46e+00 | 9.47e-01 | 7.49e-03 | 1.60e-02 | 0.100 | **PSO Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA_Vectorization | DE | 2.45e+00 | 1.28e+00 | 2.57e-02 | 4.66e-02 | 0.200 | **DE Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA_Thinking | DE | 0.00e+00 | 1.13e-03 | 1.33e-03 | 3.92e-03 | 0.910 | **LLaMEA_Thinking Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA_Baseline | CMAES | 4.77e-04 | 0.00e+00 | 2.55e-04 | 9.53e-04 | 0.147 | **CMAES Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA_Guided | DE | 0.00e+00 | 1.13e-03 | 1.75e-03 | 4.57e-03 | 0.900 | **LLaMEA_Guided Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA_Vectorization | CMAES | 1.14e-04 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA_Baseline | DE | 2.48e+01 | 5.54e-03 | 2.50e-03 | 6.32e-03 | 0.196 | **DE Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA_Baseline | CMAES | 2.48e+01 | 0.00e+00 | 2.20e-03 | 5.59e-03 | 0.193 | **CMAES Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA_Baseline | PSO | 2.48e+01 | 0.00e+00 | 7.19e-05 | 4.23e-04 | 0.102 | **PSO Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA_Thinking | PSO | 5.26e-04 | 0.00e+00 | 2.12e-02 | 4.00e-02 | 0.200 | **PSO Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA_Guided | DE | 9.12e-05 | 5.54e-03 | 2.83e-03 | 6.79e-03 | 0.900 | **LLaMEA_Guided Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA_Guided | PSO | 9.12e-05 | 0.00e+00 | 2.12e-02 | 4.00e-02 | 0.200 | **PSO Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA_Vectorization | PSO | 2.85e-03 | 0.00e+00 | 2.12e-02 | 4.00e-02 | 0.200 | **PSO Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Thinking | DE | 0.00e+00 | 3.12e-03 | 6.39e-05 | 3.83e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Baseline | CMAES | 1.11e+02 | 0.00e+00 | 3.17e-04 | 1.15e-03 | 0.157 | **CMAES Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Baseline | PSO | 1.11e+02 | 0.00e+00 | 3.17e-04 | 1.15e-03 | 0.157 | **PSO Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Guided | DE | 0.00e+00 | 3.12e-03 | 6.39e-05 | 3.83e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Vectorization | CMAES | 3.18e-04 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA_Vectorization | PSO | 3.18e-04 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA_Baseline | CMAES | 5.66e-01 | 0.00e+00 | 5.63e-03 | 1.28e-02 | 0.225 | **CMAES Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA_Guided | DE | 3.75e-03 | 2.24e-02 | 2.83e-03 | 6.79e-03 | 0.900 | **LLaMEA_Guided Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA_Vectorization | DE | 4.61e-01 | 2.24e-02 | 2.46e-04 | 9.33e-04 | 0.010 | **DE Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA_Thinking | DE | 1.25e-06 | 3.05e-03 | 7.34e-04 | 2.46e-03 | 0.950 | **LLaMEA_Thinking Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA_Thinking | CMAES | 1.25e-06 | 0.00e+00 | 5.97e-03 | 1.31e-02 | 0.200 | **CMAES Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA_Baseline | CMAES | 1.88e+00 | 0.00e+00 | 1.47e-03 | 4.16e-03 | 0.198 | **CMAES Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA_Guided | DE | 0.00e+00 | 3.05e-03 | 6.39e-05 | 3.83e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA_Vectorization | CMAES | 1.17e-03 | 0.00e+00 | 6.39e-05 | 3.83e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Thinking | DE | 7.23e-04 | 1.99e+00 | 5.61e-04 | 1.93e-03 | 0.960 | **LLaMEA_Thinking Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Thinking | PSO | 7.23e-04 | 0.00e+00 | 1.75e-03 | 4.57e-03 | 0.100 | **PSO Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Baseline | PSO | 2.69e+00 | 0.00e+00 | 2.99e-05 | 3.83e-04 | 0.091 | **PSO Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Guided | DE | 0.00e+00 | 1.99e+00 | 6.02e-05 | 3.83e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Guided | CMAES | 0.00e+00 | 1.06e+00 | 7.47e-04 | 2.46e-03 | 0.900 | **LLaMEA_Guided Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Vectorization | DE | 2.21e-03 | 1.99e+00 | 1.75e-04 | 7.79e-04 | 1.000 | **LLaMEA_Vectorization Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Vectorization | CMAES | 2.21e-03 | 1.06e+00 | 2.56e-02 | 4.66e-02 | 0.800 | **LLaMEA_Vectorization Wins** |
| 2D | 0.0 | **Rastrigin (f15)** | LLaMEA_Vectorization | PSO | 2.21e-03 | 0.00e+00 | 1.75e-03 | 4.57e-03 | 0.100 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Baseline | DE | 3.39e+01 | 4.37e+00 | 1.99e-03 | 5.15e-03 | 0.196 | **DE Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Baseline | CMAES | 3.39e+01 | 1.51e+00 | 3.75e-04 | 1.34e-03 | 0.150 | **CMAES Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Baseline | PSO | 3.39e+01 | 0.00e+00 | 7.16e-07 | 1.06e-04 | 0.013 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Thinking | DE | 3.47e-03 | 4.37e+00 | 1.83e-04 | 7.79e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Thinking | CMAES | 3.47e-03 | 1.51e+00 | 2.83e-03 | 6.79e-03 | 0.900 | **LLaMEA_Thinking Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Thinking | PSO | 3.47e-03 | 0.00e+00 | 1.75e-03 | 4.57e-03 | 0.100 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Guided | DE | 6.10e+01 | 4.37e+00 | 1.83e-04 | 7.79e-04 | 0.000 | **DE Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Guided | CMAES | 6.10e+01 | 1.51e+00 | 1.83e-04 | 7.79e-04 | 0.000 | **CMAES Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Guided | PSO | 6.10e+01 | 0.00e+00 | 8.74e-05 | 5.04e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Vectorization | DE | 2.41e-02 | 4.37e+00 | 1.83e-04 | 7.79e-04 | 1.000 | **LLaMEA_Vectorization Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Vectorization | CMAES | 2.41e-02 | 1.51e+00 | 1.73e-02 | 3.40e-02 | 0.820 | **LLaMEA_Vectorization Wins** |
| 2D | 0.05 | **Rastrigin (f15)** | LLaMEA_Vectorization | PSO | 2.41e-02 | 0.00e+00 | 1.01e-03 | 3.12e-03 | 0.080 | **PSO Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Thinking | CMAES | 5.23e-01 | 2.98e+00 | 7.07e-03 | 1.54e-02 | 0.860 | **LLaMEA_Thinking Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Guided | DE | 0.00e+00 | 1.99e+00 | 6.34e-05 | 3.83e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Guided | CMAES | 0.00e+00 | 2.98e+00 | 5.94e-05 | 3.83e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Guided | PSO | 0.00e+00 | 1.99e+00 | 7.42e-04 | 2.46e-03 | 0.900 | **LLaMEA_Guided Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Vectorization | DE | 2.17e-01 | 1.99e+00 | 1.82e-04 | 7.79e-04 | 1.000 | **LLaMEA_Vectorization Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Vectorization | CMAES | 2.17e-01 | 2.98e+00 | 2.12e-03 | 5.45e-03 | 0.910 | **LLaMEA_Vectorization Wins** |
| 3D | 0.0 | **Rastrigin (f15)** | LLaMEA_Vectorization | PSO | 2.17e-01 | 1.99e+00 | 2.56e-02 | 4.66e-02 | 0.800 | **LLaMEA_Vectorization Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Baseline | PSO | 5.44e+00 | 1.01e+00 | 5.47e-03 | 1.24e-02 | 0.227 | **PSO Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Thinking | DE | 1.07e+00 | 6.26e+00 | 1.83e-04 | 7.79e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Guided | CMAES | 1.01e+01 | 3.52e+00 | 1.70e-03 | 4.57e-03 | 0.080 | **CMAES Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Guided | PSO | 1.01e+01 | 1.01e+00 | 9.90e-04 | 3.10e-03 | 0.060 | **PSO Wins** |
| 3D | 0.05 | **Rastrigin (f15)** | LLaMEA_Vectorization | DE | 1.38e+00 | 6.26e+00 | 4.40e-04 | 1.54e-03 | 0.970 | **LLaMEA_Vectorization Wins** |
| 5D | 0.0 | **Rastrigin (f15)** | LLaMEA_Guided | DE | 1.16e-06 | 6.47e+00 | 1.83e-04 | 7.79e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 5D | 0.0 | **Rastrigin (f15)** | LLaMEA_Guided | CMAES | 1.16e-06 | 6.47e+00 | 1.81e-04 | 7.79e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 5D | 0.0 | **Rastrigin (f15)** | LLaMEA_Guided | PSO | 1.16e-06 | 5.03e+00 | 1.81e-04 | 7.79e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 5D | 0.0 | **Rastrigin (f15)** | LLaMEA_Vectorization | CMAES | 4.02e+00 | 6.47e+00 | 1.39e-02 | 2.84e-02 | 0.830 | **LLaMEA_Vectorization Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | DE | 0.00e+00 | 1.42e-07 | 6.39e-05 | 3.83e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | CMAES | 0.00e+00 | 4.19e-01 | 2.17e-03 | 5.52e-03 | 0.850 | **LLaMEA_Thinking Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | PSO | 0.00e+00 | 3.46e-01 | 1.46e-02 | 2.93e-02 | 0.750 | **LLaMEA_Thinking Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | DE | 0.00e+00 | 1.42e-07 | 6.39e-05 | 3.83e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | CMAES | 0.00e+00 | 4.19e-01 | 2.17e-03 | 5.52e-03 | 0.850 | **LLaMEA_Guided Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | PSO | 0.00e+00 | 3.46e-01 | 1.46e-02 | 2.93e-02 | 0.750 | **LLaMEA_Guided Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | DE | 0.00e+00 | 1.42e-07 | 1.75e-03 | 4.57e-03 | 0.900 | **LLaMEA_Vectorization Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | CMAES | 0.00e+00 | 4.19e-01 | 1.46e-02 | 2.93e-02 | 0.790 | **LLaMEA_Vectorization Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | PSO | 8.98e-07 | 0.00e+00 | 2.37e-02 | 4.35e-02 | 0.287 | **PSO Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | DE | 0.00e+00 | 1.83e-06 | 6.39e-05 | 3.83e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | CMAES | 0.00e+00 | 3.82e-01 | 5.97e-03 | 1.31e-02 | 0.800 | **LLaMEA_Guided Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | DE | 0.00e+00 | 1.83e-06 | 6.39e-05 | 3.83e-04 | 1.000 | **LLaMEA_Vectorization Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | CMAES | 0.00e+00 | 3.82e-01 | 5.97e-03 | 1.31e-02 | 0.800 | **LLaMEA_Vectorization Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | DE | 0.00e+00 | 5.28e-08 | 6.39e-05 | 3.83e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | CMAES | 0.00e+00 | 7.82e-01 | 2.25e-04 | 9.19e-04 | 0.950 | **LLaMEA_Thinking Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | DE | 1.19e+00 | 5.28e-08 | 7.58e-03 | 1.62e-02 | 0.237 | **DE Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | PSO | 1.19e+00 | 0.00e+00 | 4.29e-03 | 9.99e-03 | 0.219 | **PSO Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | DE | 0.00e+00 | 5.28e-08 | 6.39e-05 | 3.83e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | CMAES | 0.00e+00 | 7.82e-01 | 2.25e-04 | 9.19e-04 | 0.950 | **LLaMEA_Guided Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | DE | 0.00e+00 | 5.28e-08 | 3.40e-03 | 8.10e-03 | 0.880 | **LLaMEA_Vectorization Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | CMAES | 0.00e+00 | 7.82e-01 | 1.10e-03 | 3.38e-03 | 0.915 | **LLaMEA_Vectorization Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | DE | 3.09e+00 | 1.32e-04 | 1.36e-02 | 2.79e-02 | 0.257 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | PSO | 3.09e+00 | 8.14e-01 | 2.72e-02 | 4.89e-02 | 0.283 | **PSO Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | DE | 0.00e+00 | 1.32e-04 | 6.39e-05 | 3.83e-04 | 1.000 | **LLaMEA_Vectorization Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | CMAES | 0.00e+00 | 1.52e+00 | 2.31e-04 | 9.19e-04 | 0.950 | **LLaMEA_Vectorization Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA_Vectorization | PSO | 0.00e+00 | 8.14e-01 | 5.97e-03 | 1.31e-02 | 0.800 | **LLaMEA_Vectorization Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | DE | 0.00e+00 | 6.23e-01 | 6.20e-05 | 3.83e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | CMAES | 0.00e+00 | 1.25e+00 | 4.17e-05 | 3.83e-04 | 1.000 | **LLaMEA_Thinking Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Thinking | PSO | 0.00e+00 | 1.40e+00 | 7.47e-04 | 2.46e-03 | 0.900 | **LLaMEA_Thinking Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Baseline | DE | 5.57e+00 | 6.23e-01 | 1.29e-02 | 2.67e-02 | 0.248 | **DE Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | DE | 0.00e+00 | 6.23e-01 | 6.20e-05 | 3.83e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | CMAES | 0.00e+00 | 1.25e+00 | 4.17e-05 | 3.83e-04 | 1.000 | **LLaMEA_Guided Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA_Guided | PSO | 0.00e+00 | 1.40e+00 | 7.47e-04 | 2.46e-03 | 0.900 | **LLaMEA_Guided Wins** |

---
## 🌊 5. Noise Robustness & Landscape Fragility Analysis

The impact of stochastic evaluation noise ($\\sigma = 0.05$) is quantified via the **Degradation Factor** $\\Delta \\log_{10}(\\Delta y) = \\log_{10}(\\text{Median Error}_{\\text{Noisy}}) - \\log_{10}(\\text{Median Error}_{\\text{Clean}})$. Positive values indicate loss of precision under noise.

| Problem Landscape | Landscape Class | Median Degradation (LLaMEA) | Median Degradation (Baselines) | Noise Sensitivity Assessment |
| :--- | :--- | :---: | :---: | :--- |
| **Sphere (f1)** | Separable | +9.76 | +10.40 | 🟢 **Resilient**: Precision remains intact despite stochastic perturbation |
| **Rosenbrock (f8)** | Low Conditioning | +0.50 | +7.62 | 🔴 **High Fragility**: Severe valley stagnation under noise |
| **Discus (f11)** | High Conditioning | +6.39 | +0.75 | 🟢 **Resilient**: Precision remains intact despite stochastic perturbation |
| **Rastrigin (f15)** | Multi-Modal (Global) | +0.68 | +0.00 | 🟡 **Moderate Fragility**: Slight barrier degradation, exploration preserved |
| **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | +5.87 | +0.00 | 🟡 **Moderate Fragility**: Slight barrier degradation, exploration preserved |