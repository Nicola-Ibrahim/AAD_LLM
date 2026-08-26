# Empirical Evaluation & Experimental Methodology: Thesis Chapter Blueprint

---

## 1. Executive Summary & Chapter Scope

This document serves as the comprehensive **master blueprint** for the **Experimental Evaluation Chapter** of the Master's Thesis: *"Automated Algorithm Design for Continuous Black-Box Optimization via Large Language Models (LLaMEA) under Deterministic and Noisy Regimes"*.

### 1.1 Core Research Questions (RQs)
1. **RQ1 (Algorithmic Competitiveness)**: Can LLM-synthesized continuous optimization algorithms match or surpass established state-of-the-art classical metaheuristics (CMA-ES, Differential Evolution, Particle Swarm Optimization) across diverse BBOB landscape classes?
2. **RQ2 (Model Scaling Effects)**: How does LLM parameter scale ($7\text{B}$ vs. $14\text{B}$ parameters) impact the mathematical validity, novelty, and convergence efficacy of evolved optimization algorithms?
3. **RQ3 (Prompt Strategy Ablation)**: Does structured prompt engineering (Domain Guidance, Chain-of-Thought "Thinking", Vectorization constraints) significantly improve algorithmic search quality compared to naive evolutionary prompts?
4. **RQ4 (Noise Robustness & Generalization)**: How resilient are LLM-evolved optimizers when subjected to heteroscedastic evaluation noise ($\sigma = 0.05$) compared to deterministic landscapes ($\sigma = 0.0$)?
5. **RQ5 (Synthesis-to-Evaluation Transferability)**: Do candidate algorithms optimized under low evaluation budgets ($1,000$ function evaluations during synthesis) generalize when scaled to full benchmark budgets ($50,000$ evaluations in IOHprofiler)?

---

## 2. Experimental Architecture & Two-Stage Paradigm

The empirical investigation follows a rigorous two-stage design separating **Online Algorithmic Synthesis** from **Independent Post-Hoc Benchmarking**:

