"""Guard the intended core-to-infrastructure dependency direction."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "src"


def test_core_modules_do_not_import_infrastructure_at_module_scope():
    core_roots = [
        ROOT / "evolution/domain",
        ROOT / "evolution/application",
        ROOT / "benchmarking/domain",
        ROOT / "benchmarking/application",
    ]
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
                    if name.startswith(("evolution.infra", "benchmarking.infra")):
                        violations.append(f"{relative}: {name}")

    assert not violations, "Core modules imported infrastructure:\n" + "\n".join(violations)
