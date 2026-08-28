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
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 138.75597871512596 | 7.578689658782385e-25 | Yes | 11 |
| 2 | 0.0 | 1 | Sphere (f1) | Separable | 180.08880741708222 | 2.245603257812997e-33 | Yes | 11 |
| 2 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 125.41407537482395 | 4.016734971229473e-22 | Yes | 11 |
| 2 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 125.10727418277989 | 4.637772078178563e-22 | Yes | 11 |
| 2 | 0.0 | 11 | Discus (f11) | High Conditioning | 122.99655061618353 | 1.2461787569035066e-21 | Yes | 11 |
| 2 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 142.10183121458115 | 1.5625620439252825e-25 | Yes | 11 |
| 2 | 0.05 | 1 | Sphere (f1) | Separable | 140.2820617355854 | 3.689190370601305e-25 | Yes | 11 |
| 2 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 93.2640777357336 | 1.203727288974028e-15 | Yes | 11 |
| 2 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 112.07569840228354 | 2.0339108436481488e-19 | Yes | 11 |
| 2 | 0.05 | 11 | Discus (f11) | High Conditioning | 103.25051599215567 | 1.2160886111307055e-17 | Yes | 11 |
| 5 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 131.40957280958838 | 2.4087276596434752e-23 | Yes | 11 |
| 5 | 0.0 | 1 | Sphere (f1) | Separable | 178.9043671775257 | 3.955472576074098e-33 | Yes | 11 |
| 5 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 128.1743212010012 | 1.1007718541630723e-22 | Yes | 11 |
| 5 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 77.90103690827836 | 1.2929108943470678e-12 | Yes | 11 |
| 5 | 0.0 | 11 | Discus (f11) | High Conditioning | 137.6328756507161 | 1.2869596001748428e-24 | Yes | 11 |
| 5 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 161.0414304884645 | 1.9749531412628405e-29 | Yes | 11 |
| 5 | 0.05 | 1 | Sphere (f1) | Separable | 176.87006922096865 | 1.045448169429815e-32 | Yes | 11 |
| 5 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 121.00297872340434 | 8.32727219238108e-22 | Yes | 10 |
| 5 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 87.56304702286825 | 5.0129746982106495e-15 | Yes | 10 |
| 5 | 0.05 | 11 | Discus (f11) | High Conditioning | 124.17982225608183 | 7.16128344941404e-22 | Yes | 11 |
| 3 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 164.82002585922686 | 3.2721114344259284e-30 | Yes | 11 |
| 3 | 0.0 | 1 | Sphere (f1) | Separable | 158.5871872483313 | 6.340930163522734e-29 | Yes | 11 |
| 3 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 112.01034650336902 | 2.096661705707855e-19 | Yes | 11 |
| 3 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 86.1837004213886 | 3.04823899586335e-14 | Yes | 11 |
| 3 | 0.0 | 11 | Discus (f11) | High Conditioning | 151.15982270105633 | 2.15160080429215e-27 | Yes | 11 |
| 3 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 120.21981338425053 | 4.5661181642426846e-21 | Yes | 11 |
| 3 | 0.05 | 1 | Sphere (f1) | Separable | 144.54772768409774 | 4.9197031038115413e-26 | Yes | 11 |
| 3 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 110.92584844374205 | 3.4708553642508e-19 | Yes | 11 |
| 3 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 76.11970343503312 | 2.879332873578431e-12 | Yes | 11 |
| 3 | 0.05 | 11 | Discus (f11) | High Conditioning | 145.34125373900056 | 3.3806688930899404e-26 | Yes | 11 |

## 3. Pairwise Post-Hoc Tests (Mann-Whitney U with FDR Correction)

- **Total Pairwise Comparisons**: 1630
- **Statistically Significant After FDR**: 1258 / 1630

### Pairwise Statistical Comparisons

