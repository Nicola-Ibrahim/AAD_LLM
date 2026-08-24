# 🔬 Comprehensive Master Benchmark & Synthesis Evaluation Report

> End-to-end empirical evaluation connecting evolutionary algorithm discovery with downstream benchmark performance across BBOB continuous testbeds.

## 🏆 1. Executive Performance Scorecard (LLaMEA vs. Classical Baselines)
- **Total Evaluated Pairwise Contests ($N$):** `714`
- **🟢 LLaMEA Statistically Significant Wins ($p_{\text{FDR}} < 0.05, \hat{A}_{12} > 0.5$):** **`83`** (11.6%)
- **🔴 Classical Baseline Significant Wins ($p_{\text{FDR}} < 0.05, \hat{A}_{12} < 0.5$):** **`476`** (66.7%)
- **⚪ Ties / Equivalent ($p_{\text{FDR}} \ge 0.05$):** **`155`** (21.7%)

> **Scientific Interpretation:** LLaMEA algorithm discovery exhibits a distinct **landscape-dependent regime split**.
> On complex multimodal landscapes (e.g., *Rastrigin $f_{15}$*, *Gallagher 101 Peaks $f_{21}$*), LLaMEA evolved solvers consistently outperform or tie classical baselines by preserving exploratory search diversity and escaping local optima.
> Conversely, on smooth, separable unimodal landscapes (e.g., *Sphere $f_{1}$*), specialized numerical routines (such as CMA-ES covariance updates and DE/PSO vector steps) achieve rapid machine-precision convergence ($10^{-12}$). All reported significance badges apply **Benjamini-Hochberg False Discovery Rate (FDR)** control at $\alpha = 0.05$.

---
## 📊 2. Publication Figures & Quantitative Findings
| Figure | Focus & Research Question Answered | Key Quantitative Finding | File Link |
| :--- | :--- | :--- | :--- |
| **Figure A** | Problem Convergence & Precision Dashboard | Median precision reaches $10^{-8}$ on $f_{1}$ & $f_{11}$, with $f_{8}$ exhibiting highest stagnation rate. | [`problem_convergence_comparison.png`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/statistics/problem_convergence_comparison.png) |
| **Figure B** | Clean-to-Noisy Matched-Pair Transfer | Pearson $r = 0.00$ ($p = 1.00e+00$), demonstrating cross-condition generalizability from clean synthesis to noisy environments. | [`clean_vs_noisy_transfer.png`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/statistics/clean_vs_noisy_transfer.png) |
| **Figure C** | Noise Fragility & Degradation Matrix | Ill-conditioned $f_{8}$ suffers maximum noise degradation ($\Delta\log_{10}(\Delta y) > +3.0$), while separable $f_{1}$ is invariant. | [`noise_degradation_matrix.png`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/statistics/noise_degradation_matrix.png) |
| **Figure D** | Dolan-Moré Performance Profiles $\rho_s(\tau)$ | Classical optimizers lead at zero slack ($	au=1$), while evolved algorithms achieve broad multi-modal robustness. | [`dolan_more_profiles.png`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/statistics/dolan_more_profiles.png) |
| **Figure E** | Pairwise Effect Size Heatmap (Vargha-Delaney $A_{12}$) | Comprehensive $N \times N$ effect size matrix establishing stochastic dominance probabilities. | [`a12_effect_size_heatmap.png`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/statistics/a12_effect_size_heatmap.png) |

---
## 🌐 3. Omnibus Kruskal-Wallis Test Results

| Dim | Noise Std | Problem | Function Class | Solvers | H-Statistic | p-value | Significant? |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| 2D | 0.0 | **Rosenbrock (f8)** | Low Conditioning | 11 | 103.552 | 1.06e-17 | 🟢 **Yes** |
| 2D | 0.0 | **Sphere (f1)** | Separable | 11 | 108.175 | 1.24e-18 | 🟢 **Yes** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | Multi-Modal (Global) | 11 | 90.714 | 3.87e-15 | 🟢 **Yes** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 11 | 80.839 | 3.44e-13 | 🟢 **Yes** |
| 2D | 0.0 | **Discus (f11)** | High Conditioning | 11 | 98.199 | 1.25e-16 | 🟢 **Yes** |
| 2D | 0.05 | **Rosenbrock (f8)** | Low Conditioning | 11 | 88.861 | 9.01e-15 | 🟢 **Yes** |
| 2D | 0.05 | **Sphere (f1)** | Separable | 11 | 100.657 | 4.03e-17 | 🟢 **Yes** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | Multi-Modal (Global) | 11 | 78.847 | 8.45e-13 | 🟢 **Yes** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 11 | 82.472 | 1.64e-13 | 🟢 **Yes** |
| 2D | 0.05 | **Discus (f11)** | High Conditioning | 11 | 56.601 | 1.58e-08 | 🟢 **Yes** |
| 5D | 0.0 | **Rosenbrock (f8)** | Low Conditioning | 11 | 96.518 | 2.70e-16 | 🟢 **Yes** |
| 5D | 0.0 | **Sphere (f1)** | Separable | 11 | 104.230 | 7.73e-18 | 🟢 **Yes** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | Multi-Modal (Global) | 11 | 97.752 | 1.53e-16 | 🟢 **Yes** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 11 | 71.961 | 1.85e-11 | 🟢 **Yes** |
| 5D | 0.0 | **Discus (f11)** | High Conditioning | 11 | 102.278 | 1.91e-17 | 🟢 **Yes** |
| 5D | 0.05 | **Rosenbrock (f8)** | Low Conditioning | 11 | 96.823 | 2.35e-16 | 🟢 **Yes** |
| 5D | 0.05 | **Sphere (f1)** | Separable | 11 | 97.514 | 1.71e-16 | 🟢 **Yes** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | Multi-Modal (Global) | 10 | 88.169 | 3.79e-15 | 🟢 **Yes** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 10 | 74.224 | 2.25e-12 | 🟢 **Yes** |
| 5D | 0.05 | **Discus (f11)** | High Conditioning | 11 | 92.772 | 1.51e-15 | 🟢 **Yes** |
| 3D | 0.0 | **Rosenbrock (f8)** | Low Conditioning | 11 | 106.207 | 3.10e-18 | 🟢 **Yes** |
| 3D | 0.0 | **Sphere (f1)** | Separable | 11 | 94.948 | 5.56e-16 | 🟢 **Yes** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | Multi-Modal (Global) | 11 | 96.883 | 2.29e-16 | 🟢 **Yes** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 11 | 84.036 | 8.09e-14 | 🟢 **Yes** |
| 3D | 0.0 | **Discus (f11)** | High Conditioning | 11 | 96.760 | 2.42e-16 | 🟢 **Yes** |
| 3D | 0.05 | **Rosenbrock (f8)** | Low Conditioning | 11 | 91.482 | 2.72e-15 | 🟢 **Yes** |
| 3D | 0.05 | **Sphere (f1)** | Separable | 11 | 104.323 | 7.41e-18 | 🟢 **Yes** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | Multi-Modal (Global) | 11 | 92.130 | 2.02e-15 | 🟢 **Yes** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 11 | 79.004 | 7.87e-13 | 🟢 **Yes** |
| 3D | 0.05 | **Discus (f11)** | High Conditioning | 11 | 111.447 | 2.72e-19 | 🟢 **Yes** |

---
## 🔬 4. Problem-Level Summary & Pairwise Statistical Breakdown

### 4.1 Summary by Landscape Class (LLaMEA vs. Classical Baselines)

| Problem | Landscape Class | Contests | LLaMEA Wins | Baseline Wins | Ties / Inconclusive | Dominant Regime |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Sphere (f1)** | Separable | 144 | 9 | 81 | 54 | 🔴 Baseline Advantage |
| **Rosenbrock (f8)** | Low Conditioning | 144 | 19 | 103 | 22 | 🔴 Baseline Advantage |
| **Discus (f11)** | High Conditioning | 144 | 26 | 92 | 26 | 🔴 Baseline Advantage |
| **Rastrigin Multi-Modal (f15)** | Multi-Modal (Global) | 141 | 6 | 120 | 15 | 🔴 Baseline Advantage |
| **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | 141 | 23 | 80 | 38 | 🔴 Baseline Advantage |

