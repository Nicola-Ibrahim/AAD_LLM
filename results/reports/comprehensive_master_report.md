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
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 162.05117715677028 | 1.2218380937474248e-29 | Yes | 11 |
| 2 | 0.0 | 1 | Sphere (f1) | Separable | 210.88649460838562 | 8.611396673872168e-40 | Yes | 11 |
| 2 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 176.37593595259017 | 1.3237268833317628e-32 | Yes | 11 |
| 2 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 131.75184930919045 | 2.0507439033750425e-23 | Yes | 11 |
| 2 | 0.0 | 11 | Discus (f11) | High Conditioning | 143.68020974806893 | 7.413270556386705e-26 | Yes | 11 |
| 2 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 170.6145471189543 | 2.0694518278484415e-31 | Yes | 11 |
| 2 | 0.05 | 1 | Sphere (f1) | Separable | 166.389169910752 | 1.5500637542115046e-30 | Yes | 11 |
| 2 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 112.04968600531762 | 2.0586600667233736e-19 | Yes | 11 |
| 2 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 140.61479250971124 | 3.153078115028721e-25 | Yes | 11 |
| 2 | 0.05 | 11 | Discus (f11) | High Conditioning | 117.10384414229334 | 1.9558975381558425e-20 | Yes | 11 |
| 5 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 157.17098652054048 | 1.2425003470604503e-28 | Yes | 11 |
| 5 | 0.0 | 1 | Sphere (f1) | Separable | 203.54767953579983 | 2.9359722065859856e-38 | Yes | 11 |
| 5 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 176.4813010549094 | 1.258763337824404e-32 | Yes | 11 |
| 5 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 95.9285580979339 | 3.5465019754782274e-16 | Yes | 11 |
| 5 | 0.0 | 11 | Discus (f11) | High Conditioning | 172.2478716140351 | 9.495921027418e-32 | Yes | 11 |
| 5 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 188.1030344524461 | 4.851348083662532e-35 | Yes | 11 |
| 5 | 0.05 | 1 | Sphere (f1) | Separable | 208.14956294092647 | 3.2130569094152717e-39 | Yes | 11 |
| 5 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 162.72131343283593 | 2.019176263047816e-30 | Yes | 10 |
| 5 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 105.40650651026031 | 1.262689160326647e-18 | Yes | 10 |
| 5 | 0.05 | 11 | Discus (f11) | High Conditioning | 151.3223498291957 | 1.9920987448778234e-27 | Yes | 11 |
| 3 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | 190.40298316406427 | 1.6118288800448087e-35 | Yes | 11 |
| 3 | 0.0 | 1 | Sphere (f1) | Separable | 189.54977694509083 | 2.4258965205854095e-35 | Yes | 11 |
| 3 | 0.0 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 140.20487504901286 | 3.826043103232731e-25 | Yes | 11 |
| 3 | 0.0 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 132.6482399782004 | 1.345421161430353e-23 | Yes | 11 |
| 3 | 0.0 | 11 | Discus (f11) | High Conditioning | 177.23609560771283 | 8.777497762822536e-33 | Yes | 11 |
| 3 | 0.05 | 8 | Rosenbrock (f8) | Low Conditioning | 140.58653237232807 | 3.1954150878406292e-25 | Yes | 11 |
| 3 | 0.05 | 1 | Sphere (f1) | Separable | 167.3500013582951 | 9.808161333606595e-31 | Yes | 11 |
| 3 | 0.05 | 15 | Rastrigin Multi-Modal (f15) | Multi-Modal (Global) | 164.47506263475074 | 3.856039725866169e-30 | Yes | 11 |
| 3 | 0.05 | 21 | Gallagher 101 Peaks (f21) | Multi-Modal (Weak) | 61.40796316835979 | 1.9605194339729236e-09 | Yes | 11 |
| 3 | 0.05 | 11 | Discus (f11) | High Conditioning | 155.18749651255152 | 3.185906051603027e-28 | Yes | 11 |

