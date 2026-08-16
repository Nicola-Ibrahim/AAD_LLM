import numpy as np

from domain.services.noise_strategy import (
    AWGNStrategy,
    HomoscedasticAdditiveNoiseStrategy,
    MultiplicativeNoiseStrategy,
    NoNoiseStrategy,
)
from infra.problems.bbob import BBOBProblem


def test_bbob_eval_scalar_clean(tmp_path):
    problem = BBOBProblem(
        problem_id=1, dim=2, noise_strategy=NoNoiseStrategy()
    )
    x = np.zeros(2)
    val = problem.eval_scalar(x)
    assert isinstance(val, float)


def test_bbob_eval_scalar_noisy(tmp_path):
    problem = BBOBProblem(
        problem_id=1,
        dim=2,
        noise_strategy=MultiplicativeNoiseStrategy(0.05),
    )
    x = np.zeros(2)
    val = problem.eval_scalar(x)
    assert isinstance(val, float)


def test_bbob_get_objective_fn(tmp_path):
    clean_problem = BBOBProblem(
        problem_id=1, dim=2, noise_strategy=NoNoiseStrategy()
    )
    noisy_problem = BBOBProblem(
        problem_id=1,
        dim=2,
        noise_strategy=MultiplicativeNoiseStrategy(0.1),
    )

    clean_fn = clean_problem.get_objective_fn()
    noisy_fn = noisy_problem.get_objective_fn()

    assert clean_fn is clean_problem
    assert noisy_fn is noisy_problem

    assert hasattr(noisy_fn, "lb")
    assert hasattr(noisy_fn, "ub")
    assert hasattr(noisy_fn, "bounds")
    assert hasattr(noisy_fn, "dim")

    x = np.zeros(2)
    clean_val = clean_fn(x)
    noisy_val = noisy_fn(x)

    assert isinstance(clean_val, float)
    assert isinstance(noisy_val, float)


def test_bbob_noise_model_strategies(tmp_path):
    x = np.array([1.0, 1.0])

    p_mult = BBOBProblem(
        problem_id=1,
        dim=2,
        noise_strategy=MultiplicativeNoiseStrategy(0.1),
    )
    assert p_mult.noise_model == "multiplicative"
    v_mult = p_mult(x)
    assert isinstance(v_mult, float)

    p_add = BBOBProblem(
        problem_id=1,
        dim=2,
        noise_strategy=HomoscedasticAdditiveNoiseStrategy(0.1),
    )
    assert p_add.noise_model == "homoscedastic_additive"
    v_add = p_add(x)
    assert isinstance(v_add, float)

    p_awgn = BBOBProblem(
        problem_id=1, dim=2, noise_strategy=AWGNStrategy(0.1)
    )
    assert p_awgn.noise_model == "awgn"
    v_awgn = p_awgn(x)
    assert isinstance(v_awgn, float)


def test_bbob_is_in_bounds_and_clip():
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy())
    valid_x = np.array([0.0, 1.0])
    invalid_x = np.array([10.0, -10.0])

    assert problem.is_in_bounds(valid_x) is True
    assert problem.is_in_bounds(invalid_x) is False

    clipped_x = problem.clip(invalid_x)
    assert problem.is_in_bounds(clipped_x) is True
    assert np.all(clipped_x >= problem.lb)
    assert np.all(clipped_x <= problem.ub)


def test_ioh_logger_records_clean_distance(tmp_path):
    import ioh
    from pathlib import Path
    from infra.problems import ProblemAnalyzer

    log_dir = tmp_path / "ioh_test"

    problem = BBOBProblem(
        problem_id=1,
        dim=2,
        noise_strategy=MultiplicativeNoiseStrategy(0.05),
    )

    x = np.array([1.0, 1.0])
    with ProblemAnalyzer(
        problem=problem,
        algorithm_name="TestAlgo",
        folder_name="run1",
        log_dir=log_dir,
    ):
        noisy_val = problem(x)
        assert isinstance(noisy_val, float)

    clean_problem_standalone = ioh.get_problem(1, 1, 2, ioh.ProblemClass.BBOB)
    expected_distance = clean_problem_standalone(x.tolist()) - clean_problem_standalone.optimum.y

    dat_files = list(Path(log_dir).rglob("*.dat"))
    assert len(dat_files) == 1
    content = dat_files[0].read_text()
    assert "evaluations raw_y" in content
    lines = content.strip().splitlines()
    assert len(lines) >= 2
    raw_y = float(lines[-1].split()[1])

    # Assert raw_y matches ground-truth clean distance (f_clean - f_opt), not noisy distance
    assert np.isclose(raw_y, expected_distance, atol=1e-5)


def test_ioh_logger_noisy_problem_does_not_corrupt_trajectory(tmp_path):
    from pathlib import Path
    from infra.problems import ProblemAnalyzer

    x_test = np.array([1.5, -2.0])

    dir_clean = tmp_path / "ioh_clean"
    p_clean = BBOBProblem(
        problem_id=1,
        dim=2,
        noise_strategy=NoNoiseStrategy(),
    )
    with ProblemAnalyzer(
        problem=p_clean,
        algorithm_name="CleanAlgo",
        folder_name="run",
        log_dir=dir_clean,
    ):
        p_clean.reset()
        _ = p_clean(x_test)

    dir_noisy = tmp_path / "ioh_noisy"
    p_noisy = BBOBProblem(
        problem_id=1,
        dim=2,
        noise_strategy=MultiplicativeNoiseStrategy(0.50),
    )
    with ProblemAnalyzer(
        problem=p_noisy,
        algorithm_name="NoisyAlgo",
        folder_name="run",
        log_dir=dir_noisy,
    ):
        p_noisy.reset()
        _ = p_noisy(x_test)

    clean_dat = list(Path(dir_clean).rglob("*.dat"))[0].read_text()
    noisy_dat = list(Path(dir_noisy).rglob("*.dat"))[0].read_text()

    clean_raw_y = float(clean_dat.strip().splitlines()[-1].split()[1])
    noisy_raw_y = float(noisy_dat.strip().splitlines()[-1].split()[1])

    # Noisy problem evaluation must produce identical IOH raw_y trajectory data as clean problem
    assert np.isclose(clean_raw_y, noisy_raw_y, atol=1e-6)
