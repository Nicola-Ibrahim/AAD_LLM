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
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 103.5519781639735 | 1.0579534309818317e-17 | Yes | 11 |
| 2 | 0.0 | 1 | Sphere (f1) | Separable | 108.17540276200583 | 1.244216916150372e-18 | Yes | 11 |
| 2 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 90.71386432286344 | 3.865704508122874e-15 | Yes | 11 |
| 2 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 80.83879672205784 | 3.4375460446406537e-13 | Yes | 11 |
| 2 | 0.0 | 11 | Discus (f11) | High Conditioning | 98.19865946322103 | 1.2491470707073854e-16 | Yes | 11 |
| 2 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 88.86121314656077 | 9.005631784348318e-15 | Yes | 11 |
| 2 | 0.05 | 1 | Sphere (f1) | Separable | 100.65666182314897 | 4.026382742378624e-17 | Yes | 11 |
| 2 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 78.84652265305007 | 8.446074764185918e-13 | Yes | 11 |
| 2 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 82.47176183038984 | 1.6424982489847858e-13 | Yes | 11 |
| 2 | 0.05 | 11 | Discus (f11) | High Conditioning | 56.60146712053915 | 1.583497176371945e-08 | Yes | 11 |
| 5 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 96.5182658073411 | 2.7049728809107193e-16 | Yes | 11 |
| 5 | 0.0 | 1 | Sphere (f1) | Separable | 104.23047299563905 | 7.731288430783777e-18 | Yes | 11 |
| 5 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 97.75231534289435 | 1.5338748757512835e-16 | Yes | 11 |
| 5 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 71.96106218004913 | 1.8514285064661385e-11 | Yes | 11 |
| 5 | 0.0 | 11 | Discus (f11) | High Conditioning | 102.27765293383275 | 1.905926269400371e-17 | Yes | 11 |
| 5 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 96.82317107808002 | 2.351336633691221e-16 | Yes | 11 |
| 5 | 0.05 | 1 | Sphere (f1) | Separable | 97.51364495298523 | 1.7118289695125369e-16 | Yes | 11 |
| 5 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 88.16863366336628 | 3.791614355958277e-15 | Yes | 10 |
| 5 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 74.2243960396039 | 2.2480074868235985e-12 | Yes | 10 |
| 5 | 0.05 | 11 | Discus (f11) | High Conditioning | 92.77242965575397 | 1.5076896433260103e-15 | Yes | 11 |
| 3 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 106.20676101646343 | 3.098081762473807e-18 | Yes | 11 |
| 3 | 0.0 | 1 | Sphere (f1) | Separable | 94.94846965749632 | 5.561258215410489e-16 | Yes | 11 |
| 3 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 96.88314990821208 | 2.287405994036169e-16 | Yes | 11 |
| 3 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 84.03565833590264 | 8.085778659610463e-14 | Yes | 11 |
| 3 | 0.0 | 11 | Discus (f11) | High Conditioning | 96.76044265950685 | 2.4201065741909013e-16 | Yes | 11 |
| 3 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 91.48245445048902 | 2.7205232656156425e-15 | Yes | 11 |
| 3 | 0.05 | 1 | Sphere (f1) | Separable | 104.3226350311382 | 7.408733103029464e-18 | Yes | 11 |
| 3 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 92.13012285012286 | 2.0229729947732633e-15 | Yes | 11 |
| 3 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 79.0041198569439 | 7.86700963482474e-13 | Yes | 11 |
| 3 | 0.05 | 11 | Discus (f11) | High Conditioning | 111.44743139025918 | 2.723790390333797e-19 | Yes | 11 |

## 3. Pairwise Statistical Comparisons (FDR-Corrected)

