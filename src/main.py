"""
Execution entrypoint for the LLaMEA noisy BBOB algorithm evolution experiment.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from llamea import LLM

from problems.bbob import BBOBProblem
import core.runner as runner
from analysis.results import save_summary, print_experiment_summary
from llm.providers import get_llm_client

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
    output_dir: str = "experiments"

    # Output directory for LLaMEA optimizer logs
    log_dir: str = "logs"

    # Whether LLaMEA writes local execution/prompt log folders
    log: bool = False

    # LLM provider to request solutions from (pulled from environment variable)
    llm_provider: str = field(default_factory=lambda: os.environ.get("LLM_PROVIDER", ""))

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


def initialize_llm(provider: str) -> LLM:
    """Initialize the LLM provider, exiting if it fails."""
    try:
        return get_llm_client(provider)
    except Exception as e:
        print(f"Failed to initialize LLM provider '{provider}': {e}", file=sys.stderr)
        sys.exit(1)


def run_evolution(config: ExperimentConfig, llm: LLM) -> list[Path]:
    """Run LLaMEA evolution across BBOB problem IDs and save summaries."""
    print(
        f"Starting evolution across problem(s): {config.problems} (DIM={config.dim}, max_evaluations={config.max_evaluations})..."
    )

    # Create target directories using pathlib
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    Path(config.log_dir).mkdir(parents=True, exist_ok=True)

    problem_instances = [BBOBProblem(problem_id=pid, dim=config.dim) for pid in config.problems]

    evolution_results = runner.run_evolution_for_problems(
        problems=problem_instances,
        noise_std=config.noise_std,
        llm=llm,
        max_evaluations=config.max_evaluations,
        iterations=config.iterations,
        verbose=True,
        log=config.log,
        output_dir=config.output_dir,
    )

    saved_summary_paths: list[Path] = []
    target_base = Path(config.output_dir)

    for res in evolution_results:
        if res.error_msg is None:
            problem_dir = target_base / res.experiment_name
            summary_path = save_summary(
                history=res.run_history,
                problem_id=res.problem_id,
                dim=res.dim,
                output_dir=problem_dir,
                mode=res.mode,
            )
            print(f"Saved summary for Problem {res.problem_id} to: {summary_path}")
            saved_summary_paths.append(summary_path)
        else:
            print(f"Problem {res.problem_id} failed: {res.error_msg}", file=sys.stderr)

    return saved_summary_paths


def main():
    # 1. Initialize config & LLM
    config = ExperimentConfig()

    llm = initialize_llm(config.llm_provider)
    config.llm_model = getattr(llm, "model", "N/A")
    config.connection_endpoint = getattr(llm, "base_url", "")

    # 2. Print configuration panel
    print(config)
    print()

    # 3. Run evolution (executes & saves summary.json artifacts)
    run_evolution(config, llm)
    print()

    # 4. Collect and display saved artifact summaries
    target_dir = Path(config.output_dir)
    print_experiment_summary(target_dir)


if __name__ == "__main__":
    main()
