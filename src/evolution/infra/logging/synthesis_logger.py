"""Synthesis Telemetry & Console Logger.

Provides structured, colorized, emoji-enhanced telemetry for LLaMEA evolutionary
synthesis campaigns, per-generation candidate evaluations, auto-resumption notices,
and task dispatch summaries utilizing Python's standard logging.Logger infrastructure.
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


class SynthesisFormatter(logging.Formatter):
    """Clean formatter outputting message text directly without verbose log headers."""

    def format(self, record: logging.LogRecord) -> str:
        return record.getMessage()


class SynthesisLogger:
    """Specialized synthesis logger utilizing standard Python logging.Logger with custom colorization and emojis."""

    def __init__(
        self,
        verbose: bool = True,
        logger_name: str = "evolution.synthesis",
        stream: TextIO | None = None,
    ):
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        self._stream = stream or sys.stdout

        self._handler = logging.StreamHandler(self._stream)
        self._handler.setFormatter(SynthesisFormatter())

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
        """Logs a prominent visual banner for a synthesis session."""
        sep = f"{Colors.BRIGHT_CYAN}{'=' * width}{Colors.RESET}"
        self.logger.info(f"\n{sep}")
        self.logger.info(
            f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🧬 {title.upper()}{Colors.RESET}"
        )
        if subtitle:
            self.logger.info(f"   {Colors.DIM}{subtitle}{Colors.RESET}")
        self.logger.info(sep)

    def task_start(
        self,
        index: int,
        total: int,
        model_name: str,
        dim: int,
        noise_std: float,
        problem_id: int,
        strategy: str,
        experiment_id: int,
        problem_name: str = "",
    ) -> None:
        """Logs the start of an evolutionary synthesis task."""
        noise_label = (
            f"{Colors.GREEN}clean (σ=0.0){Colors.RESET}"
            if noise_std == 0.0
            else f"{Colors.BRIGHT_YELLOW}noisy (σ={noise_std}){Colors.RESET}"
        )
        p_name = f" ({problem_name})" if problem_name else ""

        self.logger.info(
            f"\n{Colors.BOLD}{Colors.BRIGHT_BLUE}[{index}/{total}]{Colors.RESET} "
            f"🧬 {Colors.BOLD}Task:{Colors.RESET} {Colors.BRIGHT_CYAN}{model_name}{Colors.RESET} | "
            f"{Colors.BOLD}Dim:{Colors.RESET} {dim}D | "
            f"{Colors.BOLD}Noise:{Colors.RESET} {noise_label} | "
            f"{Colors.BOLD}Problem:{Colors.RESET} {Colors.BRIGHT_MAGENTA}f{problem_id}{p_name}{Colors.RESET} | "
            f"{Colors.BOLD}Strategy:{Colors.RESET} {Colors.MAGENTA}{strategy.capitalize()}{Colors.RESET} | "
            f"{Colors.BOLD}Exp ID:{Colors.RESET} #{experiment_id}"
        )

    def generation(
        self,
        gen_idx: int,
        total_gens: int,
        algo_name: str,
        error: float | None,
        fitness: float | None,
        evals_used: int,
        runtime: float,
        is_failure: bool = False,
        failure_reason: str = "",
    ) -> None:
        """Logs individual generation candidate evaluation details."""
        if not is_failure and error is not None and error < float("inf"):
            err_str = f"{Colors.BRIGHT_GREEN}{error:>12.4e}{Colors.RESET}"
            fit_str = f"{Colors.CYAN}{fitness:>12.4e}{Colors.RESET}" if fitness is not None else "N/A"
            self.logger.info(
                f"  {Colors.GRAY}•{Colors.RESET} {Colors.BOLD}⚡ Gen {gen_idx:2d}/{total_gens:2d}{Colors.RESET} | "
                f"Algo: {Colors.BRIGHT_CYAN}{algo_name:<18}{Colors.RESET} | "
                f"Error: {err_str} | "
                f"Fitness: {fit_str} | "
                f"Evals: {Colors.CYAN}{evals_used:>7,}{Colors.RESET} | "
                f"Time: {Colors.YELLOW}{runtime:>5.2f}s{Colors.RESET}"
            )
        else:
            reason = f" ({failure_reason})" if failure_reason else ""
            err_str = f"{Colors.BRIGHT_RED}{'FAILED' + reason:>18}{Colors.RESET}"
            self.logger.info(
                f"  {Colors.GRAY}•{Colors.RESET} {Colors.BOLD}⚡ Gen {gen_idx:2d}/{total_gens:2d}{Colors.RESET} | "
                f"Algo: {Colors.DIM}{algo_name:<18}{Colors.RESET} | "
                f"Error: {err_str} | "
                f"Time: {Colors.YELLOW}{runtime:>5.2f}s{Colors.RESET}"
            )

    def resuming(self, exp_id: int, current_iter: int, total_iters: int) -> None:
        """Logs an auto-resumption notice for an existing experiment."""
        self.logger.info(
            f"  🔄 {Colors.BRIGHT_YELLOW}[RESUMING]{Colors.RESET} Found {current_iter}/{total_iters} completed generations "
            f"for Exp #{exp_id}. Continuing from Generation {current_iter + 1}..."
        )

    def cached(self, exp_id: int, total_iters: int, best_error: float | None) -> None:
        """Logs a skip notice for already completed experiment."""
        err_str = (
            f"{Colors.BRIGHT_GREEN}{best_error:.4e}{Colors.RESET}"
            if best_error is not None
            else "N/A"
        )
        self.logger.info(
            f"  📦 {Colors.DIM}[COMPLETED]{Colors.RESET} Exp #{exp_id} already has {total_iters} generations "
            f"(Best Error: {err_str}). Skipping."
        )

    def stagnation_warning(self, consecutive_failures: int, threshold: int) -> None:
        """Logs diversity injection warning upon consecutive failure threshold."""
        self.logger.warning(
            f"  ⚠️  {Colors.BRIGHT_YELLOW}[STAGNATION]{Colors.RESET} {consecutive_failures} consecutive failures "
            f"(threshold: {threshold}). Injecting meta-feedback diversity guidance..."
        )

    def task_complete(
        self,
        exp_id: int,
        best_algo_name: str,
        best_error: float | None,
        raw_obj: float | None = None,
        true_opt: float | None = None,
    ) -> None:
        """Logs completion of an evolutionary synthesis task."""
        if best_error is not None and best_error < float("inf"):
            err_str = f"{Colors.BRIGHT_GREEN}{best_error:.6e}{Colors.RESET}"
            obj_str = (
                f" | Obj: {Colors.CYAN}{raw_obj:.6f}{Colors.RESET} (Opt: {true_opt:.6f})"
                if raw_obj is not None and true_opt is not None
                else ""
            )
            self.logger.info(
                f"  ✨ {Colors.BOLD}{Colors.BRIGHT_GREEN}[SYNTHESIS COMPLETE]{Colors.RESET} Exp #{exp_id} | "
                f"Best: {Colors.BOLD}{best_algo_name}{Colors.RESET} | "
                f"Final Error: {err_str}{obj_str}"
            )
        else:
            self.logger.info(
                f"  ⚠️  {Colors.BOLD}{Colors.BRIGHT_YELLOW}[SYNTHESIS INCOMPLETE]{Colors.RESET} Exp #{exp_id} | "
                f"No valid candidate converged."
            )

    def audit_summary(
        self,
        model_name: str,
        total_conditions: int,
        completed: int,
        pending: int,
        retry: int,
        progress_pct: float,
    ) -> None:
        """Logs a formatted synthesis search space audit summary."""
        self.logger.info(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}🎯 Synthesis Matrix Audit for '{model_name}':{Colors.RESET}")
        self.logger.info(f"   • Configured Matrix Size:  {Colors.BOLD}{total_conditions}{Colors.RESET} conditions")
        self.logger.info(f"   • Completed (Champions):   {Colors.BRIGHT_GREEN}{completed}/{total_conditions}{Colors.RESET} ({progress_pct:.1f}%)")
        self.logger.info(f"   • Pending Workload:        {Colors.BRIGHT_YELLOW}{pending}{Colors.RESET}")
        if retry > 0:
            self.logger.info(f"   • Failed Runs (To Retry):  {Colors.BRIGHT_RED}{retry}{Colors.RESET}")

    def summary(
        self,
        title: str,
        stats: dict[str, Any],
        width: int = 80,
    ) -> None:
        """Logs a formatted summary box with key-value metric pairs."""
        sep = f"{Colors.BRIGHT_CYAN}{'=' * width}{Colors.RESET}"
        self.logger.info(f"\n{sep}")
        self.logger.info(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}🏁 {title.upper()}{Colors.RESET}")
        self.logger.info(sep)
        for k, v in stats.items():
            self.logger.info(
                f"   {Colors.BOLD}{k:<26}:{Colors.RESET} {Colors.BRIGHT_CYAN}{v}{Colors.RESET}"
            )
        self.logger.info(f"{sep}\n")

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
