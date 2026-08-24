"""BBOB benchmark taxonomy, function metadata, and landscape hardness classification.

Single canonical source of truth for all 24 standard BBOB functions defined by Hansen et al. (2009).
"""

from typing import Final

BBOB_METADATA: Final[dict[int, tuple[str, str]]] = {
    1:  ("Sphere", "Separable"),
    2:  ("Ellipsoidal", "Separable"),
    3:  ("Rastrigin", "Separable"),
    4:  ("Buche-Rastrigin", "Separable"),
    5:  ("Linear Slope", "Separable"),
    6:  ("Attractive Sector", "Low Conditioning"),
    7:  ("Step Ellipsoidal", "Low Conditioning"),
    8:  ("Rosenbrock", "Low Conditioning"),
    9:  ("Rosenbrock Rotated", "Low Conditioning"),
    10: ("Ellipsoidal High-Cond", "High Conditioning"),
    11: ("Discus", "High Conditioning"),
    12: ("Bent Cigar", "High Conditioning"),
    13: ("Sharp Ridge", "High Conditioning"),
    14: ("Different Powers", "High Conditioning"),
    15: ("Rastrigin Multi-Modal", "Multi-Modal (Global)"),
    16: ("Weierstrass", "Multi-Modal (Global)"),
    17: ("Schaffers F7", "Multi-Modal (Global)"),
    18: ("Schaffers F7 Ill-Cond", "Multi-Modal (Global)"),
    19: ("Griewank-Rosenbrock", "Multi-Modal (Global)"),
    20: ("Schwefel", "Multi-Modal (Weak)"),
    21: ("Gallagher 101 Peaks", "Multi-Modal (Weak)"),
    22: ("Gallagher 21 Peaks", "Multi-Modal (Weak)"),
    23: ("Katsuura", "Multi-Modal (Weak)"),
    24: ("Lunacek Bi-Rastrigin", "Multi-Modal (Weak)"),
}

BBOB_CLASSES_ORDER: Final[list[str]] = [
    "Separable",
    "Low Conditioning",
    "High Conditioning",
    "Multi-Modal (Global)",
    "Multi-Modal (Weak)",
]


def get_bbob_name(p_id: int) -> str:
    """Return the formatted benchmark function name e.g., 'Sphere (f1)'."""
    name, _ = BBOB_METADATA.get(p_id, (f"Function {p_id}", "General"))
    return f"{name} (f{p_id})"


def get_bbob_class(p_id: int) -> str:
    """Return the official BBOB landscape hardness group class."""
    _, cls = BBOB_METADATA.get(p_id, (f"Function {p_id}", "General"))
    return cls


BBOB_NAMES: Final[dict[int, str]] = {p: get_bbob_name(p) for p in range(1, 25)}
BBOB_CLASSES: Final[dict[int, str]] = {p: get_bbob_class(p) for p in range(1, 25)}