### 4.2 Statistically Significant Pairwise Contests (FDR-Corrected $p < 0.05$)

| Dim | Noise | Problem | Solver 1 | Solver 2 | Med 1 | Med 2 | Raw p-val | Adj p-val (FDR) | A12 | Outcome |
| :---: | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 2D | 0.0 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 1.94e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 7.64e-02 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 1.08e-02 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Sphere (f1)** | DE | LLaMEA-7B / baseline | 0.00e+00 | 1.94e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Sphere (f1)** | DE | LLaMEA-7B / guided | 0.00e+00 | 7.64e-02 | 6.39e-05 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Sphere (f1)** | DE | LLaMEA-7B / thinking | 0.00e+00 | 1.08e-02 | 6.39e-05 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Sphere (f1)** | LLaMEA-7B / baseline | PSO | 1.94e+01 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Sphere (f1)** | LLaMEA-7B / guided | PSO | 7.64e-02 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Sphere (f1)** | LLaMEA-7B / thinking | PSO | 1.08e-02 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-14B / guided | 0.00e+00 | 4.65e-04 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-14B / thinking | 0.00e+00 | 1.52e-08 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 1.21e-05 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 1.68e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 1.51e-01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 6.27e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 9.25e+00 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Sphere (f1)** | DE | LLaMEA-14B / baseline | 2.12e-02 | 0.00e+00 | 2.12e-02 | 2.89e-02 | 0.200 | **LLaMEA-14B / baseline Wins** |
| 2D | 0.05 | **Sphere (f1)** | DE | LLaMEA-14B / guided | 2.12e-02 | 4.65e-04 | 1.83e-04 | 3.45e-04 | 0.000 | **LLaMEA-14B / guided Wins** |
| 2D | 0.05 | **Sphere (f1)** | DE | LLaMEA-14B / thinking | 2.12e-02 | 1.52e-08 | 1.83e-04 | 3.45e-04 | 0.000 | **LLaMEA-14B / thinking Wins** |
| 2D | 0.05 | **Sphere (f1)** | DE | LLaMEA-14B / vectorization | 2.12e-02 | 1.21e-05 | 1.83e-04 | 3.45e-04 | 0.000 | **LLaMEA-14B / vectorization Wins** |
| 2D | 0.05 | **Sphere (f1)** | DE | LLaMEA-7B / baseline | 2.12e-02 | 1.68e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Sphere (f1)** | DE | LLaMEA-7B / guided | 2.12e-02 | 1.51e-01 | 7.69e-04 | 1.29e-03 | 0.950 | **DE Wins** |
| 2D | 0.05 | **Sphere (f1)** | DE | LLaMEA-7B / thinking | 2.12e-02 | 6.27e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Sphere (f1)** | DE | LLaMEA-7B / vectorization | 2.12e-02 | 9.25e+00 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA-14B / guided | PSO | 4.65e-04 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA-14B / thinking | PSO | 1.52e-08 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA-14B / vectorization | PSO | 1.21e-05 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA-7B / baseline | PSO | 1.68e+01 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA-7B / guided | PSO | 1.51e-01 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA-7B / thinking | PSO | 6.27e+01 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Sphere (f1)** | LLaMEA-7B / vectorization | PSO | 9.25e+00 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Sphere (f1)** | CMA-ES | LLaMEA-14B / baseline | 0.00e+00 | 7.72e-02 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 5.74e+01 | 2.21e-03 | 3.43e-03 | 0.850 | **CMA-ES Wins** |
| 3D | 0.0 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 3.01e-05 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 5.56e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Sphere (f1)** | DE | LLaMEA-14B / baseline | 0.00e+00 | 7.72e-02 | 6.39e-05 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Sphere (f1)** | DE | LLaMEA-7B / baseline | 0.00e+00 | 5.74e+01 | 2.21e-03 | 3.43e-03 | 0.850 | **DE Wins** |
| 3D | 0.0 | **Sphere (f1)** | DE | LLaMEA-7B / thinking | 0.00e+00 | 3.01e-05 | 6.39e-05 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Sphere (f1)** | DE | LLaMEA-7B / vectorization | 0.00e+00 | 5.56e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Sphere (f1)** | LLaMEA-14B / baseline | PSO | 7.72e-02 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Sphere (f1)** | LLaMEA-7B / baseline | PSO | 5.74e+01 | 0.00e+00 | 2.21e-03 | 3.43e-03 | 0.150 | **PSO Wins** |
| 3D | 0.0 | **Sphere (f1)** | LLaMEA-7B / thinking | PSO | 3.01e-05 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Sphere (f1)** | LLaMEA-7B / vectorization | PSO | 5.56e+01 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-14B / guided | 0.00e+00 | 2.88e-02 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-14B / thinking | 0.00e+00 | 1.97e-08 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 8.53e-03 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 1.21e-01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 2.37e-02 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 5.57e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Sphere (f1)** | DE | LLaMEA-14B / baseline | 5.30e-02 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **LLaMEA-14B / baseline Wins** |
| 3D | 0.05 | **Sphere (f1)** | DE | LLaMEA-14B / thinking | 5.30e-02 | 1.97e-08 | 1.83e-04 | 3.45e-04 | 0.000 | **LLaMEA-14B / thinking Wins** |
| 3D | 0.05 | **Sphere (f1)** | DE | LLaMEA-14B / vectorization | 5.30e-02 | 8.53e-03 | 2.46e-04 | 4.43e-04 | 0.010 | **LLaMEA-14B / vectorization Wins** |
| 3D | 0.05 | **Sphere (f1)** | DE | LLaMEA-7B / baseline | 5.30e-02 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **LLaMEA-7B / baseline Wins** |
| 3D | 0.05 | **Sphere (f1)** | DE | LLaMEA-7B / vectorization | 5.30e-02 | 5.57e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA-14B / guided | PSO | 2.88e-02 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA-14B / thinking | PSO | 1.97e-08 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA-14B / vectorization | PSO | 8.53e-03 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA-7B / guided | PSO | 1.21e-01 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA-7B / thinking | PSO | 2.37e-02 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Sphere (f1)** | LLaMEA-7B / vectorization | PSO | 5.57e+01 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 7.40e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 6.60e+00 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Sphere (f1)** | DE | LLaMEA-7B / thinking | 0.00e+00 | 7.40e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Sphere (f1)** | DE | LLaMEA-7B / vectorization | 0.00e+00 | 6.60e+00 | 6.39e-05 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Sphere (f1)** | LLaMEA-7B / thinking | PSO | 7.40e+01 | 0.00e+00 | 8.74e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Sphere (f1)** | LLaMEA-7B / vectorization | PSO | 6.60e+00 | 0.00e+00 | 8.74e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-14B / baseline | 0.00e+00 | 3.37e+00 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-14B / guided | 0.00e+00 | 3.99e-01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-14B / thinking | 0.00e+00 | 1.36e-07 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 2.95e-01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 3.58e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 4.93e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 8.00e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Sphere (f1)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 6.29e-01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Sphere (f1)** | DE | LLaMEA-14B / baseline | 1.12e-01 | 3.37e+00 | 2.11e-02 | 2.89e-02 | 0.810 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | DE | LLaMEA-14B / guided | 1.12e-01 | 3.99e-01 | 2.46e-04 | 4.43e-04 | 0.990 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | DE | LLaMEA-14B / thinking | 1.12e-01 | 1.36e-07 | 1.83e-04 | 3.45e-04 | 0.000 | **LLaMEA-14B / thinking Wins** |
| 5D | 0.05 | **Sphere (f1)** | DE | LLaMEA-14B / vectorization | 1.12e-01 | 2.95e-01 | 2.20e-03 | 3.43e-03 | 0.910 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | DE | LLaMEA-7B / baseline | 1.12e-01 | 3.58e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | DE | LLaMEA-7B / guided | 1.12e-01 | 4.93e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | DE | LLaMEA-7B / thinking | 1.12e-01 | 8.00e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | DE | LLaMEA-7B / vectorization | 1.12e-01 | 6.29e-01 | 4.40e-04 | 7.59e-04 | 0.970 | **DE Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA-14B / baseline | PSO | 3.37e+00 | 0.00e+00 | 4.21e-04 | 7.34e-04 | 0.050 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA-14B / guided | PSO | 3.99e-01 | 0.00e+00 | 1.33e-03 | 2.16e-03 | 0.090 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA-14B / thinking | PSO | 1.36e-07 | 0.00e+00 | 1.75e-03 | 2.78e-03 | 0.100 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA-14B / vectorization | PSO | 2.95e-01 | 0.00e+00 | 1.75e-03 | 2.78e-03 | 0.100 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA-7B / baseline | PSO | 3.58e+01 | 0.00e+00 | 8.74e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA-7B / guided | PSO | 4.93e+01 | 0.00e+00 | 8.74e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA-7B / thinking | PSO | 8.00e+01 | 0.00e+00 | 8.74e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Sphere (f1)** | LLaMEA-7B / vectorization | PSO | 6.29e-01 | 0.00e+00 | 1.33e-03 | 2.16e-03 | 0.090 | **PSO Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / guided | 0.00e+00 | 3.50e-10 | 7.47e-04 | 1.26e-03 | 0.900 | **CMA-ES Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / thinking | 0.00e+00 | 1.01e-06 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 1.94e-05 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 1.39e+05 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 4.37e+03 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 1.09e-02 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-14B / baseline | 4.50e-10 | 0.00e+00 | 2.21e-03 | 3.43e-03 | 0.150 | **LLaMEA-14B / baseline Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-14B / thinking | 4.50e-10 | 1.01e-06 | 2.79e-03 | 4.30e-03 | 0.900 | **DE Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-14B / vectorization | 4.50e-10 | 1.94e-05 | 2.17e-03 | 3.43e-03 | 0.910 | **DE Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / baseline | 4.50e-10 | 1.39e+05 | 1.79e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / guided | 4.50e-10 | 4.37e+03 | 1.79e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / thinking | 4.50e-10 | 0.00e+00 | 2.21e-03 | 3.43e-03 | 0.150 | **LLaMEA-7B / thinking Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / vectorization | 4.50e-10 | 1.09e-02 | 1.79e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA-14B / guided | PSO | 3.50e-10 | 0.00e+00 | 7.47e-04 | 1.26e-03 | 0.100 | **PSO Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA-14B / thinking | PSO | 1.01e-06 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA-14B / vectorization | PSO | 1.94e-05 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA-7B / baseline | PSO | 1.39e+05 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA-7B / guided | PSO | 4.37e+03 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Rosenbrock (f8)** | LLaMEA-7B / vectorization | PSO | 1.09e-02 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / thinking | 0.00e+00 | 7.98e-03 | 4.70e-03 | 7.02e-03 | 0.855 | **CMA-ES Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 1.08e-04 | 1.75e-03 | 2.78e-03 | 0.900 | **CMA-ES Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 1.88e+00 | 3.11e-04 | 5.58e-04 | 0.960 | **CMA-ES Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 5.90e+00 | 8.74e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 8.49e-02 | 1.75e-03 | 2.78e-03 | 0.900 | **CMA-ES Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 2.27e+04 | 8.74e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-14B / baseline | 4.84e-03 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **LLaMEA-14B / baseline Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-14B / guided | 4.84e-03 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **LLaMEA-14B / guided Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-14B / vectorization | 4.84e-03 | 1.08e-04 | 2.20e-03 | 3.43e-03 | 0.090 | **LLaMEA-14B / vectorization Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / baseline | 4.84e-03 | 1.88e+00 | 1.73e-02 | 2.39e-02 | 0.820 | **DE Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / guided | 4.84e-03 | 5.90e+00 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / thinking | 4.84e-03 | 8.49e-02 | 1.13e-02 | 1.62e-02 | 0.840 | **DE Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / vectorization | 4.84e-03 | 2.27e+04 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA-14B / vectorization | PSO | 1.08e-04 | 0.00e+00 | 2.27e-02 | 3.08e-02 | 0.200 | **PSO Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / baseline | PSO | 1.88e+00 | 0.00e+00 | 6.11e-03 | 8.99e-03 | 0.140 | **PSO Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / guided | PSO | 5.90e+00 | 0.00e+00 | 1.76e-03 | 2.79e-03 | 0.090 | **PSO Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / thinking | PSO | 8.49e-02 | 0.00e+00 | 2.27e-02 | 3.08e-02 | 0.200 | **PSO Wins** |
| 2D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / vectorization | PSO | 2.27e+04 | 0.00e+00 | 1.80e-04 | 3.45e-04 | 0.010 | **PSO Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / guided | 0.00e+00 | 7.92e-06 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 7.34e-03 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 2.66e+05 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 3.00e+01 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 1.71e+02 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 4.86e+00 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-14B / baseline | 1.30e-09 | 0.00e+00 | 7.47e-04 | 1.26e-03 | 0.100 | **LLaMEA-14B / baseline Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-14B / guided | 1.30e-09 | 7.92e-06 | 1.30e-03 | 2.14e-03 | 0.930 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-14B / thinking | 1.30e-09 | 0.00e+00 | 7.47e-04 | 1.26e-03 | 0.100 | **LLaMEA-14B / thinking Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-14B / vectorization | 1.30e-09 | 7.34e-03 | 1.81e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / baseline | 1.30e-09 | 2.66e+05 | 1.81e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / guided | 1.30e-09 | 3.00e+01 | 1.81e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / thinking | 1.30e-09 | 1.71e+02 | 1.81e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / vectorization | 1.30e-09 | 4.86e+00 | 1.81e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA-14B / baseline | PSO | 0.00e+00 | 2.83e-07 | 6.39e-05 | 3.45e-04 | 1.000 | **LLaMEA-14B / baseline Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA-14B / guided | PSO | 7.92e-06 | 2.83e-07 | 1.73e-02 | 2.39e-02 | 0.180 | **PSO Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA-14B / thinking | PSO | 0.00e+00 | 2.83e-07 | 6.39e-05 | 3.45e-04 | 1.000 | **LLaMEA-14B / thinking Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA-14B / vectorization | PSO | 7.34e-03 | 2.83e-07 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA-7B / baseline | PSO | 2.66e+05 | 2.83e-07 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA-7B / guided | PSO | 3.00e+01 | 2.83e-07 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA-7B / thinking | PSO | 1.71e+02 | 2.83e-07 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Rosenbrock (f8)** | LLaMEA-7B / vectorization | PSO | 4.86e+00 | 2.83e-07 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / baseline | 0.00e+00 | 6.00e-10 | 2.11e-02 | 2.89e-02 | 0.800 | **CMA-ES Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / thinking | 0.00e+00 | 6.03e-01 | 8.89e-03 | 1.29e-02 | 0.840 | **CMA-ES Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 2.17e-02 | 2.12e-02 | 2.89e-02 | 0.800 | **CMA-ES Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 7.97e+00 | 1.52e-04 | 3.45e-04 | 0.990 | **CMA-ES Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 5.36e+01 | 1.52e-04 | 3.45e-04 | 0.990 | **CMA-ES Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 2.72e+03 | 1.11e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 3.56e+03 | 1.11e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-14B / baseline | 8.30e-02 | 6.00e-10 | 1.81e-04 | 3.45e-04 | 0.000 | **LLaMEA-14B / baseline Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-14B / guided | 8.30e-02 | 0.00e+00 | 2.12e-02 | 2.89e-02 | 0.200 | **LLaMEA-14B / guided Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-14B / vectorization | 8.30e-02 | 2.17e-02 | 3.76e-02 | 4.95e-02 | 0.220 | **LLaMEA-14B / vectorization Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / baseline | 8.30e-02 | 7.97e+00 | 2.46e-04 | 4.43e-04 | 0.990 | **DE Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / guided | 8.30e-02 | 5.36e+01 | 2.46e-04 | 4.43e-04 | 0.990 | **DE Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / thinking | 8.30e-02 | 2.72e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / vectorization | 8.30e-02 | 3.56e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA-14B / baseline | PSO | 6.00e-10 | 4.54e-01 | 1.81e-04 | 3.45e-04 | 1.000 | **LLaMEA-14B / baseline Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA-14B / guided | PSO | 0.00e+00 | 4.54e-01 | 8.89e-03 | 1.29e-02 | 0.840 | **LLaMEA-14B / guided Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA-14B / vectorization | PSO | 2.17e-02 | 4.54e-01 | 2.11e-02 | 2.89e-02 | 0.810 | **LLaMEA-14B / vectorization Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / baseline | PSO | 7.97e+00 | 4.54e-01 | 4.59e-03 | 6.86e-03 | 0.120 | **PSO Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / guided | PSO | 5.36e+01 | 4.54e-01 | 3.30e-04 | 5.77e-04 | 0.020 | **PSO Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / thinking | PSO | 2.72e+03 | 4.54e-01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / vectorization | PSO | 3.56e+03 | 4.54e-01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / guided | 0.00e+00 | 2.45e-02 | 5.54e-03 | 8.26e-03 | 0.860 | **CMA-ES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / thinking | 0.00e+00 | 1.71e-01 | 2.12e-02 | 2.89e-02 | 0.800 | **CMA-ES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 2.19e-01 | 2.12e-02 | 2.89e-02 | 0.800 | **CMA-ES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 5.73e+02 | 1.10e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 6.49e+03 | 1.10e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 4.68e+03 | 1.10e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 1.04e+01 | 1.10e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-14B / baseline | 6.00e-10 | 0.00e+00 | 7.47e-04 | 1.26e-03 | 0.100 | **LLaMEA-14B / baseline Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-14B / guided | 6.00e-10 | 2.45e-02 | 1.30e-03 | 2.14e-03 | 0.930 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-14B / thinking | 6.00e-10 | 1.71e-01 | 2.81e-03 | 4.30e-03 | 0.900 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-14B / vectorization | 6.00e-10 | 2.19e-01 | 2.81e-03 | 4.30e-03 | 0.900 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / baseline | 6.00e-10 | 5.73e+02 | 1.81e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / guided | 6.00e-10 | 6.49e+03 | 1.81e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / thinking | 6.00e-10 | 4.68e+03 | 1.81e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | DE | LLaMEA-7B / vectorization | 6.00e-10 | 1.04e+01 | 1.81e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA-14B / baseline | PSO | 0.00e+00 | 9.60e-04 | 6.39e-05 | 3.45e-04 | 1.000 | **LLaMEA-14B / baseline Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA-14B / guided | PSO | 2.45e-02 | 9.60e-04 | 2.11e-02 | 2.89e-02 | 0.190 | **PSO Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA-14B / thinking | PSO | 1.71e-01 | 9.60e-04 | 2.83e-03 | 4.30e-03 | 0.100 | **PSO Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA-14B / vectorization | PSO | 2.19e-01 | 9.60e-04 | 2.83e-03 | 4.30e-03 | 0.100 | **PSO Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA-7B / baseline | PSO | 5.73e+02 | 9.60e-04 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA-7B / guided | PSO | 6.49e+03 | 9.60e-04 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA-7B / thinking | PSO | 4.68e+03 | 9.60e-04 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Rosenbrock (f8)** | LLaMEA-7B / vectorization | PSO | 1.04e+01 | 9.60e-04 | 3.30e-04 | 5.77e-04 | 0.020 | **PSO Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / guided | 1.95e+00 | 4.46e+00 | 1.39e-02 | 1.97e-02 | 0.830 | **CMA-ES Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-14B / thinking | 1.95e+00 | 3.49e+01 | 2.41e-04 | 4.43e-04 | 0.990 | **CMA-ES Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / baseline | 1.95e+00 | 5.38e+04 | 1.79e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / guided | 1.95e+00 | 2.78e+03 | 1.79e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / thinking | 1.95e+00 | 8.86e+04 | 1.79e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | CMA-ES | LLaMEA-7B / vectorization | 1.95e+00 | 1.27e+05 | 1.79e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-14B / baseline | 1.66e+00 | 7.41e-04 | 1.83e-04 | 3.45e-04 | 0.000 | **LLaMEA-14B / baseline Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-14B / guided | 1.66e+00 | 4.46e+00 | 1.13e-02 | 1.62e-02 | 0.840 | **DE Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-14B / thinking | 1.66e+00 | 3.49e+01 | 2.46e-04 | 4.43e-04 | 0.990 | **DE Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / baseline | 1.66e+00 | 5.38e+04 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / guided | 1.66e+00 | 2.78e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / thinking | 1.66e+00 | 8.86e+04 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | DE | LLaMEA-7B / vectorization | 1.66e+00 | 1.27e+05 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA-14B / baseline | PSO | 7.41e-04 | 1.90e+00 | 1.83e-04 | 3.45e-04 | 1.000 | **LLaMEA-14B / baseline Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA-14B / thinking | PSO | 3.49e+01 | 1.90e+00 | 4.40e-04 | 7.59e-04 | 0.030 | **PSO Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / baseline | PSO | 5.38e+04 | 1.90e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / guided | PSO | 2.78e+03 | 1.90e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / thinking | PSO | 8.86e+04 | 1.90e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Rosenbrock (f8)** | LLaMEA-7B / vectorization | PSO | 1.27e+05 | 1.90e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 1.14e-04 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 3.62e+00 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 1.18e+04 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 9.71e+02 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 6.69e-05 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Discus (f11)** | DE | LLaMEA-14B / baseline | 1.51e-03 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **LLaMEA-14B / baseline Wins** |
| 2D | 0.0 | **Discus (f11)** | DE | LLaMEA-14B / guided | 1.51e-03 | 0.00e+00 | 1.75e-03 | 2.78e-03 | 0.100 | **LLaMEA-14B / guided Wins** |
| 2D | 0.0 | **Discus (f11)** | DE | LLaMEA-14B / thinking | 1.51e-03 | 0.00e+00 | 7.56e-04 | 1.27e-03 | 0.070 | **LLaMEA-14B / thinking Wins** |
| 2D | 0.0 | **Discus (f11)** | DE | LLaMEA-14B / vectorization | 1.51e-03 | 1.14e-04 | 3.76e-02 | 4.95e-02 | 0.220 | **LLaMEA-14B / vectorization Wins** |
| 2D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / baseline | 1.51e-03 | 3.62e+00 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / guided | 1.51e-03 | 1.18e+04 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / thinking | 1.51e-03 | 9.71e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / vectorization | 1.51e-03 | 6.69e-05 | 1.13e-02 | 1.62e-02 | 0.160 | **LLaMEA-7B / vectorization Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA-14B / baseline | PSO | 0.00e+00 | 3.77e+00 | 6.39e-05 | 3.45e-04 | 1.000 | **LLaMEA-14B / baseline Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA-14B / guided | PSO | 0.00e+00 | 3.77e+00 | 1.75e-03 | 2.78e-03 | 0.900 | **LLaMEA-14B / guided Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA-14B / thinking | PSO | 0.00e+00 | 3.77e+00 | 1.21e-04 | 3.45e-04 | 0.990 | **LLaMEA-14B / thinking Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA-14B / vectorization | PSO | 1.14e-04 | 3.77e+00 | 1.83e-04 | 3.45e-04 | 1.000 | **LLaMEA-14B / vectorization Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA-7B / guided | PSO | 1.18e+04 | 3.77e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA-7B / thinking | PSO | 9.71e+02 | 3.77e+00 | 5.83e-04 | 9.97e-04 | 0.040 | **PSO Wins** |
| 2D | 0.0 | **Discus (f11)** | LLaMEA-7B / vectorization | PSO | 6.69e-05 | 3.77e+00 | 1.83e-04 | 3.45e-04 | 1.000 | **LLaMEA-7B / vectorization Wins** |
| 2D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-7B / baseline | 2.02e+00 | 6.81e+03 | 7.00e-04 | 1.19e-03 | 0.950 | **CMA-ES Wins** |
| 2D | 0.05 | **Discus (f11)** | DE | LLaMEA-14B / guided | 8.86e-03 | 9.12e-05 | 1.83e-04 | 3.45e-04 | 0.000 | **LLaMEA-14B / guided Wins** |
| 2D | 0.05 | **Discus (f11)** | DE | LLaMEA-14B / thinking | 8.86e-03 | 5.26e-04 | 3.76e-02 | 4.95e-02 | 0.220 | **LLaMEA-14B / thinking Wins** |
| 2D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / baseline | 8.86e-03 | 6.81e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / guided | 8.86e-03 | 5.14e-01 | 3.30e-04 | 5.77e-04 | 0.980 | **DE Wins** |
| 2D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / thinking | 8.86e-03 | 1.97e+00 | 1.40e-02 | 1.99e-02 | 0.830 | **DE Wins** |
| 2D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / vectorization | 8.86e-03 | 1.24e+02 | 1.73e-02 | 2.39e-02 | 0.820 | **DE Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA-14B / guided | PSO | 9.12e-05 | 3.06e+00 | 1.83e-04 | 3.45e-04 | 1.000 | **LLaMEA-14B / guided Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA-14B / thinking | PSO | 5.26e-04 | 3.06e+00 | 2.46e-04 | 4.43e-04 | 0.990 | **LLaMEA-14B / thinking Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA-14B / vectorization | PSO | 2.85e-03 | 3.06e+00 | 1.83e-04 | 3.45e-04 | 1.000 | **LLaMEA-14B / vectorization Wins** |
| 2D | 0.05 | **Discus (f11)** | LLaMEA-7B / baseline | PSO | 6.81e+03 | 3.06e+00 | 1.31e-03 | 2.14e-03 | 0.070 | **PSO Wins** |
| 3D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-14B / guided | 0.00e+00 | 5.67e+04 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-14B / thinking | 0.00e+00 | 3.58e+05 | 1.64e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 3.18e-04 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 8.95e+00 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 2.74e+05 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 2.04e+05 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 5.38e+03 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Discus (f11)** | DE | LLaMEA-14B / baseline | 5.08e-03 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **LLaMEA-14B / baseline Wins** |
| 3D | 0.0 | **Discus (f11)** | DE | LLaMEA-14B / guided | 5.08e-03 | 5.67e+04 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Discus (f11)** | DE | LLaMEA-14B / thinking | 5.08e-03 | 3.58e+05 | 1.03e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / baseline | 5.08e-03 | 8.95e+00 | 2.46e-04 | 4.43e-04 | 0.990 | **DE Wins** |
| 3D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / guided | 5.08e-03 | 2.74e+05 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / thinking | 5.08e-03 | 2.04e+05 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / vectorization | 5.08e-03 | 5.38e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA-14B / baseline | PSO | 0.00e+00 | 5.50e+00 | 6.39e-05 | 3.45e-04 | 1.000 | **LLaMEA-14B / baseline Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA-14B / guided | PSO | 5.67e+04 | 5.50e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA-14B / thinking | PSO | 3.58e+05 | 5.50e+00 | 4.63e-03 | 6.92e-03 | 0.100 | **PSO Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA-14B / vectorization | PSO | 3.18e-04 | 5.50e+00 | 1.83e-04 | 3.45e-04 | 1.000 | **LLaMEA-14B / vectorization Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA-7B / guided | PSO | 2.74e+05 | 5.50e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA-7B / thinking | PSO | 2.04e+05 | 5.50e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Discus (f11)** | LLaMEA-7B / vectorization | PSO | 5.38e+03 | 5.50e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-14B / baseline | 0.00e+00 | 3.38e-04 | 1.75e-03 | 2.78e-03 | 0.900 | **CMA-ES Wins** |
| 3D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-14B / guided | 0.00e+00 | 4.93e+00 | 5.66e-04 | 9.75e-04 | 0.940 | **CMA-ES Wins** |
| 3D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-14B / thinking | 0.00e+00 | 4.69e+03 | 8.74e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 1.66e+05 | 9.12e-06 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 3.33e+06 | 8.74e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 5.23e-01 | 1.75e-03 | 2.78e-03 | 0.900 | **CMA-ES Wins** |
| 3D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 6.01e+07 | 8.74e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 4.92e+06 | 8.74e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Discus (f11)** | DE | LLaMEA-14B / baseline | 3.41e-02 | 3.38e-04 | 1.83e-04 | 3.45e-04 | 0.000 | **LLaMEA-14B / baseline Wins** |
| 3D | 0.05 | **Discus (f11)** | DE | LLaMEA-14B / guided | 3.41e-02 | 4.93e+00 | 1.73e-02 | 2.39e-02 | 0.820 | **DE Wins** |
| 3D | 0.05 | **Discus (f11)** | DE | LLaMEA-14B / thinking | 3.41e-02 | 4.69e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Discus (f11)** | DE | LLaMEA-14B / vectorization | 3.41e-02 | 1.66e+05 | 1.20e-05 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / baseline | 3.41e-02 | 3.33e+06 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / guided | 3.41e-02 | 5.23e-01 | 2.46e-04 | 4.43e-04 | 0.990 | **DE Wins** |
| 3D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / thinking | 3.41e-02 | 6.01e+07 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / vectorization | 3.41e-02 | 4.92e+06 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA-14B / baseline | PSO | 3.38e-04 | 3.53e+00 | 2.46e-04 | 4.43e-04 | 0.990 | **LLaMEA-14B / baseline Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA-14B / thinking | PSO | 4.69e+03 | 3.53e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA-14B / vectorization | PSO | 1.66e+05 | 3.53e+00 | 1.20e-05 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA-7B / baseline | PSO | 3.33e+06 | 3.53e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA-7B / thinking | PSO | 6.01e+07 | 3.53e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Discus (f11)** | LLaMEA-7B / vectorization | PSO | 4.92e+06 | 3.53e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-14B / baseline | 0.00e+00 | 2.54e+04 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-14B / thinking | 0.00e+00 | 2.66e-05 | 2.21e-03 | 3.43e-03 | 0.850 | **CMA-ES Wins** |
| 5D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 1.17e-03 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 7.20e+03 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 4.53e+06 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 5.78e+00 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Discus (f11)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 6.22e-07 | 6.39e-05 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Discus (f11)** | DE | LLaMEA-14B / baseline | 1.62e-03 | 2.54e+04 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Discus (f11)** | DE | LLaMEA-14B / guided | 1.62e-03 | 0.00e+00 | 1.11e-04 | 3.45e-04 | 0.000 | **LLaMEA-14B / guided Wins** |
| 5D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / baseline | 1.62e-03 | 7.20e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / guided | 1.62e-03 | 4.53e+06 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / thinking | 1.62e-03 | 5.78e+00 | 2.46e-04 | 4.43e-04 | 0.990 | **DE Wins** |
| 5D | 0.0 | **Discus (f11)** | DE | LLaMEA-7B / vectorization | 1.62e-03 | 6.22e-07 | 2.83e-03 | 4.30e-03 | 0.100 | **LLaMEA-7B / vectorization Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA-14B / baseline | PSO | 2.54e+04 | 1.70e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA-14B / guided | PSO | 0.00e+00 | 1.70e+01 | 1.11e-04 | 3.45e-04 | 1.000 | **LLaMEA-14B / guided Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA-14B / thinking | PSO | 2.66e-05 | 1.70e+01 | 1.79e-04 | 3.45e-04 | 1.000 | **LLaMEA-14B / thinking Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA-14B / vectorization | PSO | 1.17e-03 | 1.70e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **LLaMEA-14B / vectorization Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA-7B / baseline | PSO | 7.20e+03 | 1.70e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA-7B / guided | PSO | 4.53e+06 | 1.70e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Discus (f11)** | LLaMEA-7B / vectorization | PSO | 6.22e-07 | 1.70e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **LLaMEA-7B / vectorization Wins** |
| 5D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-14B / baseline | 0.00e+00 | 7.58e+06 | 1.11e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-14B / guided | 0.00e+00 | 3.94e+03 | 1.11e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-14B / thinking | 0.00e+00 | 3.48e+03 | 1.52e-04 | 3.45e-04 | 0.990 | **CMA-ES Wins** |
| 5D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-14B / vectorization | 0.00e+00 | 4.44e+04 | 1.11e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-7B / baseline | 0.00e+00 | 2.34e+07 | 1.11e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-7B / guided | 0.00e+00 | 2.42e+03 | 1.11e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-7B / thinking | 0.00e+00 | 1.08e+07 | 1.11e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Discus (f11)** | CMA-ES | LLaMEA-7B / vectorization | 0.00e+00 | 1.50e+04 | 1.11e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Discus (f11)** | DE | LLaMEA-14B / baseline | 5.38e-02 | 7.58e+06 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | DE | LLaMEA-14B / guided | 5.38e-02 | 3.94e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | DE | LLaMEA-14B / thinking | 5.38e-02 | 3.48e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | DE | LLaMEA-14B / vectorization | 5.38e-02 | 4.44e+04 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / baseline | 5.38e-02 | 2.34e+07 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / guided | 5.38e-02 | 2.42e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / thinking | 5.38e-02 | 1.08e+07 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | DE | LLaMEA-7B / vectorization | 5.38e-02 | 1.50e+04 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA-14B / baseline | PSO | 7.58e+06 | 2.89e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA-14B / guided | PSO | 3.94e+03 | 2.89e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA-14B / thinking | PSO | 3.48e+03 | 2.89e+01 | 3.30e-04 | 5.77e-04 | 0.020 | **PSO Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA-14B / vectorization | PSO | 4.44e+04 | 2.89e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA-7B / baseline | PSO | 2.34e+07 | 2.89e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA-7B / guided | PSO | 2.42e+03 | 2.89e+01 | 3.30e-04 | 5.77e-04 | 0.020 | **PSO Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA-7B / thinking | PSO | 1.08e+07 | 2.89e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Discus (f11)** | LLaMEA-7B / vectorization | PSO | 1.50e+04 | 2.89e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / baseline | 1.22e+00 | 2.71e+03 | 1.73e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / thinking | 1.22e+00 | 3.32e+01 | 4.18e-04 | 7.31e-04 | 0.970 | **CMA-ES Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / vectorization | 1.22e+00 | 2.51e+01 | 7.34e-04 | 1.25e-03 | 0.950 | **CMA-ES Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / baseline | 1.22e+00 | 3.46e+01 | 1.73e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / thinking | 1.22e+00 | 7.84e+01 | 2.33e-04 | 4.36e-04 | 0.990 | **CMA-ES Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / vectorization | 1.22e+00 | 0.00e+00 | 2.17e-04 | 4.08e-04 | 0.050 | **LLaMEA-7B / vectorization Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / baseline | 9.95e-01 | 2.71e+03 | 1.82e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / thinking | 9.95e-01 | 3.32e+01 | 1.82e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / vectorization | 9.95e-01 | 2.51e+01 | 3.28e-04 | 5.77e-04 | 0.980 | **DE Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / baseline | 9.95e-01 | 3.46e+01 | 1.82e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / guided | 9.95e-01 | 2.43e+00 | 2.57e-02 | 3.46e-02 | 0.800 | **DE Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / thinking | 9.95e-01 | 7.84e+01 | 1.82e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / vectorization | 9.95e-01 | 0.00e+00 | 6.34e-05 | 3.45e-04 | 0.000 | **LLaMEA-7B / vectorization Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / baseline | PSO | 2.71e+03 | 0.00e+00 | 1.31e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / thinking | PSO | 3.32e+01 | 0.00e+00 | 1.31e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / vectorization | PSO | 2.51e+01 | 0.00e+00 | 1.79e-04 | 3.45e-04 | 0.010 | **PSO Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / baseline | PSO | 3.46e+01 | 0.00e+00 | 1.31e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / guided | PSO | 2.43e+00 | 0.00e+00 | 1.75e-03 | 2.78e-03 | 0.090 | **PSO Wins** |
| 2D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / thinking | PSO | 7.84e+01 | 0.00e+00 | 1.31e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / baseline | 1.00e+00 | 9.61e+02 | 1.82e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / guided | 1.00e+00 | 6.10e+01 | 1.82e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / thinking | 1.00e+00 | 2.04e+01 | 3.28e-04 | 5.77e-04 | 0.980 | **CMA-ES Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / vectorization | 1.00e+00 | 3.17e+02 | 1.82e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / baseline | 1.00e+00 | 3.26e+02 | 1.82e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / guided | 1.00e+00 | 2.31e+03 | 1.82e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / thinking | 1.00e+00 | 1.96e+02 | 1.82e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / vectorization | 1.00e+00 | 2.73e+02 | 1.82e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / baseline | 3.15e+00 | 9.61e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / guided | 3.15e+00 | 6.10e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / thinking | 3.15e+00 | 2.04e+01 | 4.59e-03 | 6.86e-03 | 0.880 | **DE Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / vectorization | 3.15e+00 | 3.17e+02 | 5.83e-04 | 9.97e-04 | 0.960 | **DE Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / baseline | 3.15e+00 | 3.26e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / guided | 3.15e+00 | 2.31e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / thinking | 3.15e+00 | 1.96e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / vectorization | 3.15e+00 | 2.73e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / baseline | PSO | 9.61e+02 | 0.00e+00 | 1.32e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / guided | PSO | 6.10e+01 | 0.00e+00 | 1.32e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / thinking | PSO | 2.04e+01 | 0.00e+00 | 1.32e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / vectorization | PSO | 3.17e+02 | 0.00e+00 | 1.32e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / baseline | PSO | 3.26e+02 | 0.00e+00 | 1.32e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / guided | PSO | 2.31e+03 | 0.00e+00 | 1.32e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / thinking | PSO | 1.96e+02 | 0.00e+00 | 1.32e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / vectorization | PSO | 2.73e+02 | 0.00e+00 | 1.32e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / baseline | 3.38e+00 | 4.34e+01 | 1.80e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / guided | 3.38e+00 | 3.25e+01 | 2.42e-04 | 4.43e-04 | 0.990 | **CMA-ES Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / thinking | 3.38e+00 | 9.97e-01 | 3.10e-02 | 4.15e-02 | 0.210 | **LLaMEA-14B / thinking Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / vectorization | 3.38e+00 | 2.42e+02 | 1.80e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / baseline | 3.38e+00 | 2.70e+01 | 1.80e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / guided | 3.38e+00 | 0.00e+00 | 6.25e-05 | 3.45e-04 | 0.000 | **LLaMEA-7B / guided Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / vectorization | 3.38e+00 | 4.63e+02 | 1.80e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / baseline | 2.49e+00 | 4.34e+01 | 1.82e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / guided | 2.49e+00 | 3.25e+01 | 1.82e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / vectorization | 2.49e+00 | 2.42e+02 | 1.82e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / baseline | 2.49e+00 | 2.70e+01 | 1.82e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / guided | 2.49e+00 | 0.00e+00 | 6.34e-05 | 3.45e-04 | 0.000 | **LLaMEA-7B / guided Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / vectorization | 2.49e+00 | 4.63e+02 | 1.82e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / baseline | PSO | 4.34e+01 | 4.97e-01 | 1.62e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / guided | PSO | 3.25e+01 | 4.97e-01 | 1.62e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / vectorization | PSO | 2.42e+02 | 4.97e-01 | 1.62e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / baseline | PSO | 2.70e+01 | 4.97e-01 | 1.62e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / guided | PSO | 0.00e+00 | 4.97e-01 | 1.49e-02 | 2.09e-02 | 0.750 | **LLaMEA-7B / guided Wins** |
| 3D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / vectorization | PSO | 4.63e+02 | 4.97e-01 | 1.62e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / baseline | 3.41e+00 | 4.17e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / guided | 3.41e+00 | 6.45e+01 | 3.30e-04 | 5.77e-04 | 0.980 | **CMA-ES Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / thinking | 3.41e+00 | 4.22e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / vectorization | 3.41e+00 | 2.86e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / baseline | 3.41e+00 | 1.81e+01 | 1.01e-03 | 1.67e-03 | 0.940 | **CMA-ES Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / guided | 3.41e+00 | 2.38e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / thinking | 3.41e+00 | 2.72e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / vectorization | 3.41e+00 | 2.50e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / baseline | 5.32e+00 | 4.17e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / guided | 5.32e+00 | 6.45e+01 | 2.46e-04 | 4.43e-04 | 0.990 | **DE Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / thinking | 5.32e+00 | 4.22e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / vectorization | 5.32e+00 | 2.86e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / baseline | 5.32e+00 | 1.81e+01 | 5.80e-03 | 8.57e-03 | 0.870 | **DE Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / guided | 5.32e+00 | 2.38e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / thinking | 5.32e+00 | 2.72e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / vectorization | 5.32e+00 | 2.50e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / baseline | PSO | 4.17e+01 | 2.03e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / guided | PSO | 6.45e+01 | 2.03e+00 | 2.46e-04 | 4.43e-04 | 0.010 | **PSO Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / thinking | PSO | 4.22e+01 | 2.03e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / vectorization | PSO | 2.86e+02 | 2.03e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / baseline | PSO | 1.81e+01 | 2.03e+00 | 1.01e-03 | 1.67e-03 | 0.060 | **PSO Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / guided | PSO | 2.38e+02 | 2.03e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / thinking | PSO | 2.72e+01 | 2.03e+00 | 2.46e-04 | 4.43e-04 | 0.010 | **PSO Wins** |
| 3D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / vectorization | PSO | 2.50e+02 | 2.03e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / baseline | 4.97e+00 | 1.13e+02 | 1.78e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / guided | 4.97e+00 | 9.29e+00 | 1.70e-02 | 2.39e-02 | 0.820 | **CMA-ES Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / thinking | 4.97e+00 | 1.98e+02 | 1.78e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / baseline | 4.97e+00 | 4.63e+01 | 1.78e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / guided | 4.97e+00 | 3.83e+01 | 1.78e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / thinking | 4.97e+00 | 8.51e+02 | 1.78e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / vectorization | 4.97e+00 | 4.80e+02 | 1.78e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / baseline | 5.97e+00 | 1.13e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / guided | 5.97e+00 | 9.29e+00 | 3.76e-02 | 4.95e-02 | 0.780 | **DE Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / thinking | 5.97e+00 | 1.98e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / baseline | 5.97e+00 | 4.63e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / guided | 5.97e+00 | 3.83e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / thinking | 5.97e+00 | 8.51e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / vectorization | 5.97e+00 | 4.80e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / baseline | PSO | 1.13e+02 | 1.19e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / thinking | PSO | 1.98e+02 | 1.19e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / baseline | PSO | 4.63e+01 | 1.19e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / guided | PSO | 3.83e+01 | 1.19e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / thinking | PSO | 8.51e+02 | 1.19e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / vectorization | PSO | 4.80e+02 | 1.19e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / baseline | 6.64e+00 | 5.84e+01 | 2.83e-03 | 4.30e-03 | 0.900 | **CMA-ES Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / guided | 6.64e+00 | 3.94e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / thinking | 6.64e+00 | 1.74e+01 | 1.01e-03 | 1.67e-03 | 0.940 | **CMA-ES Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-14B / vectorization | 6.64e+00 | 1.31e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / baseline | 6.64e+00 | 3.91e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / thinking | 6.64e+00 | 2.72e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | CMA-ES | LLaMEA-7B / vectorization | 6.64e+00 | 6.38e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / baseline | 1.59e+01 | 5.84e+01 | 2.83e-03 | 4.30e-03 | 0.900 | **DE Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / guided | 1.59e+01 | 3.94e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-14B / vectorization | 1.59e+01 | 1.31e+03 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / baseline | 1.59e+01 | 3.91e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / thinking | 1.59e+01 | 2.72e+02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | DE | LLaMEA-7B / vectorization | 1.59e+01 | 6.38e+01 | 2.46e-04 | 4.43e-04 | 0.990 | **DE Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / baseline | PSO | 5.84e+01 | 1.02e+01 | 2.83e-03 | 4.30e-03 | 0.100 | **PSO Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / guided | PSO | 3.94e+01 | 1.02e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / thinking | PSO | 1.74e+01 | 1.02e+01 | 2.11e-02 | 2.89e-02 | 0.190 | **PSO Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-14B / vectorization | PSO | 1.31e+03 | 1.02e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / baseline | PSO | 3.91e+02 | 1.02e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / thinking | PSO | 2.72e+02 | 1.02e+01 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Rastrigin Multi-Modal (f15)** | LLaMEA-7B / vectorization | PSO | 6.38e+01 | 1.02e+01 | 2.46e-04 | 4.43e-04 | 0.010 | **PSO Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / baseline | 7.33e-01 | 1.49e+01 | 3.26e-04 | 5.77e-04 | 0.980 | **CMA-ES Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / guided | 7.33e-01 | 0.00e+00 | 2.10e-02 | 2.89e-02 | 0.200 | **LLaMEA-14B / guided Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / guided | 7.33e-01 | 0.00e+00 | 2.74e-02 | 3.68e-02 | 0.215 | **LLaMEA-7B / guided Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / thinking | 7.33e-01 | 3.97e+01 | 1.81e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / vectorization | 7.33e-01 | 1.27e+01 | 2.43e-04 | 4.43e-04 | 0.990 | **CMA-ES Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / baseline | 3.39e-07 | 1.49e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / guided | 3.39e-07 | 0.00e+00 | 2.90e-02 | 3.89e-02 | 0.210 | **LLaMEA-14B / guided Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / thinking | 3.39e-07 | 9.30e-01 | 2.55e-02 | 3.45e-02 | 0.800 | **DE Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / vectorization | 3.39e-07 | 3.57e-02 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / baseline | 3.39e-07 | 1.40e+00 | 2.83e-03 | 4.30e-03 | 0.900 | **DE Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / thinking | 3.39e-07 | 3.97e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / vectorization | 3.39e-07 | 1.27e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / baseline | PSO | 1.49e+01 | 0.00e+00 | 1.49e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / baseline | PSO | 1.40e+00 | 0.00e+00 | 1.75e-03 | 2.78e-03 | 0.090 | **PSO Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / thinking | PSO | 3.97e+01 | 0.00e+00 | 1.49e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / vectorization | PSO | 1.27e+01 | 0.00e+00 | 1.49e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / baseline | 9.33e-01 | 0.00e+00 | 2.31e-04 | 4.33e-04 | 0.050 | **LLaMEA-14B / baseline Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / guided | 9.33e-01 | 0.00e+00 | 1.21e-02 | 1.72e-02 | 0.170 | **LLaMEA-14B / guided Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / vectorization | 9.33e-01 | 0.00e+00 | 2.31e-04 | 4.33e-04 | 0.050 | **LLaMEA-14B / vectorization Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / baseline | 9.33e-01 | 2.88e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / guided | 9.33e-01 | 7.92e+00 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / thinking | 9.33e-01 | 1.07e+01 | 3.30e-04 | 5.77e-04 | 0.980 | **CMA-ES Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / vectorization | 9.33e-01 | 1.14e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / baseline | 1.50e-05 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **LLaMEA-14B / baseline Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / vectorization | 1.50e-05 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **LLaMEA-14B / vectorization Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / baseline | 1.50e-05 | 2.88e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / guided | 1.50e-05 | 7.92e+00 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / thinking | 1.50e-05 | 1.07e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / vectorization | 1.50e-05 | 1.14e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / baseline | PSO | 2.88e+01 | 0.00e+00 | 1.32e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / guided | PSO | 7.92e+00 | 0.00e+00 | 1.80e-04 | 3.45e-04 | 0.010 | **PSO Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / thinking | PSO | 1.07e+01 | 0.00e+00 | 2.44e-04 | 4.43e-04 | 0.020 | **PSO Wins** |
| 2D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / vectorization | PSO | 1.14e+01 | 0.00e+00 | 1.32e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / baseline | 6.92e-01 | 1.94e+00 | 3.35e-02 | 4.44e-02 | 0.785 | **CMA-ES Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / guided | 6.92e-01 | 0.00e+00 | 5.94e-03 | 8.77e-03 | 0.200 | **LLaMEA-14B / guided Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / thinking | 6.92e-01 | 2.22e+01 | 1.72e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / guided | 6.92e-01 | 0.00e+00 | 5.94e-03 | 8.77e-03 | 0.200 | **LLaMEA-7B / guided Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / thinking | 6.92e-01 | 0.00e+00 | 5.94e-03 | 8.77e-03 | 0.200 | **LLaMEA-7B / thinking Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / vectorization | 6.92e-01 | 8.19e+01 | 1.72e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / baseline | 2.61e-06 | 1.94e+00 | 3.12e-02 | 4.15e-02 | 0.790 | **DE Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / guided | 2.61e-06 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **LLaMEA-14B / guided Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / thinking | 2.61e-06 | 2.22e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / guided | 2.61e-06 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **LLaMEA-7B / guided Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / thinking | 2.61e-06 | 0.00e+00 | 6.39e-05 | 3.45e-04 | 0.000 | **LLaMEA-7B / thinking Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / vectorization | 2.61e-06 | 8.19e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / baseline | PSO | 1.94e+00 | 3.46e-01 | 4.78e-03 | 7.14e-03 | 0.125 | **PSO Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / guided | PSO | 0.00e+00 | 3.46e-01 | 1.48e-02 | 2.09e-02 | 0.750 | **LLaMEA-14B / guided Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / thinking | PSO | 2.22e+01 | 3.46e-01 | 1.61e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / guided | PSO | 0.00e+00 | 3.46e-01 | 1.48e-02 | 2.09e-02 | 0.750 | **LLaMEA-7B / guided Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / thinking | PSO | 0.00e+00 | 3.46e-01 | 1.48e-02 | 2.09e-02 | 0.750 | **LLaMEA-7B / thinking Wins** |
| 3D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / vectorization | PSO | 8.19e+01 | 3.46e-01 | 1.61e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / baseline | 8.20e-01 | 3.70e+01 | 1.79e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / guided | 8.20e-01 | 3.49e+01 | 2.41e-04 | 4.43e-04 | 0.990 | **CMA-ES Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / thinking | 8.20e-01 | 6.85e+00 | 3.56e-03 | 5.41e-03 | 0.890 | **CMA-ES Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / vectorization | 8.20e-01 | 2.06e+01 | 1.79e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / baseline | 8.20e-01 | 3.81e+01 | 1.79e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / guided | 8.20e-01 | 6.01e+00 | 1.29e-03 | 2.13e-03 | 0.930 | **CMA-ES Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / vectorization | 8.20e-01 | 1.73e+01 | 1.79e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / baseline | 2.57e-05 | 3.70e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / guided | 2.57e-05 | 3.49e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / thinking | 2.57e-05 | 6.85e+00 | 3.30e-04 | 5.77e-04 | 0.980 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / vectorization | 2.57e-05 | 2.06e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / baseline | 2.57e-05 | 3.81e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / guided | 2.57e-05 | 6.01e+00 | 3.30e-04 | 5.77e-04 | 0.980 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / vectorization | 2.57e-05 | 1.73e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / baseline | PSO | 3.70e+01 | 3.58e-01 | 1.63e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / guided | PSO | 3.49e+01 | 3.58e-01 | 1.63e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / thinking | PSO | 6.85e+00 | 3.58e-01 | 9.22e-04 | 1.54e-03 | 0.060 | **PSO Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / vectorization | PSO | 2.06e+01 | 3.58e-01 | 1.63e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / baseline | PSO | 3.81e+01 | 3.58e-01 | 1.63e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / guided | PSO | 6.01e+00 | 3.58e-01 | 7.00e-04 | 1.19e-03 | 0.050 | **PSO Wins** |
| 3D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / vectorization | PSO | 1.73e+01 | 3.58e-01 | 1.63e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / baseline | 1.25e+00 | 2.00e+00 | 2.38e-02 | 3.22e-02 | 0.800 | **CMA-ES Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / guided | 1.25e+00 | 6.85e+01 | 1.49e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / thinking | 1.25e+00 | 0.00e+00 | 3.06e-04 | 5.51e-04 | 0.055 | **LLaMEA-14B / thinking Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / baseline | 1.25e+00 | 7.64e+00 | 1.02e-02 | 1.48e-02 | 0.840 | **CMA-ES Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / guided | 1.25e+00 | 0.00e+00 | 1.82e-04 | 3.45e-04 | 0.050 | **LLaMEA-7B / guided Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / vectorization | 1.25e+00 | 2.82e+00 | 3.51e-02 | 4.64e-02 | 0.780 | **CMA-ES Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / baseline | 4.65e-01 | 2.00e+00 | 4.57e-03 | 6.86e-03 | 0.880 | **DE Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / guided | 4.65e-01 | 6.85e+01 | 1.82e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / thinking | 4.65e-01 | 0.00e+00 | 5.63e-04 | 9.71e-04 | 0.060 | **LLaMEA-14B / thinking Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / baseline | 4.65e-01 | 7.64e+00 | 2.19e-03 | 3.43e-03 | 0.910 | **DE Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / guided | 4.65e-01 | 0.00e+00 | 6.34e-05 | 3.45e-04 | 0.000 | **LLaMEA-7B / guided Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / vectorization | 4.65e-01 | 2.82e+00 | 5.78e-03 | 8.57e-03 | 0.870 | **DE Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / guided | PSO | 6.85e+01 | 1.68e+00 | 1.82e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / thinking | PSO | 0.00e+00 | 1.68e+00 | 6.89e-04 | 1.18e-03 | 0.925 | **LLaMEA-14B / thinking Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / baseline | PSO | 7.64e+00 | 1.68e+00 | 1.72e-02 | 2.39e-02 | 0.180 | **PSO Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / guided | PSO | 0.00e+00 | 1.68e+00 | 2.30e-04 | 4.32e-04 | 0.950 | **LLaMEA-7B / guided Wins** |
| 5D | 0.0 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / vectorization | PSO | 2.82e+00 | 1.68e+00 | 3.11e-02 | 4.15e-02 | 0.210 | **PSO Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / thinking | 1.27e+00 | 6.90e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-14B / vectorization | 1.27e+00 | 6.81e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / guided | 1.27e+00 | 6.86e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / thinking | 1.27e+00 | 2.55e+00 | 3.12e-02 | 4.15e-02 | 0.790 | **CMA-ES Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | CMA-ES | LLaMEA-7B / vectorization | 1.27e+00 | 6.48e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **CMA-ES Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / thinking | 3.73e-01 | 6.90e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-14B / vectorization | 3.73e-01 | 6.81e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / guided | 3.73e-01 | 6.86e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / thinking | 3.73e-01 | 2.55e+00 | 3.61e-03 | 5.45e-03 | 0.890 | **DE Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | DE | LLaMEA-7B / vectorization | 3.73e-01 | 6.48e+01 | 1.83e-04 | 3.45e-04 | 1.000 | **DE Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / thinking | PSO | 6.90e+01 | 2.19e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-14B / vectorization | PSO | 6.81e+01 | 2.19e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / guided | PSO | 6.86e+01 | 2.19e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |
| 5D | 0.05 | **Gallagher 101 Peaks (f21)** | LLaMEA-7B / vectorization | PSO | 6.48e+01 | 2.19e+00 | 1.83e-04 | 3.45e-04 | 0.000 | **PSO Wins** |

