"""
Runner script executing the LLaMEA evolution loop across BBOB problem IDs.
"""

import os
from llamea import LLaMEA

from aad_llm.noisy_bbob import BBOBProblem
from aad_llm.prompts import TASK_PROMPT_TEMPLATE, EXAMPLE_PROMPT, FORMAT_PROMPT
from aad_llm.evaluator import Evaluator

def run_evolution_for_problem(
    problem: BBOBProblem,
    llm,
    budget: int = 1000,
    iterations: int = 30,
    output_dir: str = "generated_algorithms",
    log_dir: str = "logs"
):
    """
    Run LLaMEA optimization algorithm evolution for a single BBOB problem.
    """
    problem_id = problem.problem_id
    # 1. Create target directories if they don't exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(log_dir, f"bbob_{problem_id}"), exist_ok=True)

    print(f"--- Starting evolution for BBOB Problem {problem_id} (DIM={problem.dim}) ---")

    # 3. Instantiate the custom evaluator
    evaluator = Evaluator(
        problem=problem,
        budget=budget
    )


    # ! improtant to be solved if should be on all problems or each one on its own
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

    print(f"--- Completed BBOB Problem {problem_id}! Best Score (Fitness): {best_solution.fitness:.4f} ---")
    print(f"Saved algorithm to: {output_path}\n")
    return best_solution
