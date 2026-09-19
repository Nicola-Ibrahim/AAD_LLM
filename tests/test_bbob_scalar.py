import numpy as np

from evolution.domain.services.noise_strategy import (
    AWGNStrategy,
    HomoscedasticAdditiveNoiseStrategy,
    HeteroscedasticNoiseStrategy,
    NoNoiseStrategy,
)
from evolution.infra.problems.bbob import BBOBProblem


def test_bbob_eval_scalar_clean(tmp_path):
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy())
    x = np.zeros(2)
    val = problem.eval_scalar(x)
    assert isinstance(val, float)


def test_bbob_eval_scalar_noisy(tmp_path):
    problem = BBOBProblem(
        problem_id=1,
        dim=2,
        noise_strategy=HeteroscedasticNoiseStrategy(0.05),
    )
    x = np.zeros(2)
    val = problem.eval_scalar(x)
    assert isinstance(val, float)


def test_bbob_get_objective_fn(tmp_path):
    clean_problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy())
    noisy_problem = BBOBProblem(
        problem_id=1,
        dim=2,
        noise_strategy=HeteroscedasticNoiseStrategy(0.1),
    )

    clean_fn = clean_problem.get_objective_fn()
    noisy_fn = noisy_problem.get_objective_fn()

    assert clean_fn is clean_problem
    assert noisy_fn is noisy_problem

    assert hasattr(noisy_fn, "lower_bound")
    assert hasattr(noisy_fn, "upper_bound")
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
        noise_strategy=HeteroscedasticNoiseStrategy(0.1),
    )
    assert p_mult.noise_model == "heteroscedastic"
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

    p_awgn = BBOBProblem(problem_id=1, dim=2, noise_strategy=AWGNStrategy(0.1))
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
    assert np.all(clipped_x >= problem.lower_bound)
    assert np.all(clipped_x <= problem.upper_bound)


def test_ioh_logger_records_clean_distance(tmp_path):
    import ioh
    from pathlib import Path
    from evolution.infra.problems import ProblemAnalyzer

    log_dir = tmp_path / "ioh_test"

    problem = BBOBProblem(
        problem_id=1,
        dim=2,
        noise_strategy=HeteroscedasticNoiseStrategy(0.05),
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
    from evolution.infra.problems import ProblemAnalyzer

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
        noise_strategy=HeteroscedasticNoiseStrategy(0.50),
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


def test_bbob_function_enum():
    """Verify BBOBFunction Enum properties, values, and lookup methods."""
    from benchmarking.domain.enums import (
        BBOB_CLASSES_ORDER,
        BBOBFunction,
    )

    # 1. Total Enum members
    assert len(BBOBFunction) == 24

    # 2. Member properties
    f1 = BBOBFunction.F1
    assert f1.problem_id == 1
    assert f1.function_name == "Sphere"
    assert f1.hardness_group == "Separable"
    assert f1.display_name == "Sphere (f1)"
    assert f1.value == (1, "Sphere", "Separable")

    # 3. Lookups
    assert BBOBFunction.from_id(1) is BBOBFunction.F1
    assert BBOBFunction.from_id(24) is BBOBFunction.F24
    assert BBOBFunction.from_id(99) is None

    # 4. Helper classmethods
    assert BBOBFunction.get_name(1) == "Sphere (f1)"
    assert BBOBFunction.get_class(1) == "Separable"
    assert BBOBFunction.get_name(99) == "f99"
    assert BBOBFunction.get_class(99) == "Unknown"

    # 5. Order
    assert len(BBOB_CLASSES_ORDER) == 5


def test_noise_strategy_nrg_reproducibility_and_isolation():
    """Verify that noise strategies using NRG are reproducible, stochastic within runs, and isolated."""
    # 1. Heteroscedastic reproducibility
    s1 = HeteroscedasticNoiseStrategy(noise_std=0.2)
    s1.setup(None, np.array([-5.0]), np.array([5.0]), true_optimum=0.0, seed=123)
    vals1 = [s1.add_noise(10.0) for _ in range(5)]

    s2 = HeteroscedasticNoiseStrategy(noise_std=0.2)
    s2.setup(None, np.array([-5.0]), np.array([5.0]), true_optimum=0.0, seed=123)
    vals2 = [s2.add_noise(10.0) for _ in range(5)]

    assert vals1 == vals2
    # Stochastic within run: subsequent draws must differ
    assert len(set(vals1)) == 5

    # 2. Isolation from global numpy random state
    np.random.seed(999999)
    _ = np.random.normal(0, 1)  # mutate global state
    s3 = HeteroscedasticNoiseStrategy(noise_std=0.2)
    s3.setup(None, np.array([-5.0]), np.array([5.0]), true_optimum=0.0, seed=123)
    vals3 = [s3.add_noise(10.0) for _ in range(5)]
    assert vals3 == vals1

    # 3. AWGN reproducibility and isolation
    awgn1 = AWGNStrategy(noise_std=0.5)
    awgn1.setup(None, None, None, 0.0, seed=42)
    awgn_vals1 = [awgn1.add_noise(2.0) for _ in range(5)]

    awgn2 = AWGNStrategy(noise_std=0.5)
    awgn2.setup(None, None, None, 0.0, seed=42)
    awgn_vals2 = [awgn2.add_noise(2.0) for _ in range(5)]
    assert awgn_vals1 == awgn_vals2
    assert len(set(awgn_vals1)) == 5

    # 4. HomoscedasticAdditive reproducibility
    class MockProblem:
        def __call__(self, x):
            return sum(x)

        def reset(self):
            pass

    mock_prob = MockProblem()
    homo1 = HomoscedasticAdditiveNoiseStrategy(noise_std=0.1, n_samples=20)
    homo1.setup(mock_prob, np.array([-5.0, -5.0]), np.array([5.0, 5.0]), true_optimum=0.0, seed=77)
    homo_vals1 = [homo1.add_noise(5.0) for _ in range(5)]

    homo2 = HomoscedasticAdditiveNoiseStrategy(noise_std=0.1, n_samples=20)
    homo2.setup(mock_prob, np.array([-5.0, -5.0]), np.array([5.0, 5.0]), true_optimum=0.0, seed=77)
    homo_vals2 = [homo2.add_noise(5.0) for _ in range(5)]

    assert homo1.landscape_scale == homo2.landscape_scale
    assert homo_vals1 == homo_vals2


def test_bbob_problem_seed_variation_and_reproducibility():
    """Verify BBOBProblem seed correctly seeds noise strategy RNG."""
    x = np.array([1.0, 1.0])

    # Same seed -> identical noise sequence
    p1 = BBOBProblem(problem_id=1, dim=2, noise_strategy=HeteroscedasticNoiseStrategy(0.2), seed=43)
    p2 = BBOBProblem(problem_id=1, dim=2, noise_strategy=HeteroscedasticNoiseStrategy(0.2), seed=43)
    vals1 = [p1(x) for _ in range(5)]
    vals2 = [p2(x) for _ in range(5)]
    assert vals1 == vals2

    # Different seed -> different noise sequence
    p3 = BBOBProblem(problem_id=1, dim=2, noise_strategy=HeteroscedasticNoiseStrategy(0.2), seed=44)
    vals3 = [p3(x) for _ in range(5)]
    assert vals1 != vals3
