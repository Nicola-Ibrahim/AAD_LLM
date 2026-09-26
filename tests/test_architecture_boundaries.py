"""Guard the intended core-to-infrastructure dependency direction."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "src"


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
