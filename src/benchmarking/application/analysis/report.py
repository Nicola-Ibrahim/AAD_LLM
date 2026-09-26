from pathlib import Path
import pandas as pd

from benchmarking.application.interfaces.markdown_report_writer import MarkdownReportWriter


def generate_markdown_report(
    df_omnibus: pd.DataFrame | None = None,
    df_pairwise: pd.DataFrame | None = None,
    output_path: Path | None = None,
    omnibus_df: pd.DataFrame | None = None,
    pairwise_df: pd.DataFrame | None = None,
    writer: MarkdownReportWriter | None = None,
) -> str:
    """Generate scientific Markdown summary report documenting statistical test results."""
    o_df = (
        df_omnibus
        if df_omnibus is not None
        else (omnibus_df if omnibus_df is not None else pd.DataFrame())
    )
    p_df = (
        df_pairwise
        if df_pairwise is not None
        else (pairwise_df if pairwise_df is not None else pd.DataFrame())
    )

    report_lines: list[str] = [
        "# Comprehensive Empirical Evaluation & Statistical Analysis Report",
        "",
        "## 1. Overview & Experimental Protocol",
        "- **Benchmark Suite**: BBOB (Black-Box Optimization Benchmarking)",
        "- **Statistical Protocols**: Kruskal-Wallis H-test (omnibus), Mann-Whitney U test (pairwise)",
        "- **Multiplicity Correction**: Benjamini-Hochberg False Discovery Rate (FDR, $\\alpha=0.05$)",
        "- **Effect Size Metric**: Vargha-Delaney $\\hat{A}_{12}$ non-parametric effect size",
        "",
    ]

    if not o_df.empty:
        total_tests = len(o_df)
        sig_tests = (
            int((o_df["Significant"] == "Yes").sum()) if "Significant" in o_df.columns else 0
        )
        report_lines.extend(
            [
                "## 2. Omnibus Kruskal-Wallis Significance Summary",
                f"- **Total Experimental Conditions Evaluated**: {total_tests}",
                f"- **Statistically Significant omnibus Differences ($p < 0.05$)**: {sig_tests} / {total_tests} ({(sig_tests / max(1, total_tests) * 100):.1f}%)",
                "",
                "### Omnibus Differences by Problem Dimension",
            ]
        )
        if "Dim" in o_df.columns:
            for dim, group in o_df.groupby("Dim"):
                d_sig = int((group["Significant"] == "Yes").sum())
                report_lines.append(
                    f"- **{dim}D**: {d_sig} / {len(group)} conditions reject null hypothesis"
                )
        report_lines.append("")

    if not p_df.empty:
        total_pw = len(p_df)
        sig_pw = int(p_df["Significant (FDR)"].sum()) if "Significant (FDR)" in p_df.columns else 0
        report_lines.extend(
            [
                "## 3. Pairwise Comparisons & FDR Correction",
                f"- **Total Pairwise Hypothesis Tests**: {total_pw}",
                f"- **Significant Differences after FDR Correction ($\\alpha=0.05$)**: {sig_pw} / {total_pw} ({(sig_pw / max(1, total_pw) * 100):.1f}%)",
                "",
                "### Comparison Tier Breakdown",
            ]
        )
        if "Comparison Tier" in p_df.columns:
            for tier, group in p_df.groupby("Comparison Tier"):
                t_sig = int(group["Significant (FDR)"].sum())
                report_lines.append(f"- **{tier}**: {t_sig} / {len(group)} pairs significant")
        report_lines.append("")

    if output_path is not None:
        if writer is None:
            raise ValueError("A MarkdownReportWriter is required when output_path is set.")
        writer.write(Path(output_path), "\n".join(report_lines))

    return "\n".join(report_lines)
