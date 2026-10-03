"""Guard the intended core-to-infrastructure dependency direction."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"


def test_contexts_and_shared_foundation_are_independent() -> None:
    violations: list[str] = []
    for context in ("evolution", "benchmarking", "shared"):
        roots = (
            [ROOT / context]
            if context == "shared"
            else [ROOT / context / "domain", ROOT / context / "application"]
        )
        forbidden = {"evolution", "benchmarking"} - {context}
        for root in roots:
            for path in root.rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        names = [node.module]
                    else:
                        continue
                    if any(name.split(".")[0] in forbidden for name in names):
                        violations.append(str(path.relative_to(ROOT)))
    assert not violations, "Context ownership leaks: " + ", ".join(violations)


def test_benchmarking_backend_does_not_depend_on_presentation() -> None:
    """Figures belong to notebook-owned helpers, not any backend layer."""
    violations: list[str] = []
    for path in (ROOT / "benchmarking").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                if name.startswith(("plotly", "matplotlib", "notebooks")):
                    violations.append(f"{path.relative_to(ROOT)}: {name}")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"write_image", "write_html", "savefig"}
            ):
                violations.append(f"{path.relative_to(ROOT)}: {node.func.attr}()")
    assert not violations, "Backend depends on presentation:\n" + "\n".join(violations)


def test_core_modules_do_not_import_infrastructure_at_module_scope():
    core_roots = [
        ROOT / "evolution/domain",
        ROOT / "evolution/application",
        ROOT / "benchmarking/domain",
        ROOT / "benchmarking/application",
        ROOT / "shared/domain",
    ]
    forbidden_imports = (
        "evolution.infra",
        "benchmarking.infra",
        "shared.infra",
        "shared.config",
    )
    violations = []
    for core_root in core_roots:
        for path in core_root.rglob("*.py"):
            relative = path.relative_to(ROOT)
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                else:
                    continue
                for name in names:
                    if name.startswith(forbidden_imports):
                        violations.append(f"{relative}: {name}")

    assert not violations, "Core modules imported infrastructure:\n" + "\n".join(violations)


def test_domain_modules_do_not_read_configuration_or_files():
    domain_roots = [
        ROOT / "evolution/domain",
        ROOT / "benchmarking/domain",
        ROOT / "shared/domain",
    ]
    forbidden_modules = {"tomllib", "pathlib", "os", "shutil"}
    file_methods = {"read_text", "read_bytes", "is_file", "exists", "open"}
    violations = []
    for root in domain_roots:
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                else:
                    names = []
                for name in names:
                    if name.split(".", 1)[0] in forbidden_modules:
                        violations.append(f"{path}: {name}")
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "open":
                        violations.append(f"{path}: open()")
                    elif isinstance(node.func, ast.Attribute) and node.func.attr in file_methods:
                        violations.append(f"{path}: {node.func.attr}()")
    assert not violations, "Domain performed file/config IO:\n" + "\n".join(violations)


def test_plotting_does_not_calculate_or_load_scientific_results() -> None:
    plotting = ROOT.parent / "notebooks" / "analysis" / "plotting"
    forbidden = (
        "benchmarking.domain.services",
        "benchmarking.application.analysis.data_loader",
        "benchmarking.infra",
        "bootstrap",
    )
    violations = []
    for path in plotting.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            if any(name.startswith(forbidden) for name in names):
                violations.append(path.name)
        scientific_calls = {
            "mean",
            "median",
            "percentile",
            "quantile",
            "compute_attainment_band",
            "compute_trajectory_and_ecdf",
            "load_evaluation_traces",
            "load_provenance_records",
        }
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in scientific_calls
            ):
                violations.append(f"{path.name}: {node.func.attr}")
    assert not violations, "Plotting calculates/loads scientific inputs: " + ", ".join(violations)
