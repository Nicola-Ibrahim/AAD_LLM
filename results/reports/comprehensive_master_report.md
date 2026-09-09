# Comprehensive Empirical Evaluation & Statistical Analysis Report

## 1. Overview & Experimental Protocol
- **Benchmark Suite**: BBOB (Black-Box Optimization Benchmarking)
- **Statistical Protocols**: Kruskal-Wallis H-test (omnibus), Mann-Whitney U test (pairwise)
- **Multiplicity Correction**: Benjamini-Hochberg False Discovery Rate (FDR, $\alpha=0.05$)
- **Effect Size Metric**: Vargha-Delaney $\hat{A}_{12}$ non-parametric effect size

## 2. Omnibus Kruskal-Wallis Significance Summary
- **Total Experimental Conditions Evaluated**: 80
- **Statistically Significant omnibus Differences ($p < 0.05$)**: 72 / 80 (90.0%)

### Omnibus Differences by Problem Dimension
- **2D**: 18 / 20 conditions reject null hypothesis
- **3D**: 19 / 20 conditions reject null hypothesis
- **5D**: 18 / 20 conditions reject null hypothesis
- **10D**: 17 / 20 conditions reject null hypothesis

## 3. Pairwise Comparisons & FDR Correction
- **Total Pairwise Hypothesis Tests**: 8152
- **Significant Differences after FDR Correction ($\alpha=0.05$)**: 6525 / 8152 (80.0%)

### Comparison Tier Breakdown
- **Tier 3 (Classical vs. Classical)**: 6525 / 8152 pairs significant