| Dim | Noise Std | Problem ID | Problem Name | Function Class | Solver 1 | Solver 2 | Median 1 | Median 2 | Solver 1 Med | Solver 2 Med | U-Stat | p-value | A12 | A12 Magnitude | Comparison Tier | p-adjusted | Significant (FDR) | p-value-adj | FDR_Sig | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | DE | 0.0 | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 6.386444750436982e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 0.0001334518130318585 | True | 0.0001334518130318585 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | PSO | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.0 | 0.5 | negligible | Tier 3 (Classical vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / baseline | 0.0 | 4.5083e-06 | 0.0 | 4.5083e-06 | 20.0 | 0.00022493124248306628 | 0.9 | large | Tier 3 (Classical vs. Classical) | 0.0003887372386200361 | True | 0.0003887372386200361 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 10.0 | 0.0007467880185761928 | 0.9 | large | Tier 3 (Classical vs. Classical) | 0.0011896850711773212 | True | 0.0011896850711773212 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / thinking | 0.0 | 8.31715e-06 | 0.0 | 8.31715e-06 | 10.0 | 4.710704754839632e-05 | 0.95 | large | Tier 3 (Classical vs. Classical) | 0.0001069400542151917 | True | 0.0001069400542151917 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / vectorization | 0.0 | 0.0006921659999999999 | 0.0 | 0.0006921659999999999 | 0.0 | 8.194433744518873e-06 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.0033812972507668e-05 | True | 3.0033812972507668e-05 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / baseline | 0.0 | 794.1960457084 | 0.0 | 794.1960457084 | 0.0 | 8.194433744518873e-06 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.0033812972507668e-05 | True | 3.0033812972507668e-05 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / guided | 0.0 | 0.00358113175 | 0.0 | 0.00358113175 | 0.0 | 8.194433744518873e-06 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.0033812972507668e-05 | True | 3.0033812972507668e-05 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | nan | 0.5 | negligible | Tier 3 (Classical vs. Classical) | nan | False | nan | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / vectorization | 0.0 | 3.2616000000000002e-06 | 0.0 | 3.2616000000000002e-06 | 0.0 | 8.194433744518873e-06 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.0033812972507668e-05 | True | 3.0033812972507668e-05 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | PSO | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 100.0 | 6.386444750436982e-05 | 0.0 | large | Tier 3 (Classical vs. Classical) | 0.0001334518130318585 | True | 0.0001334518130318585 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / baseline | 0.0036945288 | 4.5083e-06 | 0.0036945288 | 4.5083e-06 | 128.0 | 0.2258238554124541 | 0.36 | medium | Tier 3 (Classical vs. Classical) | 0.2566035193210725 | False | 0.2566035193210725 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / guided | 0.0036945288 | 3.5000000000000003e-10 | 0.0036945288 | 3.5000000000000003e-10 | 100.0 | 0.00018063472080753515 | 0.0 | large | Tier 3 (Classical vs. Classical) | 0.0003180940604927121 | True | 0.0003180940604927121 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / thinking | 0.0036945288 | 8.31715e-06 | 0.0036945288 | 8.31715e-06 | 193.0 | 4.6939924119472954e-05 | 0.035 | large | Tier 3 (Classical vs. Classical) | 0.0001069400542151917 | True | 0.0001069400542151917 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / vectorization | 0.0036945288 | 0.0006921659999999999 | 0.0036945288 | 0.0006921659999999999 | 168.0 | 0.0029818378302928876 | 0.16 | large | Tier 3 (Classical vs. Classical) | 0.0043815315698093665 | True | 0.0043815315698093665 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / baseline | 0.0036945288 | 794.1960457084 | 0.0036945288 | 794.1960457084 | 0.0 | 1.2009441084406216e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.076941195033376e-05 | True | 3.076941195033376e-05 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / guided | 0.0036945288 | 0.00358113175 | 0.0036945288 | 0.00358113175 | 108.0 | 0.7414332021716763 | 0.46 | negligible | Tier 3 (Classical vs. Classical) | 0.7731471304564013 | False | 0.7731471304564013 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / thinking | 0.0036945288 | 0.0 | 0.0036945288 | 0.0 | 200.0 | 1.8213904098436073e-07 | 0.0 | large | Tier 3 (Classical vs. Classical) | 1.1913077924546196e-06 | True | 1.1913077924546196e-06 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / vectorization | 0.0036945288 | 3.2616000000000002e-06 | 0.0036945288 | 3.2616000000000002e-06 | 138.0 | 0.09898793180102639 | 0.31 | medium | Tier 3 (Classical vs. Classical) | 0.11921525618851156 | False | 0.11921525618851156 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / baseline | 0.0 | 4.5083e-06 | 0.0 | 4.5083e-06 | 20.0 | 0.00022493124248306628 | 0.9 | large | Tier 3 (Classical vs. Classical) | 0.0003887372386200361 | True | 0.0003887372386200361 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 10.0 | 0.0007467880185761928 | 0.9 | large | Tier 3 (Classical vs. Classical) | 0.0011896850711773212 | True | 0.0011896850711773212 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / thinking | 0.0 | 8.31715e-06 | 0.0 | 8.31715e-06 | 10.0 | 4.710704754839632e-05 | 0.95 | large | Tier 3 (Classical vs. Classical) | 0.0001069400542151917 | True | 0.0001069400542151917 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / vectorization | 0.0 | 0.0006921659999999999 | 0.0 | 0.0006921659999999999 | 0.0 | 8.194433744518873e-06 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.0033812972507668e-05 | True | 3.0033812972507668e-05 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / baseline | 0.0 | 794.1960457084 | 0.0 | 794.1960457084 | 0.0 | 8.194433744518873e-06 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.0033812972507668e-05 | True | 3.0033812972507668e-05 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / guided | 0.0 | 0.00358113175 | 0.0 | 0.00358113175 | 0.0 | 8.194433744518873e-06 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.0033812972507668e-05 | True | 3.0033812972507668e-05 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | nan | 0.5 | negligible | Tier 3 (Classical vs. Classical) | nan | False | nan | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / vectorization | 0.0 | 3.2616000000000002e-06 | 0.0 | 3.2616000000000002e-06 | 0.0 | 8.194433744518873e-06 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.0033812972507668e-05 | True | 3.0033812972507668e-05 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / guided | 4.5083e-06 | 3.5000000000000003e-10 | 4.5083e-06 | 3.5000000000000003e-10 | 158.0 | 0.011089878518479835 | 0.21 | large | Tier 3 (Classical vs. Classical) | 0.015329565752778397 | True | 0.015329565752778397 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / thinking | 4.5083e-06 | 8.31715e-06 | 4.5083e-06 | 8.31715e-06 | 229.0 | 0.43997667783325367 | 0.4275 | small | Tier 3 (Classical vs. Classical) | 0.4802730492765978 | False | 0.4802730492765978 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / vectorization | 4.5083e-06 | 0.0006921659999999999 | 4.5083e-06 | 0.0006921659999999999 | 169.0 | 0.4091360434734501 | 0.5775 | small | Tier 3 (Classical vs. Classical) | 0.44751862267082343 | False | 0.44751862267082343 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / baseline | 4.5083e-06 | 794.1960457084 | 4.5083e-06 | 794.1960457084 | 0.0 | 6.700376361164958e-08 | 1.0 | large | Tier 3 (Classical vs. Classical) | 5.910348508773477e-07 | True | 5.910348508773477e-07 | True | Qwen2.5-Coder-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / guided | 4.5083e-06 | 0.00358113175 | 4.5083e-06 | 0.00358113175 | 161.0 | 0.2974500472539555 | 0.5975 | small | Tier 3 (Classical vs. Classical) | 0.3330750333419599 | False | 0.3330750333419599 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / thinking | 4.5083e-06 | 0.0 | 4.5083e-06 | 0.0 | 360.0 | 1.104894143345323e-06 | 0.1 | large | Tier 3 (Classical vs. Classical) | 6.3491952737236595e-06 | True | 6.3491952737236595e-06 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / vectorization | 4.5083e-06 | 3.2616000000000002e-06 | 4.5083e-06 | 3.2616000000000002e-06 | 179.0 | 0.5790402879610703 | 0.5525 | negligible | Tier 3 (Classical vs. Classical) | 0.6194653080647354 | False | 0.6194653080647354 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-14B / thinking | 3.5000000000000003e-10 | 8.31715e-06 | 3.5000000000000003e-10 | 8.31715e-06 | 40.0 | 0.008740784692067904 | 0.8 | large | Tier 3 (Classical vs. Classical) | 0.012155507838839463 | True | 0.012155507838839463 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-14B / vectorization | 3.5000000000000003e-10 | 0.0006921659999999999 | 3.5000000000000003e-10 | 0.0006921659999999999 | 0.0 | 1.195589582158822e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.076941195033376e-05 | True | 3.076941195033376e-05 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / baseline | 3.5000000000000003e-10 | 794.1960457084 | 3.5000000000000003e-10 | 794.1960457084 | 0.0 | 1.195589582158822e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.076941195033376e-05 | True | 3.076941195033376e-05 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / guided | 3.5000000000000003e-10 | 0.00358113175 | 3.5000000000000003e-10 | 0.00358113175 | 0.0 | 1.195589582158822e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.076941195033376e-05 | True | 3.076941195033376e-05 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / thinking | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 0.0 | 180.0 | 7.000010305297568e-06 | 0.1 | large | Tier 3 (Classical vs. Classical) | 3.0033812972507668e-05 | True | 3.0033812972507668e-05 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / vectorization | 3.5000000000000003e-10 | 3.2616000000000002e-06 | 3.5000000000000003e-10 | 3.2616000000000002e-06 | 0.0 | 1.195589582158822e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 3.076941195033376e-05 | True | 3.076941195033376e-05 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-14B / vectorization | 8.31715e-06 | 0.0006921659999999999 | 8.31715e-06 | 0.0006921659999999999 | 76.0 | 0.0008347739570997606 | 0.81 | large | Tier 3 (Classical vs. Classical) | 0.001322191117167305 | True | 0.001322191117167305 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / baseline | 8.31715e-06 | 794.1960457084 | 8.31715e-06 | 794.1960457084 | 0.0 | 6.776473833976438e-08 | 1.0 | large | Tier 3 (Classical vs. Classical) | 5.910348508773477e-07 | True | 5.910348508773477e-07 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / guided | 8.31715e-06 | 0.00358113175 | 8.31715e-06 | 0.00358113175 | 18.0 | 9.105234362245009e-07 | 0.955 | large | Tier 3 (Classical vs. Classical) | 5.320570444921013e-06 | True | 5.320570444921013e-06 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / thinking | 8.31715e-06 | 0.0 | 8.31715e-06 | 0.0 | 380.0 | 1.0518688476277236e-07 | 0.05 | large | Tier 3 (Classical vs. Classical) | 8.004165863804443e-07 | True | 8.004165863804443e-07 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / vectorization | 8.31715e-06 | 3.2616000000000002e-06 | 8.31715e-06 | 3.2616000000000002e-06 | 137.0 | 0.09087707385138948 | 0.6575 | medium | Tier 3 (Classical vs. Classical) | 0.10969333220321506 | False | 0.10969333220321506 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / baseline | 0.0006921659999999999 | 794.1960457084 | 0.0006921659999999999 | 794.1960457084 | 0.0 | 6.795615128173357e-08 | 1.0 | large | Tier 3 (Classical vs. Classical) | 5.910348508773477e-07 | True | 5.910348508773477e-07 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / guided | 0.0006921659999999999 | 0.00358113175 | 0.0006921659999999999 | 0.00358113175 | 76.0 | 0.0008357168217272525 | 0.81 | large | Tier 3 (Classical vs. Classical) | 0.001322191117167305 | True | 0.001322191117167305 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / thinking | 0.0006921659999999999 | 0.0 | 0.0006921659999999999 | 0.0 | 400.0 | 8.006545033944715e-09 | 0.0 | large | Tier 3 (Classical vs. Classical) | 2.525986462670009e-07 | True | 2.525986462670009e-07 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / vectorization | 0.0006921659999999999 | 3.2616000000000002e-06 | 0.0006921659999999999 | 3.2616000000000002e-06 | 239.0 | 0.29767675447218045 | 0.4025 | small | Tier 3 (Classical vs. Classical) | 0.3330750333419599 | False | 0.3330750333419599 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-7B / baseline | Qwen2.5-Coder-7B / guided | 794.1960457084 | 0.00358113175 | 794.1960457084 | 0.00358113175 | 400.0 | 6.795615128173357e-08 | 0.0 | large | Tier 3 (Classical vs. Classical) | 5.910348508773477e-07 | True | 5.910348508773477e-07 | True | Qwen2.5-Coder-7B / guided Wins |
