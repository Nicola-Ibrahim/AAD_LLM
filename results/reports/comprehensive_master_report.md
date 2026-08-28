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
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 105.54993089390693 | 4.1990976615676134e-18 | Yes | 11 |
| 2 | 0.0 | 1 | Sphere (f1) | Separable | 181.53956728498602 | 1.1222387965140424e-33 | Yes | 11 |
| 2 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 121.75775408696266 | 2.2248103594379007e-21 | Yes | 11 |
| 2 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 125.1682404496017 | 4.507161657485041e-22 | Yes | 11 |
| 2 | 0.0 | 11 | Discus (f11) | High Conditioning | 124.7894311578307 | 5.382475572353785e-22 | Yes | 11 |
| 2 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 102.0764352259683 | 2.0914546784919784e-17 | Yes | 11 |
| 2 | 0.05 | 1 | Sphere (f1) | Separable | 138.137207491647 | 1.014634921608382e-24 | Yes | 11 |
| 2 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 91.88450600406837 | 2.2635637040163518e-15 | Yes | 11 |
| 2 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 114.43657705971263 | 6.779935528911874e-20 | Yes | 11 |
| 2 | 0.05 | 11 | Discus (f11) | High Conditioning | 83.61448450057418 | 9.787417939805711e-14 | Yes | 11 |
| 5 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 128.3172718220453 | 1.0293456310851703e-22 | Yes | 11 |
| 5 | 0.0 | 1 | Sphere (f1) | Separable | 153.43320930067568 | 7.322926533532829e-28 | Yes | 11 |
| 5 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 129.06874928884343 | 7.233715815057901e-23 | Yes | 11 |
| 5 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 81.21362851529166 | 2.9019054814184474e-13 | Yes | 11 |
| 5 | 0.0 | 11 | Discus (f11) | High Conditioning | 131.92982298995778 | 1.886137458986265e-23 | Yes | 11 |
| 5 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 135.50315481248913 | 3.510306175699493e-24 | Yes | 11 |
| 5 | 0.05 | 1 | Sphere (f1) | Separable | 140.23808431466546 | 3.7665518343612506e-25 | Yes | 11 |
| 5 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 120.62927051671738 | 9.931855932976364e-22 | Yes | 10 |
| 5 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 83.92122215212174 | 2.6785080823859042e-14 | Yes | 10 |
| 5 | 0.05 | 11 | Discus (f11) | High Conditioning | 121.2947515997858 | 2.762655138312809e-21 | Yes | 11 |
| 3 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 129.38086955568238 | 6.247616024304998e-23 | Yes | 11 |
| 3 | 0.0 | 1 | Sphere (f1) | Separable | 159.2227819295964 | 4.6880707610431194e-29 | Yes | 11 |
| 3 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 111.94732543546566 | 2.1590048246602132e-19 | Yes | 11 |
| 3 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 90.9549998758552 | 3.46236203520163e-15 | Yes | 11 |
| 3 | 0.0 | 11 | Discus (f11) | High Conditioning | 123.24416323048493 | 1.1098060776036218e-21 | Yes | 11 |
| 3 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 92.01693206816168 | 2.130501777911161e-15 | Yes | 11 |
| 3 | 0.05 | 1 | Sphere (f1) | Separable | 147.4713204897484 | 1.2341973684259105e-26 | Yes | 11 |
| 3 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 113.45733664491142 | 1.0695642408240189e-19 | Yes | 11 |
| 3 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 79.25883916506645 | 7.013611408133375e-13 | Yes | 11 |
| 3 | 0.05 | 11 | Discus (f11) | High Conditioning | 121.50675345451997 | 2.501918134271865e-21 | Yes | 11 |

## 3. Pairwise Post-Hoc Tests (Mann-Whitney U with FDR Correction)

- **Total Pairwise Comparisons**: 1630
- **Statistically Significant After FDR**: 1277 / 1630

### Pairwise Statistical Comparisons

