"""
Execution entrypoint for the LLaMEA noisy BBOB algorithm evolution experiment.
"""

import sys
import os
from dotenv import load_dotenv

import aad_llm.runner as runner
from aad_llm.llm_providers import build_llm, Provider
from aad_llm.noisy_bbob import BBOBProblem

# Load environment variables from .env if present
load_dotenv()

# =====================================================================
# EXPERIMENT CONFIGURATION
# Adjust these constants to configure your run.
# =====================================================================
# Range or list of BBOB Problem IDs (1-24) to run.
# Examples:
#   PROBLEMS = range(1, 25)  # Runs all 24 problems (1 to 24)
#   PROBLEMS = range(1, 2)   # Runs only problem 1
#   PROBLEMS = [1, 3, 5]     # Runs specific problems 1, 3, and 5
PROBLEMS = range(1, 2)

DIM = 3                   # Search space dimensionality (e.g. 3 or 5)
NOISE_STD = 0.05          # Standard deviation of additive Gaussian noise
BUDGET = 1000             # Objective function call budget per run
ITERATIONS = 30           # Number of LLM evolution iterations per problem
OUTPUT_DIR = "generated_algorithms"
LOG_DIR = "logs"

# =====================================================================
# LLM PROVIDER CONFIGURATION
# Choose provider. Config values will be pulled automatically from env.
# =====================================================================
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", Provider.GEMINI)
# =====================================================================

def main():
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    try:
        llm = build_llm(LLM_PROVIDER)
    except Exception as e:
        console.print(f"[bold red]Failed to initialize LLM provider '{LLM_PROVIDER}': {e}[/bold red]", style="red")
        sys.exit(1)

    # Display configuration panel
    config_table = Table.grid(padding=(0, 2))
    config_table.add_column(style="bold cyan")
    config_table.add_column()
    
    config_table.add_row("Provider", str(LLM_PROVIDER))
    config_table.add_row("Model Target", getattr(llm, "model", "N/A"))
    if hasattr(llm, "base_url") and llm.base_url:
        config_table.add_row("Connection Endpoint", llm.base_url)
    config_table.add_row("Problems to Run", str(list(PROBLEMS)))
    config_table.add_row("Dimension (DIM)", str(DIM))
    config_table.add_row("Evaluation Budget", str(BUDGET))
    config_table.add_row("Iterations", str(ITERATIONS))
    config_table.add_row("Noise Standard Dev", f"{NOISE_STD:.4f}")

    console.print(
        Panel(
            config_table,
            title="[bold green]LLaMEA Noisy BBOB Evolution Experiment[/bold green]",
            subtitle="[yellow]Ensure your LLM server/API is accessible before starting[/yellow]",
            expand=False
        )
    )
    console.print()

    console.print(f"[bold blue]Starting evolution across problem(s): {list(PROBLEMS)} (DIM={DIM}, budget={BUDGET})...[/bold blue]")
    
    results = {}
    for problem_id in PROBLEMS:
        console.print(f"\n[bold yellow]>>> Evolving algorithm for BBOB Problem {problem_id}...[/bold yellow]")
        try:
            # Instantiate BBOBProblem directly (validation is handled inside constructor)
            problem = BBOBProblem(
                problem_id=problem_id,
                dim=DIM,
                noise_std=NOISE_STD,
                instance_id=1
            )
            best_sol = runner.run_evolution_for_problem(
                problem=problem,
                llm=llm,
                budget=BUDGET,
                iterations=ITERATIONS,
                output_dir=OUTPUT_DIR,
                log_dir=LOG_DIR
            )
            results[problem_id] = best_sol.fitness
        except Exception as e:
            console.print(f"[bold red]Error evolving algorithm for problem {problem_id}: {e}[/bold red]", style="red")
            results[problem_id] = None
            
    # Display results in a clean table
    results_table = Table(title="[bold green]Experiment Results - Final Scores[/bold green]", show_header=True, header_style="bold magenta")
    results_table.add_column("Problem ID", justify="right", style="cyan")
    results_table.add_column("Score (Fitness)", justify="right")

    for pid, score in results.items():
        if score is not None:
            score_str = f"[bold green]{score:.4f}[/bold green]"
        else:
            score_str = "[bold red]FAILED[/bold red]"
        results_table.add_row(str(pid), score_str)
        
    console.print(results_table)

if __name__ == "__main__":
    main()
