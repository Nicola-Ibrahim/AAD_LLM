"""BBOB benchmark taxonomy, Enum definitions, and function metadata (Hansen et al., 2009)."""

from enum import Enum


class BBOBFunction(Enum):
    """Canonical 24 BBOB benchmark functions: (problem_id, function_name, hardness_group)."""

    F1 = (1, "Sphere", "Separable")
    F2 = (2, "Ellipsoidal", "Separable")
    F3 = (3, "Rastrigin", "Separable")
    F4 = (4, "Buche-Rastrigin", "Separable")
    F5 = (5, "Linear Slope", "Separable")
    F6 = (6, "Attractive Sector", "Low Conditioning")
    F7 = (7, "Step Ellipsoidal", "Low Conditioning")
    F8 = (8, "Rosenbrock", "Low Conditioning")
    F9 = (9, "Rosenbrock Rotated", "Low Conditioning")
    F10 = (10, "Ellipsoidal High-Cond", "High Conditioning")
    F11 = (11, "Discus", "High Conditioning")
    F12 = (12, "Bent Cigar", "High Conditioning")
    F13 = (13, "Sharp Ridge", "High Conditioning")
    F14 = (14, "Different Powers", "High Conditioning")
    F15 = (15, "Rastrigin Multi-Modal", "Multi-Modal (Global)")
    F16 = (16, "Weierstrass", "Multi-Modal (Global)")
    F17 = (17, "Schaffers F7", "Multi-Modal (Global)")
    F18 = (18, "Schaffers F7 Ill-Cond", "Multi-Modal (Global)")
    F19 = (19, "Griewank-Rosenbrock", "Multi-Modal (Global)")
    F20 = (20, "Schwefel", "Multi-Modal (Weak)")
    F21 = (21, "Gallagher 101 Peaks", "Multi-Modal (Weak)")
    F22 = (22, "Gallagher 21 Peaks", "Multi-Modal (Weak)")
    F23 = (23, "Katsuura", "Multi-Modal (Weak)")
    F24 = (24, "Lunacek Bi-Rastrigin", "Multi-Modal (Weak)")

    @property
    def problem_id(self) -> int:
        """The 1-indexed BBOB function number."""
        return self.value[0]

    @property
    def function_name(self) -> str:
        """Official name of the benchmark function."""
        return self.value[1]

    @property
    def hardness_group(self) -> str:
        """Landscape difficulty classification."""
        return self.value[2]

    @property
    def display_name(self) -> str:
        """Formatted label, e.g. 'Sphere (f1)'."""
        return f"{self.function_name} (f{self.problem_id})"

    @classmethod
    def from_id(cls, p_id: int) -> "BBOBFunction | None":
        """Look up enum member by integer problem ID."""
        for member in cls:
            if member.problem_id == p_id:
                return member
        return None

    @classmethod
    def get_name(cls, p_id: int) -> str:
        """Return formatted function name e.g. 'Sphere (f1)'."""
        func = cls.from_id(p_id)
        return func.display_name if func else f"f{p_id}"

    @classmethod
    def get_class(cls, p_id: int) -> str:
        """Return landscape hardness group e.g. 'Separable'."""
        func = cls.from_id(p_id)
        return func.hardness_group if func else "Unknown"


BBOB_CLASSES_ORDER = [
    "Separable",
    "Low Conditioning",
    "High Conditioning",
    "Multi-Modal (Global)",
    "Multi-Modal (Weak)",
]