| Dim | Noise Std | Problem ID | Problem Name | Function Class | Solver 1 | Solver 2 | Median 1 | Median 2 | Solver 1 Med | Solver 2 Med | U-Stat | p-value | A12 | A12 Magnitude | Comparison Tier | p-adjusted | Significant (FDR) | p-value-adj | FDR_Sig | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | DE | 0.0 | 4.5e-10 | 0.0 | 4.5e-10 | 15.0 | 0.0022125420307360344 | 0.85 | large | Tier 3 (Classical vs. Classical) | 0.0034347081048568917 | True | 0.0034347081048568917 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-14B / baseline | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 2 (LLaMEA vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 10.0 | 0.0007467880185761928 | 0.9 | large | Tier 2 (LLaMEA vs. Classical) | 0.0012614139588385434 | True | 0.0012614139588385434 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-14B / thinking | 0.0 | 1.0087499999999999e-06 | 0.0 | 1.0087499999999999e-06 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-14B / vectorization | 0.0 | 1.939605e-05 | 0.0 | 1.939605e-05 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-7B / baseline | 0.0 | 138911.19265567663 | 0.0 | 138911.19265567663 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-7B / guided | 0.0 | 4365.643946387 | 0.0 | 4365.643946387 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 2 (LLaMEA vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | LLaMEA-7B / vectorization | 0.0 | 0.010897929 | 0.0 | 0.010897929 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | PSO | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 3 (Classical vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-14B / baseline | 4.5e-10 | 0.0 | 4.5e-10 | 0.0 | 85.0 | 0.0022125420307360344 | 0.15 | large | Tier 2 (LLaMEA vs. Classical) | 0.0034347081048568917 | True | 0.0034347081048568917 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-14B / guided | 4.5e-10 | 3.5000000000000003e-10 | 4.5e-10 | 3.5000000000000003e-10 | 48.0 | 0.9088997388029892 | 0.52 | negligible | Tier 2 (LLaMEA vs. Classical) | 0.9761992622167579 | False | 0.9761992622167579 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-14B / thinking | 4.5e-10 | 1.0087499999999999e-06 | 4.5e-10 | 1.0087499999999999e-06 | 10.0 | 0.00278594464156807 | 0.9 | large | Tier 2 (LLaMEA vs. Classical) | 0.004302944452399997 | True | 0.004302944452399997 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-14B / vectorization | 4.5e-10 | 1.939605e-05 | 4.5e-10 | 1.939605e-05 | 9.0 | 0.0021685160641053097 | 0.91 | large | Tier 2 (LLaMEA vs. Classical) | 0.0034347081048568917 | True | 0.0034347081048568917 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-7B / baseline | 4.5e-10 | 138911.19265567663 | 4.5e-10 | 138911.19265567663 | 0.0 | 0.00017861448837368167 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-7B / guided | 4.5e-10 | 4365.643946387 | 4.5e-10 | 4365.643946387 | 0.0 | 0.00017861448837368167 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-7B / thinking | 4.5e-10 | 0.0 | 4.5e-10 | 0.0 | 85.0 | 0.0022125420307360344 | 0.15 | large | Tier 2 (LLaMEA vs. Classical) | 0.0034347081048568917 | True | 0.0034347081048568917 | True | LLaMEA-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | LLaMEA-7B / vectorization | 4.5e-10 | 0.010897929 | 4.5e-10 | 0.010897929 | 0.0 | 0.00017861448837368167 | 1.0 | large | Tier 2 (LLaMEA vs. Classical) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | PSO | 4.5e-10 | 0.0 | 4.5e-10 | 0.0 | 85.0 | 0.0022125420307360344 | 0.15 | large | Tier 3 (Classical vs. Classical) | 0.0034347081048568917 | True | 0.0034347081048568917 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 10.0 | 0.0007467880185761928 | 0.9 | large | Tier 1 (LLaMEA Intra-Model / Strategies) | 0.0012614139588385434 | True | 0.0012614139588385434 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-14B / thinking | 0.0 | 1.0087499999999999e-06 | 0.0 | 1.0087499999999999e-06 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 1 (LLaMEA Intra-Model / Strategies) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-14B / vectorization | 0.0 | 1.939605e-05 | 0.0 | 1.939605e-05 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 1 (LLaMEA Intra-Model / Strategies) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-7B / baseline | 0.0 | 138911.19265567663 | 0.0 | 138911.19265567663 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 1 (LLaMEA Intra-Model / Strategies) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-7B / guided | 0.0 | 4365.643946387 | 0.0 | 4365.643946387 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 1 (LLaMEA Intra-Model / Strategies) | 0.0003450231975765545 | True | 0.0003450231975765545 | True | LLaMEA-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | LLaMEA-14B / baseline | LLaMEA-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 1 (LLaMEA Intra-Model / Strategies) | 1.0 | False | 1.0 | False | Tie |