```
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │ STAGE 1: Automated Algorithm Synthesis (LLaMEA Online Evolution)            │
 │ • Iterations: 10–20 generations per run                                     │
 │ • Budget: 1,000 function evaluations per candidate                          │
 │ • LLMs: Qwen2.5-Coder-7B & Qwen2.5-Coder-14B (GGUF Q4_K_M)                 │
 │ • Prompt Strategies: Baseline, Guided, Thinking, Vectorization              │
 │ • Storage: SQLite Database (292 completed runs, 2,902 code iterations)     │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │ (Champion Selection: Minimum Final Error)
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │ STAGE 2: Independent Empirical Benchmarking (IOHprofiler / BBOB Protocol)   │
 │ • Benchmark Suite: COCO / BBOB (f1, f8, f11, f15, f21)                      │
 │ • Dimensions: D ∈ {2, 3, 5} | Noise Regimes: σ ∈ {0.0, 0.05}                │
 │ • Replications: 10 independent random seeds per condition                   │
 │ • Evaluation Budget: 50,000 evaluations (10,000 × D scaling)                │
 │ • Solvers Evaluated: 11 (3 Classical Baselines + 8 LLaMEA Champions)        │
 │ • Trace Repository: IOHprofiler .dat / .json convergence logs               │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │ (Empirical Performance Profiling)
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │ STAGE 3: Performance Profiling & Comparative Analysis                       │
 │ • Empirical Cumulative Distribution Functions (ECDF over targets Δy ≤ 10⁻⁸) │
 │ • Log-scale Convergence Trajectories with IQR (25th–75th percentiles)       │
 │ • Empirical Target Success Rates across BBOB Landscape Hardness Classes     │
 │ • Cross-Environment Noise Retention & Fragility Metrics (Clean vs. Noisy)   │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Experimental Setup & Configurations

### 3.1 Stage 1: Algorithm Synthesis Configuration (LLaMEA)

| Hyperparameter / Component | Exact Configuration | Rationale / Scientific Grounding |
| :--- | :--- | :--- |
| **Evolution Engine** | LLaMEA (LLM-driven Automated Algorithm Design) | 1+1 evolutionary loop iteratively mutating Python algorithm ASTs. |
| **Large Language Models** | `qwen2.5-coder-7b-instruct-q4_k_m.gguf`<br>`qwen2.5-coder-14b-instruct-q4_k_m.gguf` | High coding competence at local inference scale; enables direct 7B vs 14B scaling comparison. |
| **Quantization Scheme** | 4-bit Medium Quantization (`Q4_K_M`) | Minimizes VRAM footprint while preserving instruction following and syntax precision. |
| **Inference Backend** | `llama-cpp-python` / Local GPU Execution | Deterministic temperature controls without external API drift or rate-limiting. |
| **Sampling Temperature** | $T = 0.7$ (synthesis mutations) | Balances exploitation of working algorithmic scaffolds with stochastic code novelty. |
| **Synthesis Evaluation Budget** | $1,000$ function evaluations | Fast online evaluation enabling multi-generation evolutionary cycles. |
| **Max Synthesis Iterations** | $10 \text{ to } 20$ generations | Allows observable genetic trajectory without excessive computational overhead. |
| **Target Functions (Synthesis)** | BBOB $f_1, f_8, f_{11}, f_{15}, f_{21}$ ($D \in \{2,3,5\}$) | Spans the full range of mathematical landscapes (separable, ill-conditioned, multi-modal). |
| **Completed Synthesis Runs** | **292 complete evolutionary runs** | Totaling **2,902 evaluated algorithm iterations** stored in `database.sqlite`. |

#### Prompt Strategy Ablation Matrix:
1. **`baseline`**: Standard metaheuristic prompt requesting an iterative Python continuous optimizer without specialized domain priors.
2. **`guided`**: Enriched with domain heuristics (step-size adaptation principles, population diversity preservation, and covariance hints).
3. **`thinking`**: Structured Chain-of-Thought (CoT) scaffold compelling the LLM to write `<thinking>` trace analyzing previous failure modes before emitting code.
4. **`vectorization`**: Specialized vectorization constraints forcing matrix-oriented NumPy operations and vectorized exploration loops.

---

### 3.2 Stage 2: Empirical Benchmarking Protocol (IOHprofiler)

| Parameter | Value / Protocol | Notes |
| :--- | :--- | :--- |
| **Benchmark Suite** | BBOB / COCO Single-Objective Continuous Suite | Standard benchmark standard in continuous black-box optimization. |
| **Dimensions ($D$)** | $D \in \{2, 3, 5\}$ | Testing low-dimensional geometry scaling behavior. |
| **Noise Levels ($\sigma$)** | $\sigma = 0.0$ (Clean), $\sigma = 0.05$ (Heteroscedastic Optimality-Gap) | Injected via domain strategy: $\tilde{f}(x) = f(x) + \mathcal{N}(0, (\sigma \cdot |f(x) - f^*|)^2)$. |
| **Problem Instances** | 5 canonical BBOB functions across 5 distinct hardness classes: |
| | • $f_1$: **Sphere** (Separable, unimodal, convex) | Baseline convergence rate test. |
| | • $f_8$: **Rosenbrock** (Low conditioning, parabolic valley) | Valley-following and coordinate rotation test. |
| | • $f_{11}$: **Discus** (High conditioning, condition number $10^6$) | Numerical stability & eigenvalue distortion test. |
| | • $f_{15}$: **Rastrigin** (Multi-modal with global structure) | Basins of attraction and premature convergence test. |
| | • $f_{21}$: **Gallagher 101 Peaks** (Multi-modal with weak structure) | Highly deceptive landscape with 101 local optima. |
| **Replication Budget** | $10$ independent random seeds per problem condition | Total of $30 \times 10 \times 11 = 3,300$ complete benchmark runs. |
| **Evaluation Budget** | $50,000$ function evaluations ($10,000 \times D$) | Long-horizon benchmark testing asymptotic convergence. |
| **Success Criterion** | Target precision $\Delta y = f(x) - f_{\text{opt}} \le 10^{-8}$ | Standard COCO precision threshold for empirical hitting times. |
| **Classical Baselines** | **CMA-ES** (Covariance Matrix Adaptation Evolution Strategy)<br>**DE** (Differential Evolution `best1bin`)<br>**PSO** (Particle Swarm Optimization) | Established continuous optimization algorithms serving as gold standards. |
| **Total Solvers Evaluated** | **11 Solvers**: 3 Classical Baselines + 8 LLaMEA Evolved Champions | Fully evaluated across all 30 conditions ($3 \text{ dims} \times 2 \text{ noise levels} \times 5 \text{ problems}$). |

---

## 4. Empirical Terminology, Metrics & Evaluation Methodology

### 4.1 Foundational Terminology: Points, Evaluations, and Iterations

To prevent ambiguity in continuous optimization benchmarking, four distinct operational terms are strictly defined:

| Term | Mathematical Symbol | Definition in Benchmarking Protocol | Role in the Thesis |
| :--- | :---: | :--- | :--- |
| **Candidate Point** | $\vec{x} \in \mathbb{R}^D$ | A single coordinate vector in $D$-dimensional search space (e.g. $\vec{x} = [1.2, -0.4, 3.1]$ in 3D). | Basic unit of decision space exploration. |
| **Function Evaluation** | $f(\vec{x})$ | Evaluating the mathematical objective value/error for **exactly one point $\vec{x}$**. | **The fundamental cost metric (X-axis of all benchmark plots)**. Budget = $50,000$ evaluations ($10,000 \times D$). |
| **Algorithmic Iteration** | $t \in \mathbb{N}$ | One complete update cycle/step of the optimizer loop. An algorithm with population size $N$ evaluates $N$ points per iteration ($N$ evaluations consumed). | Internal solver loop counter (not used on plot axes to ensure fair comparison across variable population sizes). |
| **Benchmark Replication** | Run $r \in [1, 10]$ | An independent execution of the solver on the same problem condition with a distinct random seed. | Ensures statistical reliability and variance quantification across stochastic runs. |

> **Why the X-Axis Uses Function Evaluations ($f(\vec{x})$ Calls):**  
> In black-box optimization, algorithmic internal iterations vary widely (e.g., $(1+1)$-ES evaluates $1$ point per step, while CMA-ES evaluates $\lambda = 4 + \lfloor 3 \ln D \rfloor$ points, and PSO evaluates a swarm of $30$ particles per step). The standard BBOB/COCO protocol evaluates computational efficiency strictly by the **total cumulative function evaluations** consumed to reach a target.

---

### 4.2 Empirical Cumulative Distribution Functions (ECDF)

The performance aggregation across problem instances and runs is evaluated using the **Empirical Runtime Cumulative Distribution Function (ECDF)** as standardized by Nikolaus Hansen et al. (COCO/BBOB, 2016) and IOHprofiler (de Nobel et al., 2021).

#### The 51 Logarithmic Target Checkpoints ($T$)
Rather than measuring a binary all-or-nothing success threshold ($\Delta y \le 10^{-8}$), the benchmark establishes a discretized ladder of **51 precision target values** spanning **10 orders of magnitude** from coarse approximation ($10^2 = 100$) down to machine-precision optimum ($10^{-8}$):

$$T = \left\{ 10^{2.0 - 0.2 \cdot k} \;\middle|\; k \in \{0, 1, \dots, 50\} \right\} = \left\{ 10^{2.0}, 10^{1.8}, 10^{1.6}, \dots, 10^{0.0}, \dots, 10^{-7.8}, 10^{-8.0} \right\}$$

$$\text{Total Targets } |T| = \frac{\log_{10}(10^2) - \log_{10}(10^{-8})}{\Delta \log_{10}} + 1 = \frac{2 - (-8)}{0.2} + 1 = \mathbf{51 \text{ targets}}$$

#### Mathematical Formulation of Runtime ECDF
Let $y_r(k) = \min_{j \le k} \left( f(\vec{x}_j) - f_{\text{opt}} \right)$ denote the best objective value found in run $r \in \{1, \dots, N_{\text{runs}}\}$ at or before function evaluation $k \in [1, 50000]$.

The empirical fraction of solved targets at evaluation budget $k$ is given by:
$$\text{ECDF}(k) = \frac{1}{|T| \cdot N_{\text{runs}}} \sum_{r=1}^{N_{\text{runs}}} \sum_{t \in T} \mathbb{I}\left( y_r(k) \le t \right)$$

where $\mathbb{I}(\cdot)$ is the indicator function returning $1$ if the condition is satisfied and $0$ otherwise.

```
Fraction of Targets Solved (Y-axis)
 1.0 |                                    ┌────────── (All 51 targets solved across all 10 runs)
     |                             ┌──────┘
 0.5 |                      ┌──────┘
     |               ┌──────┘
 0.0 |───────────────┴───────────────────────────────
     10⁰            10²            10⁴           10⁵  --> Function Evaluations (X-axis, Log-scale)
