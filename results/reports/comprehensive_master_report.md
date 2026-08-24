# Comprehensive Empirical Evaluation & Statistical Analysis Report

## 1. Overview & Experimental Protocol
- **Benchmark Suite**: BBOB (Black-Box Optimization Benchmarking)
- **Statistical Protocols**: Kruskal-Wallis H-test (omnibus), Mann-Whitney U test (pairwise)
- **Multiplicity Correction**: Benjamini-Hochberg False Discovery Rate (FDR, $\alpha=0.05$)
- **Effect Size Metric**: Vargha-Delaney $\hat{A}_{12}$ statistic

## 2. Omnibus Kruskal-Wallis Test Summary

- **Total Experimental Conditions Analyzed**: 30
- **Statistically Significant Differences Found**: 30 (100.0%)

### Omnibus Results Table
| Dim | Noise Std | Problem ID | Problem Name | Function Class | H-Statistic | p-value | Significant | Solvers Count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 106.74426775765849 | 2.4153138998123388e-18 | Yes | 11 |
| 2 | 0.0 | 1 | Sphere (f1) | Separable | 106.63253006194587 | 2.543624951761941e-18 | Yes | 11 |
| 2 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 90.56195559078648 | 4.143532211350358e-15 | Yes | 11 |
| 2 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 80.95790336237738 | 3.257438520661363e-13 | Yes | 11 |
| 2 | 0.0 | 11 | Discus (f11) | High Conditioning | 99.2561864056123 | 7.676985801902695e-17 | Yes | 11 |
| 2 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 85.98164638276997 | 3.3415347837912677e-14 | Yes | 11 |
| 2 | 0.05 | 1 | Sphere (f1) | Separable | 100.19720114960977 | 4.976252172852653e-17 | Yes | 11 |
| 2 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 78.35170281291155 | 1.055502534197575e-12 | Yes | 11 |
| 2 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 82.46312136382724 | 1.6489359221412825e-13 | Yes | 11 |
| 2 | 0.05 | 11 | Discus (f11) | High Conditioning | 57.81904950852191 | 9.350108793952495e-09 | Yes | 11 |
| 5 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 95.95158776517466 | 3.509193586353572e-16 | Yes | 11 |
| 5 | 0.0 | 1 | Sphere (f1) | Separable | 104.64062439583252 | 6.395515237799951e-18 | Yes | 11 |
| 5 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 97.95920677715463 | 1.3946293341124897e-16 | Yes | 11 |
| 5 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 69.03524676869439 | 6.805990038211013e-11 | Yes | 11 |
| 5 | 0.0 | 11 | Discus (f11) | High Conditioning | 103.84984587447505 | 9.218820559238698e-18 | Yes | 11 |
| 5 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 96.74323712660163 | 2.4393175698409397e-16 | Yes | 11 |
| 5 | 0.05 | 1 | Sphere (f1) | Separable | 96.50225535289452 | 2.724943915185328e-16 | Yes | 11 |
| 5 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 88.40221782178213 | 3.404314024533659e-15 | Yes | 10 |
| 5 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 72.86432317607374 | 4.166935286326903e-12 | Yes | 10 |
| 5 | 0.05 | 11 | Discus (f11) | High Conditioning | 92.67381436604606 | 1.5773205018701078e-15 | Yes | 11 |
| 3 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 107.01721516657464 | 2.1284040723112832e-18 | Yes | 11 |
| 3 | 0.0 | 1 | Sphere (f1) | Separable | 93.70232971229687 | 9.84748552102807e-16 | Yes | 11 |
| 3 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 96.3725253850155 | 2.8922884532021765e-16 | Yes | 11 |
| 3 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 84.70574965704468 | 5.965795576008548e-14 | Yes | 11 |
| 3 | 0.0 | 11 | Discus (f11) | High Conditioning | 96.97304262203622 | 2.1948245314849693e-16 | Yes | 11 |
| 3 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 87.46669196505195 | 1.7002131239775615e-14 | Yes | 11 |
| 3 | 0.05 | 1 | Sphere (f1) | Separable | 103.18181430702566 | 1.2553088019302574e-17 | Yes | 11 |
| 3 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 91.99930030521479 | 2.147757441622448e-15 | Yes | 11 |
| 3 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 78.2094413382631 | 1.1253266364391127e-12 | Yes | 11 |
| 3 | 0.05 | 11 | Discus (f11) | High Conditioning | 108.55714285714284 | 1.0423289616456424e-18 | Yes | 11 |

