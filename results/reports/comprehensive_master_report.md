# Comprehensive Empirical Evaluation & Statistical Analysis Report

## 1. Overview & Experimental Protocol
- **Benchmark Suite**: BBOB (Black-Box Optimization Benchmarking)
- **Statistical Protocols**: Kruskal-Wallis H-test (omnibus), Mann-Whitney U test (pairwise)
- **Multiplicity Correction**: Benjamini-Hochberg False Discovery Rate (FDR, $\alpha=0.05$)
- **Effect Size Metric**: Vargha-Delaney $\hat{A}_{12}$ statistic

## 2. Omnibus Kruskal-Wallis Test Summary

- **Total Problem Conditions Tested**: 30
- **Significant Differences Detected (p < 0.05)**: 30 / 30 (100.0%)

### Omnibus Results Table

| Dim | Noise Std | Problem ID | Problem Name | Function Class | H-Statistic | p-value | Significant | Solvers Count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 93.79829598177878 | 9.423782752554111e-16 | Yes | 11 |
| 2 | 0.0 | 1 | Sphere (f1) | Separable | 106.41749340763221 | 2.8100186121222845e-18 | Yes | 11 |
| 2 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 88.78865755663499 | 9.308587596402929e-15 | Yes | 11 |
| 2 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 89.75397893245992 | 5.992562620751042e-15 | Yes | 11 |
| 2 | 0.0 | 11 | Discus (f11) | High Conditioning | 93.33650118953217 | 1.1644474833707526e-15 | Yes | 11 |
| 2 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 77.41529728141728 | 1.6086946290373861e-12 | Yes | 11 |
| 2 | 0.05 | 1 | Sphere (f1) | Separable | 102.03232510148085 | 2.134476029435884e-17 | Yes | 11 |
| 2 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 82.78680168700242 | 1.4241323660629483e-13 | Yes | 11 |
| 2 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 92.68132542774207 | 1.5719059780196245e-15 | Yes | 11 |
| 2 | 0.05 | 11 | Discus (f11) | High Conditioning | 64.30773920101 | 5.497177350667728e-10 | Yes | 11 |
| 5 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 97.3188652866099 | 1.8722204874919377e-16 | Yes | 11 |
| 5 | 0.0 | 1 | Sphere (f1) | Separable | 104.29502427572966 | 7.503931520324793e-18 | Yes | 11 |
| 5 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 96.22880155452555 | 3.089685071787e-16 | Yes | 11 |
| 5 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 48.18885522614155 | 2.3546595766054438e-07 | Yes | 10 |
| 5 | 0.0 | 11 | Discus (f11) | High Conditioning | 104.28050389596285 | 7.554484965283063e-18 | Yes | 11 |
| 5 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 99.73784522167223 | 6.149414390011147e-17 | Yes | 11 |
| 5 | 0.05 | 1 | Sphere (f1) | Separable | 103.63354979041571 | 1.0188118565136422e-17 | Yes | 11 |
| 5 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 87.32887128712878 | 5.584338190451205e-15 | Yes | 10 |
| 5 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 74.84021218631104 | 1.6993557207163645e-12 | Yes | 10 |
| 5 | 0.05 | 11 | Discus (f11) | High Conditioning | 94.94760708697281 | 5.563459482882091e-16 | Yes | 11 |
| 3 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 103.86760459895225 | 9.143452370274406e-18 | Yes | 11 |
| 3 | 0.0 | 1 | Sphere (f1) | Separable | 93.49796711858728 | 1.08141817348344e-15 | Yes | 11 |
| 3 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 85.29489721612892 | 4.565422432910975e-14 | Yes | 11 |
| 3 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 76.60412841396382 | 2.3164205028936892e-12 | Yes | 11 |
| 3 | 0.0 | 11 | Discus (f11) | High Conditioning | 99.09799052560341 | 8.257140401180301e-17 | Yes | 11 |
| 3 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 82.39781532345492 | 1.6984136919599098e-13 | Yes | 11 |
| 3 | 0.05 | 1 | Sphere (f1) | Separable | 97.8558383949936 | 1.4625470429664457e-16 | Yes | 11 |
| 3 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 87.87087204872613 | 1.4143434758048126e-14 | Yes | 11 |
| 3 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 68.91549328163053 | 7.177475900609796e-11 | Yes | 11 |
| 3 | 0.05 | 11 | Discus (f11) | High Conditioning | 97.23775162890212 | 1.9433591245283782e-16 | Yes | 11 |

## 3. Pairwise Post-Hoc Tests (Mann-Whitney U with FDR Correction)

- **Total Pairwise Comparisons**: 1620
- **Statistically Significant After FDR**: 1253 / 1620

### Pairwise Statistical Comparisons

