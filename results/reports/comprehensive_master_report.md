# Comprehensive Empirical Evaluation & Statistical Analysis Report

## 1. Overview & Experimental Protocol
- **Benchmark Suite**: BBOB (Black-Box Optimization Benchmarking)
- **Statistical Protocols**: Kruskal-Wallis H-test (omnibus), Mann-Whitney U test (pairwise)
- **Multiplicity Correction**: Benjamini-Hochberg False Discovery Rate (FDR, $\alpha=0.05$)
- **Effect Size Metric**: Vargha-Delaney $\hat{A}_{12}$ non-parametric effect size

## 2. Omnibus Kruskal-Wallis Significance Summary
- **Total Experimental Conditions Evaluated**: 40
- **Statistically Significant omnibus Differences ($p < 0.05$)**: 40 / 40 (100.0%)

### Omnibus Differences by Problem Dimension
- **2D**: 10 / 10 conditions reject null hypothesis
- **3D**: 10 / 10 conditions reject null hypothesis
- **5D**: 10 / 10 conditions reject null hypothesis
- **10D**: 10 / 10 conditions reject null hypothesis

## 3. Pairwise Comparisons & FDR Correction
- **Total Pairwise Hypothesis Tests**: 5623
- **Significant Differences after FDR Correction ($\alpha=0.05$)**: 4398 / 5623 (78.2%)

### Comparison Tier Breakdown
- **Tier 3 (Classical vs. Classical)**: 4398 / 5623 pairs significant
