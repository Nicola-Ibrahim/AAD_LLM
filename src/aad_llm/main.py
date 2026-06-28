"""
Execution entrypoint for the LLaMEA noisy BBOB algorithm evolution experiment.
"""

import sys
import os
import aad_llm.runner as runner
from aad_llm.llm_providers import build_llm, PROVIDER_GEMINI, PROVIDER_LMSTUDIO

# =====================================================================
# EXPERIMENT CONFIGURATION
# Adjust these constants to configure your run.
# =====================================================================
RUN_ALL_PROBLEMS = False  # Set to True to evolve all 24 problems sequentially
PROBLEM_ID = 1            # BBOB Problem ID (1-24) to run when RUN_ALL_PROBLEMS is False

DIM = 3                   # Search space dimensionality (e.g. 3 or 5)
NOISE_STD = 0.05          # Standard deviation of additive Gaussian noise
BUDGET = 1000             # Objective function call budget per run
ITERATIONS = 30           # Number of LLM evolution iterations per problem
OUTPUT_DIR = "generated_algorithms"
LOG_DIR = "logs"

# =====================================================================
# LLM PROVIDER CONFIGURATION
# Choose provider and configure keys/models/URLs below.
# =====================================================================
LLM_PROVIDER = PROVIDER_GEMINI  # Choose: PROVIDER_GEMINI or PROVIDER_LMSTUDIO

LLM_CONFIGS = {
    PROVIDER_GEMINI: {
        # Falls back to GOOGLE_API_KEY env var if not set
        "api_key": os.environ.get("GOOGLE_API_KEY", ""),
        "model": "gemini-2.0-flash",
    },
    PROVIDER_LMSTUDIO: {
        # Falls back to LLM_STUDIO_API_KEY env var, then "llm-studio"
        "api_key": os.environ.get("LLM_STUDIO_API_KEY", "llm-studio"),
        "model": "local-model",
        # Falls back to LLM_STUDIO_BASE_URL env var, then http://localhost:1234/v1
        "base_url": os.environ.get("LLM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
    },
}
# =====================================================================

def main():
    try:
        config = LLM_CONFIGS[LLM_PROVIDER]
        llm = build_llm(LLM_PROVIDER, **config)
    except Exception as e:
        print(f"Failed to initialize LLM provider '{LLM_PROVIDER}': {e}", file=sys.stderr)
        sys.exit(1)

    print("=================================================================")
    print(" LLaMEA Noisy BBOB Evolution Experiment")
    print("=================================================================")
    print(f"Provider:            {LLM_PROVIDER}")
    print(f"Model target:        {llm.model}")
    if hasattr(llm, "base_url") and llm.base_url:
        print(f"Connection Endpoint: {llm.base_url}")
    print("Ensure your LLM server/API is accessible before starting execution.")
    print("=================================================================\n")

    if RUN_ALL_PROBLEMS:
        print(f"Starting execution across all 24 problems (DIM={DIM}, budget={BUDGET})...")
        results = runner.run_all_problems(
            llm=llm,
            dim=DIM,
            noise_std=NOISE_STD,
            budget=BUDGET,
            iterations=ITERATIONS,
            output_dir=OUTPUT_DIR,
            log_dir=LOG_DIR
        )
        print("=================================================================")
        print("Experiment run completed! Final scores:")
        for pid, score in results.items():
            score_str = f"{score:.4f}" if score is not None else "FAILED"
            print(f"  Problem {pid:2d}: Score = {score_str}")
        print("=================================================================")
    else:
        if not isinstance(PROBLEM_ID, int) or not (1 <= PROBLEM_ID <= 24):
            print(
                "Error: Please set PROBLEM_ID to an integer between 1 and 24, "
                "or set RUN_ALL_PROBLEMS = True.", 
                file=sys.stderr
            )
            sys.exit(1)
            
        print(f"Starting execution for Problem {PROBLEM_ID} (DIM={DIM}, budget={BUDGET})...")
        try:
            runner.run_evolution_for_problem(
                problem_id=PROBLEM_ID,
                llm=llm,
                dim=DIM,
                noise_std=NOISE_STD,
                budget=BUDGET,
                iterations=ITERATIONS,
                output_dir=OUTPUT_DIR,
                log_dir=LOG_DIR
            )
            print("Successfully completed evolution!")
        except Exception as e:
            print(f"Execution failed: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