## 3. Pairwise Statistical Comparisons (FDR-Corrected)

| Dim | Noise Std | Problem ID | Problem Name | Function Class | Solver 1 | Solver 2 | Median 1 | Median 2 | Solver 1 Med | Solver 2 Med | U-Stat | p-value | A12 | A12 Magnitude | Comparison Tier | p-adjusted | Significant (FDR) | p-value-adj | FDR_Sig | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | DE | 0.0 | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-14B / baseline | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 2 (LLaMEA vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 10.0 | 0.0007467880185761928 | 0.9 | large | Tier 2 (LLaMEA vs. Classical) | 0.001238315839551571 | True | 0.001238315839551571 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-14B / thinking | 0.0 | 1.0087499999999999e-06 | 0.0 | 1.0087499999999999e-06 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-14B / vectorization | 0.0 | 1.939605e-05 | 0.0 | 1.939605e-05 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-7B / baseline | 0.0 | 138911.19265567663 | 0.0 | 138911.19265567663 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-7B / guided | 0.0 | 4365.643946387 | 0.0 | 4365.643946387 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 2 (LLaMEA vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-7B / vectorization | 0.0 | 0.010897929 | 0.0 | 0.010897929 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | PSO | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 3 (Classical vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-14B / baseline | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 100.0 | 6.386444750436982e-05 | 0.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-14B / guided | 0.0036945288 | 3.5000000000000003e-10 | 0.0036945288 | 3.5000000000000003e-10 | 100.0 | 0.00018063472080753515 | 0.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | LLaMEA-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-14B / thinking | 0.0036945288 | 1.0087499999999999e-06 | 0.0036945288 | 1.0087499999999999e-06 | 100.0 | 0.00018267179110955002 | 0.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | LLaMEA-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-14B / vectorization | 0.0036945288 | 1.939605e-05 | 0.0036945288 | 1.939605e-05 | 100.0 | 0.00018267179110955002 | 0.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | LLaMEA-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-7B / baseline | 0.0036945288 | 138911.19265567663 | 0.0036945288 | 138911.19265567663 | 0.0 | 0.00018267179110955002 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-7B / guided | 0.0036945288 | 4365.643946387 | 0.0036945288 | 4365.643946387 | 0.0 | 0.00018267179110955002 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-7B / thinking | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 100.0 | 6.386444750436982e-05 | 0.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | LLaMEA-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-7B / vectorization | 0.0036945288 | 0.010897929 | 0.0036945288 | 0.010897929 | 32.0 | 0.18587673236587599 | 0.68 | medium | Tier 2 (LLaMEA vs. Classical) | 0.2203484172773657 | False | 0.2203484172773657 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | PSO | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 100.0 | 6.386444750436982e-05 | 0.0 | large | Tier 3 (Classical vs. Classical) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 10.0 | 0.0007467880185761928 | 0.9 | large | Tier 1 (LLaMEA Intra-Model / Strategies) | 0.001238315839551571 | True | 0.001238315839551571 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-14B / thinking | 0.0 | 1.0087499999999999e-06 | 0.0 | 1.0087499999999999e-06 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 1 (LLaMEA Intra-Model / Strategies) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-14B / vectorization | 0.0 | 1.939605e-05 | 0.0 | 1.939605e-05 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 1 (LLaMEA Intra-Model / Strategies) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-7B / baseline | 0.0 | 138911.19265567663 | 0.0 | 138911.19265567663 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 1 (LLaMEA Intra-Model / Strategies) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-7B / guided | 0.0 | 4365.643946387 | 0.0 | 4365.643946387 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 1 (LLaMEA Intra-Model / Strategies) | 0.00033797391544672703 | True | 0.00033797391544672703 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 1 (LLaMEA Intra-Model / Strategies) | 1.0 | False | 1.0 | False | Tie |
