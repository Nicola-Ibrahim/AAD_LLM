"""Evaluation Telemetry & Console Logger.

Provides structured, colorized, emoji-enhanced telemetry for empirical
benchmark trials, condition progress, caching notices, and batch summaries
utilizing Python's standard logging.Logger infrastructure.
"""

import logging
import sys
from collections.abc import Mapping
from typing import TextIO

from benchmarking.application.champions import GenerationMode
from benchmarking.application.interfaces.logger import EvaluationLoggerInterface


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


class EvaluationLogger(EvaluationLoggerInterface):
    """Specialized evaluation logger utilizing standard Python logging.Logger with custom colorization and emojis."""

    def __init__(
        self,
        verbose: bool = True,
        logger_name: str = "benchmarking.evaluation",
        stream: TextIO | None = None,
    ) -> None:
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
        self.logger.info(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🚀 {title.upper()}{Colors.RESET}")
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
        mode: GenerationMode | str | None = None,
        strategy: str | None = None,
    ) -> None:
        """Logs the start of an evaluation condition."""
        noise_color = Colors.GREEN if noise_std == 0.0 else Colors.BRIGHT_YELLOW
        p_name = f" ({problem_name})" if problem_name else ""
        icon = "🏆" if solver_type.lower() == "champion" else "⚙️"

        def column(label: str, value: str, color: str, width: int) -> str:
            return f"{Colors.BOLD}{label:<13}{Colors.RESET}{color}{value:<{width}}{Colors.RESET}"

        mode_value = getattr(mode, "value", mode) or "—"
        strategy_value = strategy or "—"
        fields = "  " + "  ".join(
            (
                column("Mode:", str(mode_value), Colors.BRIGHT_CYAN, 9),
                column("Strategy:", str(strategy_value), Colors.BRIGHT_MAGENTA, 13),
                column("Dim:", f"{dim}D", Colors.CYAN, 5),
                column("Noise level:", f"σ={noise_std:g}", noise_color, 8),
                f"{Colors.BOLD}{'Problem:':<13}{Colors.RESET}"
                f"{Colors.BRIGHT_MAGENTA}f{problem_id}{p_name}{Colors.RESET}",
            )
        )
        self.logger.info(
            f"\n{Colors.BOLD}{Colors.BRIGHT_BLUE}[{index}/{total}]{Colors.RESET} "
            f"{icon} {Colors.BOLD}{solver_type.title()}:{Colors.RESET} "
            f"{Colors.BRIGHT_CYAN}{solver_name}{Colors.RESET}\n{fields}"
        )

    def trial(
        self,
        trial_idx: int,
        total_trials: int,
        best_clean: float,
        runtime: float,
        evals_used: int,
        best_objective: float | None = None,
        true_optimum: float | None = None,
    ) -> None:
        """Log the clean objective, known optimum, and objective-gap error for a trial."""
        if best_clean < float("inf"):
            err_str = f"{Colors.BRIGHT_GREEN}{best_clean:.3f}{Colors.RESET}"
        else:
            err_str = f"{Colors.BRIGHT_RED}FAILED (inf){Colors.RESET}"

        score_details = ""
        if best_objective is not None and true_optimum is not None:
            score_details = (
                f"f-opt: {Colors.BRIGHT_MAGENTA}{true_optimum:.3f}{Colors.RESET} | "
                f"Best f: {Colors.BRIGHT_CYAN}{best_objective:.3f}{Colors.RESET} | "
            )

        self.logger.info(
            f"  {Colors.GRAY}•{Colors.RESET} {Colors.BOLD}⚡ Trial {trial_idx}/{total_trials}{Colors.RESET} | "
            f"{score_details}Δy Error: {err_str} | "
            f"Evals: {Colors.CYAN}{evals_used:,}{Colors.RESET} | "
            f"Time: {Colors.YELLOW}{runtime:.3f}s{Colors.RESET}"
        )

    def cached(self, runs_count: int, median_error: float | None) -> None:
        """Logs a cache-hit notice."""
        err_str = (
            f"{Colors.BRIGHT_GREEN}{median_error:.3f}{Colors.RESET}"
            if median_error is not None
            else "N/A"
        )
        self.logger.info(
            f"  📦 {Colors.DIM}[CACHED]{Colors.RESET} {Colors.GREEN}{runs_count} runs found{Colors.RESET} "
            f"(Median Δy Error: {err_str}). Skipping."
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
            f"{Colors.BRIGHT_GREEN}{median_error:.3f}{Colors.RESET}"
            if median_error is not None
            else "N/A"
        )
        self.logger.info(
            f"  ✨ {Colors.BOLD}{Colors.BRIGHT_GREEN}[COMPLETED]{Colors.RESET} {n_runs} runs finished | "
            f"Median Δy Error: {err_str}"
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

    def summary(self, title: str, stats: Mapping[str, object], width: int = 80) -> None:
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
