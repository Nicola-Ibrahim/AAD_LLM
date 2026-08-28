"""Evaluation Telemetry & Console Logger.

Provides structured, colorized, emoji-enhanced telemetry for empirical
benchmark trials, condition progress, caching notices, and batch summaries
utilizing Python's standard logging.Logger infrastructure.
"""

import logging
import sys
from typing import Any, TextIO


class Colors:
    """ANSI color codes for rich terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    BRIGHT_CYAN = "\033[96m"
    GREEN = "\033[32m"
    BRIGHT_GREEN = "\033[92m"
    YELLOW = "\033[33m"
    BRIGHT_YELLOW = "\033[93m"
    MAGENTA = "\033[35m"
    BRIGHT_MAGENTA = "\033[95m"
    BLUE = "\033[34m"
    BRIGHT_BLUE = "\033[94m"
    RED = "\033[31m"
    BRIGHT_RED = "\033[91m"
    GRAY = "\033[90m"


class EvaluationFormatter(logging.Formatter):
    """Clean formatter outputting message text directly without verbose log headers."""

    def format(self, record: logging.LogRecord) -> str:
        return record.getMessage()


class EvaluationLogger:
    """Specialized evaluation logger utilizing standard Python logging.Logger with custom colorization and emojis."""

    def __init__(
        self,
        verbose: bool = True,
        logger_name: str = "benchmarking.evaluation",
        stream: TextIO | None = None,
    ):
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        self._stream = stream or sys.stdout

        self._handler = logging.StreamHandler(self._stream)
        self._handler.setFormatter(EvaluationFormatter())

        self.logger.handlers.clear()
        self.logger.addHandler(self._handler)

        self.verbose = verbose

    @property
    def verbose(self) -> bool:
        """Current verbosity state."""
        return self.logger.level <= logging.INFO

    @verbose.setter
    def verbose(self, value: bool) -> None:
        level = logging.INFO if value else logging.WARNING
        self.logger.setLevel(level)
        self._handler.setLevel(level)

    def header(self, title: str, subtitle: str | None = None, width: int = 80) -> None:
        """Logs a prominent visual banner for a benchmark session."""
        sep = f"{Colors.BRIGHT_CYAN}{'=' * width}{Colors.RESET}"
        self.logger.info(f"\n{sep}")
        self.logger.info(
            f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🚀 {title.upper()}{Colors.RESET}"
        )
        if subtitle:
            self.logger.info(f"   {Colors.DIM}{subtitle}{Colors.RESET}")
        self.logger.info(sep)

    def condition_start(
        self,
        index: int,
        total: int,
        solver_type: str,
        solver_name: str,
        dim: int,
        noise_std: float,
        problem_id: int,
        problem_name: str = "",
    ) -> None:
        """Logs the start of an evaluation condition."""
        noise_label = (
            f"{Colors.GREEN}clean (σ=0.0){Colors.RESET}"
            if noise_std == 0.0
            else f"{Colors.BRIGHT_YELLOW}noisy (σ={noise_std}){Colors.RESET}"
        )
        p_name = f" ({problem_name})" if problem_name else ""
        icon = "🏆" if solver_type.lower() == "champion" else "⚙️"

        self.logger.info(
            f"\n{Colors.BOLD}{Colors.BRIGHT_BLUE}[{index}/{total}]{Colors.RESET} "
            f"{icon} {Colors.BOLD}{solver_type.title()}:{Colors.RESET} {Colors.BRIGHT_CYAN}{solver_name}{Colors.RESET} | "
            f"{Colors.BOLD}Dim:{Colors.RESET} {dim}D | "
            f"{Colors.BOLD}Noise:{Colors.RESET} {noise_label} | "
            f"{Colors.BOLD}Problem:{Colors.RESET} {Colors.BRIGHT_MAGENTA}f{problem_id}{p_name}{Colors.RESET}"
        )

    def trial(
        self,
        trial_idx: int,
        total_trials: int,
        best_clean: float,
        runtime: float,
        evals_used: int,
    ) -> None:
        """Logs individual trial execution details with metrics."""
        if best_clean < float("inf"):
            err_str = f"{Colors.BRIGHT_GREEN}{best_clean:>12.4e}{Colors.RESET}"
        else:
            err_str = f"{Colors.BRIGHT_RED}{'FAILED (inf)':>12}{Colors.RESET}"

        self.logger.info(
            f"  {Colors.GRAY}•{Colors.RESET} {Colors.BOLD}⚡ Trial {trial_idx:2d}/{total_trials:2d}{Colors.RESET} | "
            f"Error: {err_str} | "
            f"Evals: {Colors.CYAN}{evals_used:>7,}{Colors.RESET} | "
            f"Time: {Colors.YELLOW}{runtime:>5.2f}s{Colors.RESET}"
        )

    def cached(self, runs_count: int, median_error: float | None) -> None:
        """Logs a cache-hit notice."""
        err_str = (
            f"{Colors.BRIGHT_GREEN}{median_error:.4e}{Colors.RESET}"
            if median_error is not None
            else "N/A"
        )
        self.logger.info(
            f"  📦 {Colors.DIM}[CACHED]{Colors.RESET} {Colors.GREEN}{runs_count} runs found{Colors.RESET} "
            f"(Median Error: {err_str}). Skipping."
        )

    def resuming(self, existing_runs: int, target_runs: int) -> None:
        """Logs a resumption notice for partial runs."""
        self.logger.info(
            f"  🔄 {Colors.BRIGHT_YELLOW}[RESUMING]{Colors.RESET} Found {existing_runs}/{target_runs} completed runs. "
            f"Continuing from Trial {existing_runs + 1}..."
        )

    def condition_complete(self, n_runs: int, median_error: float | None) -> None:
        """Logs completion of a condition."""
        err_str = (
            f"{Colors.BRIGHT_GREEN}{median_error:.4e}{Colors.RESET}"
            if median_error is not None
            else "N/A"
        )
        self.logger.info(
            f"  ✨ {Colors.BOLD}{Colors.BRIGHT_GREEN}[COMPLETED]{Colors.RESET} {n_runs} runs finished | "
            f"Median Clean Error: {err_str}"
        )

    def missing_code(self, code_path: str) -> None:
        """Logs when algorithm code file is missing."""
        self.logger.error(
            f"  ❌ {Colors.BOLD}{Colors.BRIGHT_RED}[MISSING CODE]{Colors.RESET} "
            f"Algorithm file not found at '{code_path}'. Skipping."
        )

    def info(self, msg: str) -> None:
        """Logs an informational message."""
        self.logger.info(f"ℹ️  {Colors.CYAN}{msg}{Colors.RESET}")

    def success(self, msg: str) -> None:
        """Logs a success message."""
        self.logger.info(f"✅ {Colors.BRIGHT_GREEN}{msg}{Colors.RESET}")

    def warning(self, msg: str) -> None:
        """Logs a warning message."""
        self.logger.warning(f"⚠️  {Colors.BRIGHT_YELLOW}{msg}{Colors.RESET}")

    def error(self, msg: str) -> None:
        """Logs an error message."""
        self.logger.error(f"❌ {Colors.BRIGHT_RED}{msg}{Colors.RESET}")

    def summary(self, title: str, stats: dict[str, Any], width: int = 80) -> None:
        """Logs a batch completion summary banner."""
        sep = f"{Colors.BRIGHT_GREEN}{'=' * width}{Colors.RESET}"
        stats_str = " | ".join(
            f"{Colors.BOLD}{k}:{Colors.RESET} {Colors.BRIGHT_CYAN}{v}{Colors.RESET}"
            for k, v in stats.items()
        )
        self.logger.info(sep)
        self.logger.info(
            f"{Colors.BOLD}{Colors.BRIGHT_GREEN}🏁 {title.upper()}{Colors.RESET} | {stats_str}"
        )
        self.logger.info(sep)