| Dim | Noise Std | Problem ID | Problem Name | Function Class | Solver 1 | Solver 2 | Median 1 | Median 2 | Solver 1 Med | Solver 2 Med | U-Stat | p-value | A12 | A12 Magnitude | Comparison Tier | p-adjusted | Significant (FDR) | p-value-adj | FDR_Sig | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | DE | 0.0 | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.00015287611430838007 | True | 0.00015287611430838007 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | PSO | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 3 (Classical vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / baseline | 0.0 | 0.11154009640000001 | 0.0 | 0.11154009640000001 | 35.0 | 0.0017093888797144682 | 0.825 | large | Tier 3 (Classical vs. Classical) | 0.0025218182099084325 | True | 0.0025218182099084325 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 10.0 | 0.0007467880185761928 | 0.9 | large | Tier 3 (Classical vs. Classical) | 0.0011512684190681786 | True | 0.0011512684190681786 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / thinking | 0.0 | 8.10155e-06 | 0.0 | 8.10155e-06 | 15.0 | 0.00010539242746175711 | 0.925 | large | Tier 3 (Classical vs. Classical) | 0.0002450031755279808 | True | 0.0002450031755279808 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / vectorization | 0.0 | 0.0007107627 | 0.0 | 0.0007107627 | 0.0 | 8.194433744518873e-06 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.82355920691273e-05 | True | 3.82355920691273e-05 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / baseline | 0.0 | 138911.19265567663 | 0.0 | 138911.19265567663 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.00015287611430838007 | True | 0.00015287611430838007 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / guided | 0.0 | 4365.643946387 | 0.0 | 4365.643946387 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.00015287611430838007 | True | 0.00015287611430838007 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 3 (Classical vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / vectorization | 0.0 | 0.010897929 | 0.0 | 0.010897929 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.00015287611430838007 | True | 0.00015287611430838007 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | PSO | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 100.0 | 6.386444750436982e-05 | 0.0 | large | Tier 3 (Classical vs. Classical) | 0.00015287611430838007 | True | 0.00015287611430838007 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / baseline | 0.0036945288 | 0.11154009640000001 | 0.0036945288 | 0.11154009640000001 | 93.0 | 0.773530465453452 | 0.535 | negligible | Tier 3 (Classical vs. Classical) | 0.8013875111546696 | False | 0.8013875111546696 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / guided | 0.0036945288 | 3.5000000000000003e-10 | 0.0036945288 | 3.5000000000000003e-10 | 100.0 | 0.00018063472080753515 | 0.0 | large | Tier 3 (Classical vs. Classical) | 0.0003081510528560053 | True | 0.0003081510528560053 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / thinking | 0.0036945288 | 8.10155e-06 | 0.0036945288 | 8.10155e-06 | 182.0 | 0.00033435257187782147 | 0.09 | large | Tier 3 (Classical vs. Classical) | 0.0005402627816400907 | True | 0.0005402627816400907 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / vectorization | 0.0036945288 | 0.0007107627 | 0.0036945288 | 0.0007107627 | 146.0 | 0.04531344230901011 | 0.27 | large | Tier 3 (Classical vs. Classical) | 0.056589112837066115 | False | 0.056589112837066115 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / baseline | 0.0036945288 | 138911.19265567663 | 0.0036945288 | 138911.19265567663 | 0.0 | 0.00018267179110955002 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003081510528560053 | True | 0.0003081510528560053 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / guided | 0.0036945288 | 4365.643946387 | 0.0036945288 | 4365.643946387 | 0.0 | 0.00018267179110955002 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003081510528560053 | True | 0.0003081510528560053 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / thinking | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 100.0 | 6.386444750436982e-05 | 0.0 | large | Tier 3 (Classical vs. Classical) | 0.00015287611430838007 | True | 0.00015287611430838007 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / vectorization | 0.0036945288 | 0.010897929 | 0.0036945288 | 0.010897929 | 32.0 | 0.18587673236587599 | 0.68 | medium | Tier 3 (Classical vs. Classical) | 0.2141970070396468 | False | 0.2141970070396468 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / baseline | 0.0 | 0.11154009640000001 | 0.0 | 0.11154009640000001 | 35.0 | 0.0017093888797144682 | 0.825 | large | Tier 3 (Classical vs. Classical) | 0.0025218182099084325 | True | 0.0025218182099084325 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 10.0 | 0.0007467880185761928 | 0.9 | large | Tier 3 (Classical vs. Classical) | 0.0011512684190681786 | True | 0.0011512684190681786 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / thinking | 0.0 | 8.10155e-06 | 0.0 | 8.10155e-06 | 15.0 | 0.00010539242746175711 | 0.925 | large | Tier 3 (Classical vs. Classical) | 0.0002450031755279808 | True | 0.0002450031755279808 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / vectorization | 0.0 | 0.0007107627 | 0.0 | 0.0007107627 | 0.0 | 8.194433744518873e-06 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.82355920691273e-05 | True | 3.82355920691273e-05 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / baseline | 0.0 | 138911.19265567663 | 0.0 | 138911.19265567663 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.00015287611430838007 | True | 0.00015287611430838007 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / guided | 0.0 | 4365.643946387 | 0.0 | 4365.643946387 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.00015287611430838007 | True | 0.00015287611430838007 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 3 (Classical vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / vectorization | 0.0 | 0.010897929 | 0.0 | 0.010897929 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.00015287611430838007 | True | 0.00015287611430838007 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / guided | 0.11154009640000001 | 3.5000000000000003e-10 | 0.11154009640000001 | 3.5000000000000003e-10 | 135.0 | 0.12389020558406098 | 0.325 | medium | Tier 3 (Classical vs. Classical) | 0.14751450199255156 | False | 0.14751450199255156 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / thinking | 0.11154009640000001 | 8.10155e-06 | 0.11154009640000001 | 8.10155e-06 | 242.5 | 0.2522092844913638 | 0.39375 | small | Tier 3 (Classical vs. Classical) | 0.286133209377174 | False | 0.286133209377174 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / vectorization | 0.11154009640000001 | 0.0007107627 | 0.11154009640000001 | 0.0007107627 | 220.0 | 0.5968972220191695 | 0.45 | negligible | Tier 3 (Classical vs. Classical) | 0.6326325162321592 | False | 0.6326325162321592 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / baseline | 0.11154009640000001 | 138911.19265567663 | 0.11154009640000001 | 138911.19265567663 | 0.0 | 1.0581248124442412e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.82355920691273e-05 | True | 3.82355920691273e-05 | True | Qwen2.5-Coder-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / guided | 0.11154009640000001 | 4365.643946387 | 0.11154009640000001 | 4365.643946387 | 3.0 | 1.9361543219577366e-05 | 0.985 | large | Tier 3 (Classical vs. Classical) | 5.7442810546480916e-05 | True | 5.7442810546480916e-05 | True | Qwen2.5-Coder-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / thinking | 0.11154009640000001 | 0.0 | 0.11154009640000001 | 0.0 | 165.0 | 0.0017093888797144682 | 0.175 | large | Tier 3 (Classical vs. Classical) | 0.0025218182099084325 | True | 0.0025218182099084325 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / vectorization | 0.11154009640000001 | 0.010897929 | 0.11154009640000001 | 0.010897929 | 107.0 | 0.773530465453452 | 0.465 | negligible | Tier 3 (Classical vs. Classical) | 0.8013875111546696 | False | 0.8013875111546696 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-14B / thinking | 3.5000000000000003e-10 | 8.10155e-06 | 3.5000000000000003e-10 | 8.10155e-06 | 35.0 | 0.004451282465972665 | 0.825 | large | Tier 3 (Classical vs. Classical) | 0.00629036495849295 | True | 0.00629036495849295 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-14B / vectorization | 3.5000000000000003e-10 | 0.0007107627 | 3.5000000000000003e-10 | 0.0007107627 | 0.0 | 1.195589582158822e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.82355920691273e-05 | True | 3.82355920691273e-05 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / baseline | 3.5000000000000003e-10 | 138911.19265567663 | 3.5000000000000003e-10 | 138911.19265567663 | 0.0 | 0.00018063472080753515 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003081510528560053 | True | 0.0003081510528560053 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / guided | 3.5000000000000003e-10 | 4365.643946387 | 3.5000000000000003e-10 | 4365.643946387 | 0.0 | 0.00018063472080753515 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003081510528560053 | True | 0.0003081510528560053 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / thinking | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 0.0 | 90.0 | 0.0007467880185761928 | 0.1 | large | Tier 3 (Classical vs. Classical) | 0.0011512684190681786 | True | 0.0011512684190681786 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / vectorization | 3.5000000000000003e-10 | 0.010897929 | 3.5000000000000003e-10 | 0.010897929 | 0.0 | 0.00018063472080753515 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0003081510528560053 | True | 0.0003081510528560053 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-14B / vectorization | 8.10155e-06 | 0.0007107627 | 8.10155e-06 | 0.0007107627 | 71.0 | 0.0005078360809385547 | 0.8225 | large | Tier 3 (Classical vs. Classical) | 0.0008005126481330837 | True | 0.0008005126481330837 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / baseline | 8.10155e-06 | 138911.19265567663 | 8.10155e-06 | 138911.19265567663 | 0.0 | 1.190254292173355e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.82355920691273e-05 | True | 3.82355920691273e-05 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / guided | 8.10155e-06 | 4365.643946387 | 8.10155e-06 | 4365.643946387 | 0.0 | 1.190254292173355e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.82355920691273e-05 | True | 3.82355920691273e-05 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / thinking | 8.10155e-06 | 0.0 | 8.10155e-06 | 0.0 | 185.0 | 0.00010539242746175711 | 0.075 | large | Tier 3 (Classical vs. Classical) | 0.0002450031755279808 | True | 0.0002450031755279808 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / vectorization | 8.10155e-06 | 0.010897929 | 8.10155e-06 | 0.010897929 | 6.0 | 3.867046032022654e-05 | 0.97 | large | Tier 3 (Classical vs. Classical) | 0.00010929493258927184 | True | 0.00010929493258927184 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / baseline | 0.0007107627 | 138911.19265567663 | 0.0007107627 | 138911.19265567663 | 0.0 | 1.2009441084406216e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.82355920691273e-05 | True | 3.82355920691273e-05 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / guided | 0.0007107627 | 4365.643946387 | 0.0007107627 | 4365.643946387 | 0.0 | 1.2009441084406216e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.82355920691273e-05 | True | 3.82355920691273e-05 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / thinking | 0.0007107627 | 0.0 | 0.0007107627 | 0.0 | 200.0 | 8.194433744518873e-06 | 0.0 | large | Tier 3 (Classical vs. Classical) | 3.82355920691273e-05 | True | 3.82355920691273e-05 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / vectorization | 0.0007107627 | 0.010897929 | 0.0007107627 | 0.010897929 | 20.0 | 0.00046958139251866075 | 0.9 | large | Tier 3 (Classical vs. Classical) | 0.0007423902093695411 | True | 0.0007423902093695411 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-7B / baseline | Qwen2.5-Coder-7B / guided | 138911.19265567663 | 4365.643946387 | 138911.19265567663 | 4365.643946387 | 89.0 | 0.003610514312329602 | 0.11 | large | Tier 3 (Classical vs. Classical) | 0.005133749829799637 | True | 0.005133749829799637 | True | Qwen2.5-Coder-7B / guided Wins |