## 3. Pairwise Post-Hoc Tests (Mann-Whitney U with FDR Correction)

- **Total Pairwise Comparisons**: 1630
- **Statistically Significant After FDR**: 1277 / 1630

### Pairwise Statistical Comparisons

| Dim | Noise Std | Problem ID | Problem Name | Function Class | Solver 1 | Solver 2 | Median 1 | Median 2 | Solver 1 Med | Solver 2 Med | U-Stat | p-value | A12 | A12 Magnitude | Comparison Tier | p-adjusted | Significant (FDR) | p-value-adj | FDR_Sig | Outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | DE | 0.0 | 0.002946151 | 0.0 | 0.002946151 | 0.0 | 8.006545033944715e-09 | 1.0 | large | Tier 3 (Classical vs. Classical) | 7.259565692788979e-08 | True | 7.259565692788979e-08 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | PSO | 0.0 | 0.0 | 0.0 | 0.0 | 190.0 | 0.34211225261696354 | 0.525 | negligible | Tier 3 (Classical vs. Classical) | 0.3818763314974772 | False | 0.3818763314974772 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / baseline | 0.0 | 4.5083e-06 | 0.0 | 4.5083e-06 | 40.0 | 1.104894143345323e-06 | 0.9 | large | Tier 3 (Classical vs. Classical) | 2.518599992485196e-06 | True | 2.518599992485196e-06 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 20.0 | 7.000010305297568e-06 | 0.9 | large | Tier 3 (Classical vs. Classical) | 1.4008651942660856e-05 | True | 1.4008651942660856e-05 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / thinking | 0.0 | 8.31715e-06 | 0.0 | 8.31715e-06 | 20.0 | 1.0518688476277236e-07 | 0.95 | large | Tier 3 (Classical vs. Classical) | 3.085349036833311e-07 | True | 3.085349036833311e-07 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-14B / vectorization | 0.0 | 0.0006921659999999999 | 0.0 | 0.0006921659999999999 | 0.0 | 8.006545033944715e-09 | 1.0 | large | Tier 3 (Classical vs. Classical) | 7.259565692788979e-08 | True | 7.259565692788979e-08 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / baseline | 0.0 | 794.1960457084 | 0.0 | 794.1960457084 | 0.0 | 8.006545033944715e-09 | 1.0 | large | Tier 3 (Classical vs. Classical) | 7.259565692788979e-08 | True | 7.259565692788979e-08 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / guided | 0.0 | 0.00358113175 | 0.0 | 0.00358113175 | 0.0 | 8.006545033944715e-09 | 1.0 | large | Tier 3 (Classical vs. Classical) | 7.259565692788979e-08 | True | 7.259565692788979e-08 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 200.0 | 1.0 | 0.5 | negligible | Tier 3 (Classical vs. Classical) | 1.0 | False | 1.0 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | CMA-ES | Qwen2.5-Coder-7B / vectorization | 0.0 | 3.2616000000000002e-06 | 0.0 | 3.2616000000000002e-06 | 0.0 | 8.006545033944715e-09 | 1.0 | large | Tier 3 (Classical vs. Classical) | 7.259565692788979e-08 | True | 7.259565692788979e-08 | True | CMA-ES Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | PSO | 0.002946151 | 0.0 | 0.002946151 | 0.0 | 380.0 | 2.7769221156100106e-07 | 0.05 | large | Tier 3 (Classical vs. Classical) | 7.042100927554761e-07 | True | 7.042100927554761e-07 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / baseline | 0.002946151 | 4.5083e-06 | 0.002946151 | 4.5083e-06 | 238.0 | 0.31017520847080804 | 0.405 | small | Tier 3 (Classical vs. Classical) | 0.34983624972072375 | False | 0.34983624972072375 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / guided | 0.002946151 | 3.5000000000000003e-10 | 0.002946151 | 3.5000000000000003e-10 | 200.0 | 1.195589582158822e-05 | 0.0 | large | Tier 3 (Classical vs. Classical) | 2.209900553286994e-05 | True | 2.209900553286994e-05 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / thinking | 0.002946151 | 8.31715e-06 | 0.002946151 | 8.31715e-06 | 369.0 | 5.155273845815383e-06 | 0.0775 | large | Tier 3 (Classical vs. Classical) | 1.0653188096771107e-05 | True | 1.0653188096771107e-05 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-14B / vectorization | 0.002946151 | 0.0006921659999999999 | 0.002946151 | 0.0006921659999999999 | 295.0 | 0.010581211443165647 | 0.2625 | large | Tier 3 (Classical vs. Classical) | 0.01449224149557624 | True | 0.01449224149557624 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / baseline | 0.002946151 | 794.1960457084 | 0.002946151 | 794.1960457084 | 0.0 | 6.795615128173357e-08 | 1.0 | large | Tier 3 (Classical vs. Classical) | 2.2508741536786448e-07 | True | 2.2508741536786448e-07 | True | DE Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / guided | 0.002946151 | 0.00358113175 | 0.002946151 | 0.00358113175 | 173.0 | 0.4734806277722057 | 0.5675 | small | Tier 3 (Classical vs. Classical) | 0.516437539566055 | False | 0.516437539566055 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / thinking | 0.002946151 | 0.0 | 0.002946151 | 0.0 | 400.0 | 8.006545033944715e-09 | 0.0 | large | Tier 3 (Classical vs. Classical) | 7.259565692788979e-08 | True | 7.259565692788979e-08 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | DE | Qwen2.5-Coder-7B / vectorization | 0.002946151 | 3.2616000000000002e-06 | 0.002946151 | 3.2616000000000002e-06 | 263.0 | 0.09090738325062646 | 0.3425 | medium | Tier 3 (Classical vs. Classical) | 0.11093434813215546 | False | 0.11093434813215546 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / baseline | 0.0 | 4.5083e-06 | 0.0 | 4.5083e-06 | 56.0 | 1.6131899650811803e-05 | 0.86 | large | Tier 3 (Classical vs. Classical) | 2.9026688617813257e-05 | True | 2.9026688617813257e-05 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / guided | 0.0 | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 29.0 | 0.00013024912726185536 | 0.855 | large | Tier 3 (Classical vs. Classical) | 0.00021883471381572593 | True | 0.00021883471381572593 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / thinking | 0.0 | 8.31715e-06 | 0.0 | 8.31715e-06 | 39.0 | 2.6783409305725734e-06 | 0.9025 | large | Tier 3 (Classical vs. Classical) | 5.757546132873227e-06 | True | 5.757546132873227e-06 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-14B / vectorization | 0.0 | 0.0006921659999999999 | 0.0 | 0.0006921659999999999 | 20.0 | 2.7769221156100106e-07 | 0.95 | large | Tier 3 (Classical vs. Classical) | 7.042100927554761e-07 | True | 7.042100927554761e-07 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / baseline | 0.0 | 794.1960457084 | 0.0 | 794.1960457084 | 0.0 | 1.1266570353724972e-08 | 1.0 | large | Tier 3 (Classical vs. Classical) | 9.52377275213314e-08 | True | 9.52377275213314e-08 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / guided | 0.0 | 0.00358113175 | 0.0 | 0.00358113175 | 20.0 | 2.7769221156100106e-07 | 0.95 | large | Tier 3 (Classical vs. Classical) | 7.042100927554761e-07 | True | 7.042100927554761e-07 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / thinking | 0.0 | 0.0 | 0.0 | 0.0 | 210.0 | 0.34211225261696354 | 0.475 | negligible | Tier 3 (Classical vs. Classical) | 0.3818763314974772 | False | 0.3818763314974772 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | PSO | Qwen2.5-Coder-7B / vectorization | 0.0 | 3.2616000000000002e-06 | 0.0 | 3.2616000000000002e-06 | 20.0 | 2.7769221156100106e-07 | 0.95 | large | Tier 3 (Classical vs. Classical) | 7.042100927554761e-07 | True | 7.042100927554761e-07 | True | PSO Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / guided | 4.5083e-06 | 3.5000000000000003e-10 | 4.5083e-06 | 3.5000000000000003e-10 | 158.0 | 0.011089878518479835 | 0.21 | large | Tier 3 (Classical vs. Classical) | 0.015176115375626284 | True | 0.015176115375626284 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / thinking | 4.5083e-06 | 8.31715e-06 | 4.5083e-06 | 8.31715e-06 | 229.0 | 0.43997667783325367 | 0.4275 | small | Tier 3 (Classical vs. Classical) | 0.48366265116978374 | False | 0.48366265116978374 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-14B / vectorization | 4.5083e-06 | 0.0006921659999999999 | 4.5083e-06 | 0.0006921659999999999 | 169.0 | 0.4091360434734501 | 0.5775 | small | Tier 3 (Classical vs. Classical) | 0.45202709227869947 | False | 0.45202709227869947 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / baseline | 4.5083e-06 | 794.1960457084 | 4.5083e-06 | 794.1960457084 | 0.0 | 6.700376361164958e-08 | 1.0 | large | Tier 3 (Classical vs. Classical) | 2.2508741536786448e-07 | True | 2.2508741536786448e-07 | True | Qwen2.5-Coder-14B / baseline Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / guided | 4.5083e-06 | 0.00358113175 | 4.5083e-06 | 0.00358113175 | 161.0 | 0.2974500472539555 | 0.5975 | small | Tier 3 (Classical vs. Classical) | 0.33691030160972724 | False | 0.33691030160972724 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / thinking | 4.5083e-06 | 0.0 | 4.5083e-06 | 0.0 | 360.0 | 1.104894143345323e-06 | 0.1 | large | Tier 3 (Classical vs. Classical) | 2.518599992485196e-06 | True | 2.518599992485196e-06 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / baseline | Qwen2.5-Coder-7B / vectorization | 4.5083e-06 | 3.2616000000000002e-06 | 4.5083e-06 | 3.2616000000000002e-06 | 179.0 | 0.5790402879610703 | 0.5525 | negligible | Tier 3 (Classical vs. Classical) | 0.6215491979899584 | False | 0.6215491979899584 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-14B / thinking | 3.5000000000000003e-10 | 8.31715e-06 | 3.5000000000000003e-10 | 8.31715e-06 | 40.0 | 0.008740784692067904 | 0.8 | large | Tier 3 (Classical vs. Classical) | 0.012125037226689067 | True | 0.012125037226689067 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-14B / vectorization | 3.5000000000000003e-10 | 0.0006921659999999999 | 3.5000000000000003e-10 | 0.0006921659999999999 | 0.0 | 1.195589582158822e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 2.209900553286994e-05 | True | 2.209900553286994e-05 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / baseline | 3.5000000000000003e-10 | 794.1960457084 | 3.5000000000000003e-10 | 794.1960457084 | 0.0 | 1.195589582158822e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 2.209900553286994e-05 | True | 2.209900553286994e-05 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / guided | 3.5000000000000003e-10 | 0.00358113175 | 3.5000000000000003e-10 | 0.00358113175 | 0.0 | 1.195589582158822e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 2.209900553286994e-05 | True | 2.209900553286994e-05 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / thinking | 3.5000000000000003e-10 | 0.0 | 3.5000000000000003e-10 | 0.0 | 180.0 | 7.000010305297568e-06 | 0.1 | large | Tier 3 (Classical vs. Classical) | 1.4008651942660856e-05 | True | 1.4008651942660856e-05 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / guided | Qwen2.5-Coder-7B / vectorization | 3.5000000000000003e-10 | 3.2616000000000002e-06 | 3.5000000000000003e-10 | 3.2616000000000002e-06 | 0.0 | 1.195589582158822e-05 | 1.0 | large | Tier 3 (Classical vs. Classical) | 2.209900553286994e-05 | True | 2.209900553286994e-05 | True | Qwen2.5-Coder-14B / guided Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-14B / vectorization | 8.31715e-06 | 0.0006921659999999999 | 8.31715e-06 | 0.0006921659999999999 | 76.0 | 0.0008347739570997606 | 0.81 | large | Tier 3 (Classical vs. Classical) | 0.001293010869078485 | True | 0.001293010869078485 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / baseline | 8.31715e-06 | 794.1960457084 | 8.31715e-06 | 794.1960457084 | 0.0 | 6.776473833976438e-08 | 1.0 | large | Tier 3 (Classical vs. Classical) | 2.2508741536786448e-07 | True | 2.2508741536786448e-07 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / guided | 8.31715e-06 | 0.00358113175 | 8.31715e-06 | 0.00358113175 | 18.0 | 9.105234362245009e-07 | 0.955 | large | Tier 3 (Classical vs. Classical) | 2.1202001965457174e-06 | True | 2.1202001965457174e-06 | True | Qwen2.5-Coder-14B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / thinking | 8.31715e-06 | 0.0 | 8.31715e-06 | 0.0 | 380.0 | 1.0518688476277236e-07 | 0.05 | large | Tier 3 (Classical vs. Classical) | 3.085349036833311e-07 | True | 3.085349036833311e-07 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / thinking | Qwen2.5-Coder-7B / vectorization | 8.31715e-06 | 3.2616000000000002e-06 | 8.31715e-06 | 3.2616000000000002e-06 | 137.0 | 0.09087707385138948 | 0.6575 | medium | Tier 3 (Classical vs. Classical) | 0.11093434813215546 | False | 0.11093434813215546 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / baseline | 0.0006921659999999999 | 794.1960457084 | 0.0006921659999999999 | 794.1960457084 | 0.0 | 6.795615128173357e-08 | 1.0 | large | Tier 3 (Classical vs. Classical) | 2.2508741536786448e-07 | True | 2.2508741536786448e-07 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / guided | 0.0006921659999999999 | 0.00358113175 | 0.0006921659999999999 | 0.00358113175 | 76.0 | 0.0008357168217272525 | 0.81 | large | Tier 3 (Classical vs. Classical) | 0.001293010869078485 | True | 0.001293010869078485 | True | Qwen2.5-Coder-14B / vectorization Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / thinking | 0.0006921659999999999 | 0.0 | 0.0006921659999999999 | 0.0 | 400.0 | 8.006545033944715e-09 | 0.0 | large | Tier 3 (Classical vs. Classical) | 7.259565692788979e-08 | True | 7.259565692788979e-08 | True | Qwen2.5-Coder-7B / thinking Wins |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-14B / vectorization | Qwen2.5-Coder-7B / vectorization | 0.0006921659999999999 | 3.2616000000000002e-06 | 0.0006921659999999999 | 3.2616000000000002e-06 | 239.0 | 0.29767675447218045 | 0.4025 | small | Tier 3 (Classical vs. Classical) | 0.33691030160972724 | False | 0.33691030160972724 | False | Tie |
| 2 | 0.0 | 8 | Rosenbrock (f8) | Low Conditioning | Qwen2.5-Coder-7B / baseline | Qwen2.5-Coder-7B / guided | 794.1960457084 | 0.00358113175 | 794.1960457084 | 0.00358113175 | 400.0 | 6.795615128173357e-08 | 0.0 | large | Tier 3 (Classical vs. Classical) | 2.2508741536786448e-07 | True | 2.2508741536786448e-07 | True | Qwen2.5-Coder-7B / guided Wins |
