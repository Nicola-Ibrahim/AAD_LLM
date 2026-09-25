"""Formatting tests for benchmark trial telemetry."""

from io import StringIO

from benchmarking.infra.logging.evaluation_logger import EvaluationLogger


def test_trial_values_use_three_decimals_without_field_padding():
    stream = StringIO()
    logger = EvaluationLogger(stream=stream)
    logger.trial(
        trial_idx=1,
        total_trials=20,
        best_clean=81.46921,
        runtime=0.1236,
        evals_used=50_000,
        best_objective=79.12349,
        true_optimum=-2.34567,
    )

    output = stream.getvalue()
    assert "Trial 1/20" in output
    assert "f-opt: \033[95m-2.346\033[0m" in output
    assert "Best f: \033[96m79.123\033[0m" in output
    assert "Δy Error: \033[92m81.469\033[0m" in output
    assert "Evals: \033[36m50,000\033[0m" in output
    assert "Time: \033[33m0.124s\033[0m" in output
    assert "          -2.345670" not in output


def test_cached_and_completed_errors_use_three_decimals():
    stream = StringIO()
    logger = EvaluationLogger(stream=stream)
    logger.cached(3, 0.123456)
    logger.condition_complete(3, 0.987654)

    output = stream.getvalue()
    assert "Median Δy Error: \033[92m0.123\033[0m" in output
    assert "Median Δy Error: \033[92m0.988\033[0m" in output


def test_noise_level_preserves_configured_precision_without_repeated_noise_label():
    stream = StringIO()
    logger = EvaluationLogger(stream=stream)
    logger.condition_start(
        1, 2, "champion", "Model", 3, 0.05, 8,
        problem_name="Sphere", mode="explicit", strategy="guided",
    )

    output = stream.getvalue()
    assert "Noise level: \033[0m\033[93mσ=0.05  \033[0m" in output
    assert "noisy" not in output
    assert "σ=0.050" not in output
    assert "Mode:        \033[0m\033[96mexplicit \033[0m" in output
    assert "Strategy:    \033[0m\033[95mguided       \033[0m" in output
    assert "Dim:         \033[0m\033[36m3D   \033[0m" in output
    assert "Problem:     \033[0m\033[95mf8 (Sphere)\033[0m" in output