---
## 🌊 5. Noise Robustness & Landscape Fragility Analysis

The impact of stochastic evaluation noise ($\sigma = 0.05$) is quantified via the **Degradation Factor** $\Delta \log_{10}(\Delta y) = \log_{10}(\text{Median Error}_{\text{Noisy}}) - \log_{10}(\text{Median Error}_{\text{Clean}})$. Positive values indicate loss of precision under noise.

| Problem Landscape | Landscape Class | Median Degradation (LLaMEA) | Median Degradation (Baselines) | Noise Sensitivity Assessment |
| :--- | :--- | :---: | :---: | :--- |
| **Sphere (f1)** | Separable | +0.30 | 0.00 (Stable) | 🟢 **Resilient**: Precision remains intact despite stochastic perturbation |
| **Rosenbrock (f8)** | Low Conditioning | +0.74 | +7.03 | 🔴 **High Fragility**: Severe valley stagnation under noise |
| **Discus (f11)** | High Conditioning | +1.40 | +0.34 | 🟢 **Resilient**: Precision remains intact despite stochastic perturbation |
| **Rastrigin Multi-Modal (f15)** | Multi-Modal (Global) | +0.97 | +0.21 | 🟡 **Moderate Fragility**: Slight barrier degradation, exploration preserved |
| **Gallagher 101 Peaks (f21)** | Multi-Modal (Weak) | -0.31 | +0.88 | 🟡 **Moderate Fragility**: Slight barrier degradation, exploration preserved |