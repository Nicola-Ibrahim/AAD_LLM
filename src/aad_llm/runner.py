"""
Runner script executing the LLaMEA evolution loop across BBOB problem IDs.
"""

import os
from llamea import LLaMEA

from aad_llm.prompts import TASK_PROMPT_TEMPLATE, EXAMPLE_PROMPT, FORMAT_PROMPT
from aad_llm.evaluator import Evaluator

def run_evolution_for_problem(
    problem_id: int,
    llm,
    dim: int = 3,
    noise_std: float = 0.05,
    budget: int = 1000,
    iterations: int = 30,
    output_dir: str = "generated_algorithms",
    log_dir: str = "logs"
):
    """
    Run LLaMEA optimization algorithm evolution for a single BBOB problem.
    """
    # 1. Create target directories if they don't exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(log_dir, f"bbob_{problem_id}"), exist_ok=True)

    print(f"--- Starting evolution for BBOB Problem {problem_id} (DIM={dim}) ---")

    # 3. Instantiate the custom evaluator
    evaluator = Evaluator(
        problem_id=problem_id,
        dim=dim,
        noise_std=noise_std,
        budget=budget,
        instance_id=1
    )

    # 4. Initialize LLaMEA
    optimizer = LLaMEA(
        f=evaluator,
        llm=llm,
        n_parents=1,
        n_offspring=1,
        budget=iterations,
        task_prompt=TASK_PROMPT_TEMPLATE.format(problem_id=problem_id),
        example_prompt=EXAMPLE_PROMPT,
        output_format_prompt=FORMAT_PROMPT,
        experiment_name=f"bbob_{problem_id}",
        log=True
    )

    # 6. Run the evolution loop
    best_solution = optimizer.run()

    # 7. Save the best algorithm code to a python file
    output_path = os.path.join(output_dir, f"best_algo_bbob_{problem_id}.py")
    with open(output_path, "w") as f:
        f.write(best_solution.code)

    print(f"--- Completed BBOB Problem {problem_id}! Best Score (Fitness): {best_solution.score:.4f} ---")
    print(f"Saved algorithm to: {output_path}\n")
    return best_solution

def run_all_problems(
    llm,
    dim: int = 3,
    noise_std: float = 0.05,
    budget: int = 1000,
    iterations: int = 30,
    output_dir: str = "generated_algorithms",
    log_dir: str = "logs"
):
    """
    Sequentially run the evolution loop for BBOB problems 1 through 24.
    """
    results = {}
    for problem_id in range(1, 25):
        try:
            best_sol = run_evolution_for_problem(
                problem_id=problem_id,
                llm=llm,
                dim=dim,
                noise_std=noise_std,
                budget=budget,
                iterations=iterations,
                output_dir=output_dir,
                log_dir=log_dir
            )
            results[problem_id] = best_sol.score
        except Exception as e:
            print(f"Error evolving algorithm for problem {problem_id}: {e}")
            results[problem_id] = None
            
    return results