| Dim | Noise Std | Problem ID | Problem Name | Function Class | Solver 1 | Solver 2 | Median 1 | Median 2 | Solver 1 Med | Solver 2 Med | U-Stat | p-value | A12 | A12 Magnitude | Comparison Tier | p-adjusted | Significant (FDR) | p-value-adj | FDR_Sig | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | DE | 0.0 | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | PSO | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 3 (Classical vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / baseline | 0.0 | 0.4432593187 | 0.0 | 0.4432593187 | 15.0 | 0.0022125420307360344 | 0.85 | large | Tier 3 (Classical vs. Classical) | 0.00340068129961326 | True | 0.00340068129961326 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 10.0 | 0.0007467880185761928 | 0.9 | large | Tier 3 (Classical vs. Classical) | 0.0012497898657990005 | True | 0.0012497898657990005 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / thinking | 0.0 | 1.13191e-05 | 0.0 | 1.13191e-05 | 10.0 | 0.0007511794334780429 | 0.9 | large | Tier 3 (Classical vs. Classical) | 0.001253255079541122 | True | 0.001253255079541122 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / vectorization | 0.0 | 0.00036183215 | 0.0 | 0.00036183215 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / baseline | 0.0 | 138911.19265567663 | 0.0 | 138911.19265567663 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / guided | 0.0 | 4365.643946387 | 0.0 | 4365.643946387 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 3 (Classical vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / vectorization | 0.0 | 0.010897929 | 0.0 | 0.010897929 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | PSO | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 100.0 | 6.386444750436982e-05 | 0.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / baseline | 0.0036945288 | 0.4432593187 | 0.0036945288 | 0.4432593187 | 30.0 | 0.13986791147975935 | 0.7 | medium | Tier 3 (Classical vs. Classical) | 0.16695038739290907 | False | 0.16695038739290907 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / guided | 0.0036945288 | 3.5000000000000003e-10 | 0.0036945288 | 3.5000000000000003e-10 | 100.0 | 0.00018063472080753515 | 0.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / thinking | 0.0036945288 | 1.13191e-05 | 0.0036945288 | 1.13191e-05 | 98.0 | 0.0003281333148201422 | 0.02 | large | Tier 3 (Classical vs. Classical) | 0.0005751758919917648 | True | 0.0005751758919917648 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / vectorization | 0.0036945288 | 0.00036183215 | 0.0036945288 | 0.00036183215 | 74.0 | 0.07566157214388701 | 0.26 | large | Tier 3 (Classical vs. Classical) | 0.09464999758540306 | False | 0.09464999758540306 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / baseline | 0.0036945288 | 138911.19265567663 | 0.0036945288 | 138911.19265567663 | 0.0 | 0.00018267179110955002 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / guided | 0.0036945288 | 4365.643946387 | 0.0036945288 | 4365.643946387 | 0.0 | 0.00018267179110955002 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / thinking | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 100.0 | 6.386444750436982e-05 | 0.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / vectorization | 0.0036945288 | 0.010897929 | 0.0036945288 | 0.010897929 | 32.0 | 0.18587673236587599 | 0.68 | medium | Tier 3 (Classical vs. Classical) | 0.21663331398037344 | False | 0.21663331398037344 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / baseline | 0.0 | 0.4432593187 | 0.0 | 0.4432593187 | 15.0 | 0.0022125420307360344 | 0.85 | large | Tier 3 (Classical vs. Classical) | 0.00340068129961326 | True | 0.00340068129961326 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 10.0 | 0.0007467880185761928 | 0.9 | large | Tier 3 (Classical vs. Classical) | 0.0012497898657990005 | True | 0.0012497898657990005 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / thinking | 0.0 | 1.13191e-05 | 0.0 | 1.13191e-05 | 10.0 | 0.0007511794334780429 | 0.9 | large | Tier 3 (Classical vs. Classical) | 0.001253255079541122 | True | 0.001253255079541122 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / vectorization | 0.0 | 0.00036183215 | 0.0 | 0.00036183215 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / baseline | 0.0 | 138911.19265567663 | 0.0 | 138911.19265567663 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / guided | 0.0 | 4365.643946387 | 0.0 | 4365.643946387 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 3 (Classical vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / vectorization | 0.0 | 0.010897929 | 0.0 | 0.010897929 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / guided | 0.4432593187 | 3.5000000000000003e-10 | 0.4432593187 | 3.5000000000000003e-10 | 73.0 | 0.08644997593889946 | 0.27 | large | Tier 3 (Classical vs. Classical) | 0.10772997001616702 | False | 0.10772997001616702 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / thinking | 0.4432593187 | 1.13191e-05 | 0.4432593187 | 1.13191e-05 | 73.0 | 0.08657015565562572 | 0.27 | large | Tier 3 (Classical vs. Classical) | 0.1077968118079275 | False | 0.1077968118079275 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / vectorization | 0.4432593187 | 0.00036183215 | 0.4432593187 | 0.00036183215 | 70.0 | 0.13986791147975935 | 0.3 | medium | Tier 3 (Classical vs. Classical) | 0.16695038739290907 | False | 0.16695038739290907 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / baseline | 0.4432593187 | 138911.19265567663 | 0.4432593187 | 138911.19265567663 | 0.0 | 0.00017861448837368167 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / guided | 0.4432593187 | 4365.643946387 | 0.4432593187 | 4365.643946387 | 2.0 | 0.0003230556926118561 | 0.98 | large | Tier 3 (Classical vs. Classical) | 0.000573848927665797 | True | 0.000573848927665797 | True | Qwen2.5-Coder-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / thinking | 0.4432593187 | 0.0 | 0.4432593187 | 0.0 | 85.0 | 0.0022125420307360344 | 0.15 | large | Tier 3 (Classical vs. Classical) | 0.00340068129961326 | True | 0.00340068129961326 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / vectorization | 0.4432593187 | 0.010897929 | 0.4432593187 | 0.010897929 | 70.0 | 0.13986791147975935 | 0.3 | medium | Tier 3 (Classical vs. Classical) | 0.16695038739290907 | False | 0.16695038739290907 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-14B / thinking | 3.5000000000000003e-10 | 1.13191e-05 | 3.5000000000000003e-10 | 1.13191e-05 | 18.0 | 0.016798679062603412 | 0.82 | large | Tier 3 (Classical vs. Classical) | 0.0232002217232886 | True | 0.0232002217232886 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-14B / vectorization | 3.5000000000000003e-10 | 0.00036183215 | 3.5000000000000003e-10 | 0.00036183215 | 0.0 | 0.00018063472080753515 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / baseline | 3.5000000000000003e-10 | 138911.19265567663 | 3.5000000000000003e-10 | 138911.19265567663 | 0.0 | 0.00018063472080753515 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / guided | 3.5000000000000003e-10 | 4365.643946387 | 3.5000000000000003e-10 | 4365.643946387 | 0.0 | 0.00018063472080753515 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / thinking | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 0.0 | 90.0 | 0.0007467880185761928 | 0.1 | large | Tier 3 (Classical vs. Classical) | 0.0012497898657990005 | True | 0.0012497898657990005 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / vectorization | 3.5000000000000003e-10 | 0.010897929 | 3.5000000000000003e-10 | 0.010897929 | 0.0 | 0.00018063472080753515 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-14B / vectorization | 1.13191e-05 | 0.00036183215 | 1.13191e-05 | 0.00036183215 | 16.0 | 0.01129895191826991 | 0.84 | large | Tier 3 (Classical vs. Classical) | 0.015960094459868658 | True | 0.015960094459868658 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / baseline | 1.13191e-05 | 138911.19265567663 | 1.13191e-05 | 138911.19265567663 | 0.0 | 0.0001816511460914649 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / guided | 1.13191e-05 | 4365.643946387 | 1.13191e-05 | 4365.643946387 | 0.0 | 0.0001816511460914649 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / thinking | 1.13191e-05 | 0.0 | 1.13191e-05 | 0.0 | 90.0 | 0.0007511794334780429 | 0.1 | large | Tier 3 (Classical vs. Classical) | 0.001253255079541122 | True | 0.001253255079541122 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / vectorization | 1.13191e-05 | 0.010897929 | 1.13191e-05 | 0.010897929 | 1.0 | 0.00024480482452445495 | 0.99 | large | Tier 3 (Classical vs. Classical) | 0.0004386441883459539 | True | 0.0004386441883459539 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / baseline | 0.00036183215 | 138911.19265567663 | 0.00036183215 | 138911.19265567663 | 0.0 | 0.00018267179110955002 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / guided | 0.00036183215 | 4365.643946387 | 0.00036183215 | 4365.643946387 | 0.0 | 0.00018267179110955002 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / thinking | 0.00036183215 | 0.0 | 0.00036183215 | 0.0 | 100.0 | 6.386444750436982e-05 | 0.0 | large | Tier 3 (Classical vs. Classical) | 0.0003393673183457236 | True | 0.0003393673183457236 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / vectorization | 0.00036183215 | 0.010897929 | 0.00036183215 | 0.010897929 | 13.0 | 0.00579535854433471 | 0.87 | large | Tier 3 (Classical vs. Classical) | 0.008435292759948096 | True | 0.008435292759948096 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-7B / baseline | Qwen2.5-Coder-7B / guided | 138911.19265567663 | 4365.643946387 | 138911.19265567663 | 4365.643946387 | 89.0 | 0.003610514312329602 | 0.11 | large | Tier 3 (Classical vs. Classical) | 0.005361166989893634 | True | 0.005361166989893634 | True | Qwen2.5-Coder-7B / guided Wins |
