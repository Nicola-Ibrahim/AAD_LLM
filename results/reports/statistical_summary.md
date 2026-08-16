# 📊 Comprehensive Benchmark & Statistical Analysis Report

> **Master Roll-Up Report** evaluating **LLaMEA Champion** against classical baseline optimizers (**CMA-ES**, **DE**, **PSO**).

## 🏆 1. Executive Summary & Win-Loss Metrics

- **Total Pairwise Hypothesis Tests ($N$):** `85`
- **🟢 LLaMEA Statistically Significant Wins ($p < 0.05, \hat{A}_{12} < 0.5$):** **`30`** (35.3%)
- **🔴 Baseline Statistically Significant Wins ($p < 0.05, \hat{A}_{12} > 0.5$):** **`14`** (16.5%)
- **⚪ Non-Significant Differences & Exact Ties:** **`41`** (48.2%)

---
## 📁 2. Direct Links to Per-Condition Statistical Reports

| Dimension | Noise Level | Condition Label | Dedicated Report Folder |
| :---: | :---: | :--- | :--- |
| **2D** | `0.0` | Clean (std = 0.0) | [`results/reports/2D/std_0.0/statistical_summary.md`](2D/std_0.0/statistical_summary.md) |
| **2D** | `0.05` | Noisy (std = 0.05) | [`results/reports/2D/std_0.05/statistical_summary.md`](2D/std_0.05/statistical_summary.md) |
| **3D** | `0.0` | Clean (std = 0.0) | [`results/reports/3D/std_0.0/statistical_summary.md`](3D/std_0.0/statistical_summary.md) |
| **3D** | `0.05` | Noisy (std = 0.05) | [`results/reports/3D/std_0.05/statistical_summary.md`](3D/std_0.05/statistical_summary.md) |