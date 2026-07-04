"""
Execution entrypoint for the LLaMEA noisy BBOB algorithm evolution experiment.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

import aad_llm.core.runner as runner
from aad_llm.llm.providers import Provider, build_llm

# Load environment variables from .env if present
load_dotenv()


@dataclass
class ExperimentConfig:
    # BBOB problem IDs to evolve algorithms for (e.g., [1, 2, 3])
    problems: list[int] = field(default_factory=lambda: list(range(1, 2)))

    # Dimensionality of the optimization problem search space
    dim: int = 3

    # Standard deviation of statistical noise added to objective function evaluations
    noise_std: float = 0.05

    # Number of objective function evaluations allowed for each candidate algorithm
    max_evaluations: int = 1000

    # Number of LLaMEA evolution cycles (LLM calls to generate/refine code)
    iterations: int = 5

    # Output directory where the final generated Python algorithms will be saved
    output_dir: str = "generated_algorithms"

    # Output directory for LLaMEA optimizer logs
    log_dir: str = "logs"

    # Whether LLaMEA writes local execution/prompt log folders
    log: bool = False

    # LLM provider to request solutions from (pulled from environment variable)
    llm_provider: str = field(
        default_factory=lambda: os.environ.get("LLM_PROVIDER", Provider.GEMINI)
    )

    # Target model name (automatically populated during initialization)
    llm_model: str = "N/A"

    # API connection endpoint url (automatically populated during initialization)
    connection_endpoint: str = ""

    def __str__(self) -> str:
        lines = [
            "==================================================",
            "LLaMEA Noisy BBOB Evolution Experiment Configuration",
            "==================================================",
            f"Provider:            {self.llm_provider}",
            f"Model Target:        {self.llm_model}",
        ]
        if self.connection_endpoint:
            lines.append(f"Connection Endpoint: {self.connection_endpoint}")
        lines.extend(
            [
                f"Problems to Run:     {self.problems}",
                f"Dimension (DIM):     {self.dim}",
                f"Max Evaluations:     {self.max_evaluations}",
                f"Iterations:          {self.iterations}",
                f"Noise Standard Dev:  {self.noise_std:.4f}",
                f"Enable Logging:      {self.log}",
                "==================================================",
            ]
        )
        return "\n".join(lines)


@dataclass
class ExperimentResults:
    results: dict[int, float | None] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = [
            "==================================================",
            "Experiment Results - Final Scores",
            "==================================================",
            "Problem ID | Score (Fitness)",
            "-----------|----------------",
        ]
        for pid, score in self.results.items():
            score_str = f"{score:.4f}" if score is not None else "FAILED"
            lines.append(f"{pid:<10} | {score_str}")
        lines.append("==================================================")
        return "\n".join(lines)


def initialize_llm(provider: str):
    """Initialize the LLM provider, exiting if it fails."""
    try:
        return build_llm(provider)
    except Exception as e:
        print(f"Failed to initialize LLM provider '{provider}': {e}", file=sys.stderr)
        sys.exit(1)


def run_evolution(config: ExperimentConfig, llm) -> ExperimentResults:
    """Run LLaMEA evolution across BBOB problem IDs."""
    print(
        f"Starting evolution across problem(s): {config.problems} (DIM={config.dim}, max_evaluations={config.max_evaluations})..."
    )

    # Create target directories using pathlib
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    Path(config.log_dir).mkdir(parents=True, exist_ok=True)
    for problem_id in config.problems:
        (Path(config.log_dir) / f"bbob_{problem_id}").mkdir(parents=True, exist_ok=True)

    raw_results = runner.run_evolution_for_problems(
        problems=config.problems,
        dim=config.dim,
        noise_std=config.noise_std,
        llm=llm,
        max_evaluations=config.max_evaluations,
        iterations=config.iterations,
        output_dir=config.output_dir,
        log_dir=config.log_dir,
        verbose=True,
        log=config.log,
    )

    return ExperimentResults(results=raw_results)


def main():
    # 1. Initialize config & LLM
    config = ExperimentConfig()

    llm = initialize_llm(config.llm_provider)
    config.llm_model = getattr(llm, "model", "N/A")
    config.connection_endpoint = getattr(llm, "base_url", "")

    # 2. Print configuration panel
    print(config)
    print()

    # 3. Run and print results
    results = run_evolution(config, llm)
    print(results)


if __name__ == "__main__":
    main()