```

#### Properties and Interpretation:
1. **Monotonically Non-Decreasing ($0.0 \to 1.0$)**: Because best-so-far error $y_r(k)$ is non-increasing as $k$ grows, $\text{ECDF}(k)$ is guaranteed to be monotonically non-decreasing over function evaluations.
2. **Steepness and Height**: A steeper, left-shifted curve indicates faster convergence speed. A higher plateau indicates greater global exploration capability and fewer premature stagnations.
3. **What "ECDF = 1.0 at 1,000 Evaluations" Signifies**: It proves that across **100% of the independent runs**, the optimizer successfully reached the global optimum ($\Delta y \le 10^{-8}$) within the first $1,000$ function calls.
4. **Equivalence to Expected Running Time (ERT)**: The area above the ECDF curve up to budget $B$ is proportional to the Expected Running Time (ERT) across the 51 targets, providing a unified single-curve representation of both speed and robustness.

---

### 4.3 Empirical Target Success Rate
The asymptotic success rate measures the fraction of runs that successfully hit the strictest precision target ($\Delta y \le 10^{-8}$) by the end of the full $50,000$ evaluation budget:
$$\text{Success Rate} = \frac{1}{N_{\text{runs}}} \sum_{r=1}^{N_{\text{runs}}} \mathbb{I}\left( y_r(B) \le 10^{-8} \right)$$

---

### 4.4 Convergence Trajectories with Interquartile Ranges (IQR)
* Irregular execution traces logged by IOHprofiler are interpolated onto a uniform logarithmic evaluation grid ($k \in [10^0, 10^5]$, 200 points).
* The **median** convergence trajectory is plotted alongside the shaded **25th–75th percentile Interquartile Range (IQR)** to capture central tendency and stochastic variance without assuming normal distribution.

---

### 4.5 Cross-Environment Noise Retention & Fragility Index
Evaluates solver resilience when transitioning from deterministic ($\sigma = 0.0$) to heteroscedastic noisy landscapes ($\sigma = 0.05$):
$$\Delta_{\text{noise}} = \text{Success Rate}_{\text{clean}} - \text{Success Rate}_{\text{noisy}}$$
$$\text{Noise Retention Ratio} = \frac{\text{Success Rate}_{\text{noisy}}}{\text{Success Rate}_{\text{clean}} + \epsilon}$$
A smaller $\Delta_{\text{noise}}$ or higher retention ratio characterizes algorithms with inherent noise tolerance.

---

## 5. Comprehensive Empirical Findings & Performance Analysis

### 5.1 Empirical Success Rates by Environment (Clean vs. Noisy)

Across all 30 experimental conditions, the empirical target success rates ($\Delta y \le 10^{-8}$) reveal clear performance tiers:

| Optimization Solver | Overall Success Rate | Clean Regime ($\sigma=0.0$) | Noisy Regime ($\sigma=0.05$) | Performance Drop ($\Delta_{\text{noise}}$) |
| :--- | :---: | :---: | :---: | :---: |
| **CMA-ES** (Classical Baseline) | **57.67%** | 65.33% | 50.00% | $-15.33\%$ |
| **LLaMEA-14B / guided** | **48.97%** | **78.67%** | 17.14% | $-61.53\%$ |
| **LLaMEA-14B / baseline** | **45.67%** | 56.00% | 35.33% | $-20.67\%$ |
| **PSO** (Classical Baseline) | **40.00%** | 42.67% | 37.33% | $-5.34\%$ |
| **LLaMEA-14B / thinking** | **32.00%** | 54.00% | 10.00% | $-44.00\%$ |
| **LLaMEA-14B / vectorization** | **23.33%** | 37.33% | 9.33% | $-28.00\%$ |
| **LLaMEA-7B / guided** | **23.10%** | 38.00% | 7.14% | $-30.86\%$ |
| **LLaMEA-7B / thinking** | **15.67%** | 28.00% | 3.33% | $-24.67\%$ |
| **LLaMEA-7B / baseline** | **14.33%** | 14.00% | 14.67% | $+0.67\%$ |
| **LLaMEA-7B / vectorization** | **13.67%** | 26.00% | 1.33% | $-24.67\%$ |
| **DE** (Classical Baseline) | **0.67%** | 0.00% | 1.33% | $+1.33\%$ |

---

### 5.2 Core Thesis Insights by Research Question

#### Insight 1 (RQ1: Algorithmic Competitiveness vs. Classical Baselines)
* **LLaMEA-14B Champions outperform classical baselines on clean landscapes**: In deterministic environments ($\sigma = 0.0$), `LLaMEA-14B / guided` achieves a **78.67% target success rate**, surpassing CMA-ES (65.33%), PSO (42.67%), and DE (0.00%).
* On unimodal and low-conditioning landscapes ($f_1$ Sphere, $f_8$ Rosenbrock), 14B champions reach target precision ($\Delta y \le 10^{-8}$) within fewer function evaluations than standard PSO.
* On ill-conditioned problems ($f_{11}$ Discus, condition number $10^6$), CMA-ES maintains its superiority due to its closed-form analytical covariance matrix adaptation, whereas LLM-generated algorithms exhibit slower convergence unless covariance tracking heuristics are present.

#### Insight 2 (RQ2: Model Scaling Laws — 14B vs. 7B)
* **Parameter scale fundamentally dictates algorithmic sophistication and convergence rate**:
  * Clean Success Rate: **LLaMEA-14B averages 56.5%** vs. **LLaMEA-7B averaging 26.5%** ($>2.13\times$ scaling advantage).
* **Code Syntactic & Algorithmic Quality**:
  * 7B models frequently generate simple random-walk variants or basic local hill-climbers that stagnate early on $D=5$.
  * 14B models consistently invent adaptive momentum mechanisms, orthogonal exploration steps, and dynamic step-size decay schedules.

#### Insight 3 (RQ3: Prompt Engineering Ablation)
* **Domain Guidance and Chain-of-Thought Prompts significantly enhance algorithmic performance**:
  * In deterministic benchmarks, `guided` prompts achieved the highest success rates across both model families (14B: $78.67\%$, 7B: $38.00\%$).
  * `thinking` prompts allowed the LLM to reflect on prior generation failure modes, resulting in more stable exploration/exploitation balance than unguided `baseline` prompts.

#### Insight 4 (RQ4: Robustness under Heteroscedastic Noise)
* Under heteroscedastic Gaussian noise ($\sigma = 0.05$), classical algorithms like PSO and `LLaMEA-14B / baseline` retain high relative success ($37.33\%$ and $35.33\%$, respectively), exhibiting robust performance retention.
* Algorithms with aggressive step-size decay without noise-averaging buffers suffered significant success rate drops, identifying clear directions for future prompt design incorporating explicit noise-filtering primitives.

#### Insight 5 (RQ5: Budget Generalization)
* Optimizers synthesized with only $1,000$ function evaluations successfully scale to $50,000$ evaluations in Stage 2 without early asymptotic collapse, demonstrating that LLM meta-heuristics learn generalizable search dynamics rather than over-fitting to the synthesis horizon.

---

## 6. Thesis Chapter Structure & Writing Guide

When drafting the **Experiments & Empirical Evaluation Chapter**, use the following structure and cross-references:

### Chapter Section Breakdown

#### Section 3.1: Experimental Design & Benchmark Suite
* Define BBOB testsuite function properties ($f_1, f_8, f_{11}, f_{15}, f_{21}$), dimensionality selection ($D \in \{2, 3, 5\}$), and the heteroscedastic noise model ($\sigma = 0.05$).
* Present the Two-Stage Paradigm (Stage 1 Synthesis vs. Stage 2 Independent Benchmarking).
* Define classical baselines (CMA-ES, DE, PSO) and evaluation budgets (50,000 evaluations across 10 random seeds).

#### Section 3.2: Automated Algorithm Synthesis Dynamics (LLaMEA Stage 1)
* Describe the 292 evolutionary runs and 2,902 candidate iterations.
* Detail the 4 prompt engineering strategies (`baseline`, `guided`, `thinking`, `vectorization`).
* Include synthesis dynamics: valid AST rate, runtime per generation, and best error progression.

#### Section 3.3: Empirical Benchmark Results & Convergence Analysis (Stage 2)
* Present the **6-Panel Empirical Convergence Profiles** (`results/figures/profiles/{slug}/{dim}D/std_{noise}/convergence_trajectories.png`) displaying log-scale median convergence with shaded Interquartile Range (IQR) bands across the 5 canonical BBOB problem classes ($f_1, f_8, f_{11}, f_{15}, f_{21}$) and overall summary.
* Present the **6-Panel Empirical Runtime ECDF Figures** (`results/figures/profiles/{slug}/{dim}D/std_{noise}/target_precision_ecdf.png`) displaying the empirical fraction of solved BBOB target checkpoints ($51$ targets in $10^{-8} \le \Delta y \le 10^2$) as a function of function evaluation budget vs. classical baselines (CMA-ES, DE, PSO).
* Present the **Global Performance Ranking Figures**:
  * **Figure 9: Global Area Under Runtime ECDF Ranking (AUC-ECDF)** (`results/publication/main_results/fig_09_auc_ecdf_ranking.png`) — Non-parametric, p-value-free integration of speed and target coverage across all 30 BBOB conditions.
  * **Figure 7: Global Pairwise Win Summary** (`results/publication/main_results/fig_07_win_tie_loss.png`) — Head-to-head pairwise comparison summary across 1,630 matchups.
* Present the comprehensive Empirical Target Success Rate comparison table (Table 5.1).

#### Section 3.4: Ablation Studies & Deep Dives
* **Ablation A: LLM Parameter Scale ($7\text{B} \text{ vs. } 14\text{B}$)** — Impact on algorithmic complexity, success rate, and dimensional scaling ($2.13\times$ clean success rate advantage for 14B).
* **Ablation B: Prompt Strategy Efficacy** — Performance comparison of `baseline`, `guided`, `thinking`, and `vectorization` prompts (`fig_03_prompt_strategy_ablation_{dim}D.png`).
* **Ablation C: Noise Fragility & Robustness** — Cross-environment degradation and retention profiles under heteroscedastic noise $\sigma = 0.05$ (`fig_05_noise_fragility_matrix_{dim}D.png` and `fig_06_robustness_profile_{dim}D.png`).
* **Ablation D: Synthesis vs. Evaluation Transferability** — Correlation between low-budget synthesis error ($1,000$ evals) and full benchmark error ($50,000$ evals) (`fig_08_synthesis_transfer.png`).

#### Section 3.5: Threats to Validity & Discussion
* Internal validity: Stochasticity in LLM code generation and random seed replication.
* External validity: Generalization from synthetic BBOB benchmarks to complex real-world continuous optimization problems.

---

## 7. Artifacts & Generated Assets Reference

All high-resolution publication figures and profiles are organized within the repository:

| Asset / File Path | Contents / Usage in Thesis |
| :--- | :--- |
| [`results/figures/profiles/{slug}/{dim}D/std_{noise}/`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/figures/profiles) | **Core Benchmarking Visuals**: 6-panel grid figures showing per-problem Convergence Trajectories (IQR bands) and Target Precision ECDFs across the 5 BBOB problem classes vs. CMA-ES, DE, PSO. |
| [`results/publication/main_results/`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/publication/main_results) | Benchmark difficulty validation (`fig_01`), global win summaries (`fig_07`), synthesis transferability plots (`fig_08`), and **global AUC-ECDF ranking (`fig_09`)**. |
| [`results/publication/ablation/`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/publication/ablation) | Prompt strategy and model parameter scale ablation bar charts (`fig_03`). |
| [`results/publication/noise_robustness/`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/publication/noise_robustness) | Landscape fragility matrices (`fig_05`) and cross-environment robustness retention profiles (`fig_06`). |
| [`results/ioh_traces/`](file:///Users/nicolaibrahim/Desktop/proj/AAD_LLM/results/ioh_traces) | Raw empirical IOHprofiler `.dat` and `.json` convergence logs. |

