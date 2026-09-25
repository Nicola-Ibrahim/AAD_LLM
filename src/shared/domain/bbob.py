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

    # Established synthesis-side names for the same 24 scientific functions.
    SPHERE = F1
    ELLIPSOIDAL = F2
    RASTRIGIN_SEPARABLE = F3
    BUECHE_RASTRIGIN = F4
    LINEAR_SLOPE = F5
    ATTRACTIVE_SECTOR = F6
    STEP_ELLIPSOIDAL = F7
    ROSENBROCK = F8
    ROSENBROCK_ROTATED = F9
    ELLIPSOIDAL_HIGH_COND = F10
    DISCUS = F11
    BENT_CIGAR = F12
    SHARP_RIDGE = F13
    DIFFERENT_POWERS = F14
    RASTRIGIN = F15
    WEIERSTRASS = F16
    SCHAFFERS_F7 = F17
    SCHAFFERS_F7_ILL_COND = F18
    GRIEWANK_ROSENBROCK = F19
    SCHWEFEL = F20
    GALLAGHER_101 = F21
    GALLAGHER_21 = F22
    KATUSHA = F23
    LUNACEK = F24

    def __int__(self) -> int:
        return self.problem_id

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

    @property
    def short_name(self) -> str:
        return self.function_name.split()[0]

    @classmethod
    def get_short_name(cls, problem_id: int) -> str:
        func = cls.from_id(problem_id)
        return cls.get_display_name(problem_id).split()[0] if func else f"f{problem_id}"

    @classmethod
    def get_display_name(cls, problem_id: int) -> str:
        func = cls.from_id(problem_id)
        return SYNTHESIS_DISPLAY_NAMES[problem_id] if func else f"Function {problem_id}"


SYNTHESIS_DISPLAY_NAMES = {
    1: "Sphere (Separable)",
    2: "Ellipsoidal (Separable)",
    3: "Rastrigin (Separable)",
    4: "Büche-Rastrigin",
    5: "Linear Slope",
    6: "Attractive Sector",
    7: "Step Ellipsoidal",
    8: "Rosenbrock (Moderate)",
    9: "Rosenbrock (Rotated)",
    10: "Ellipsoidal (High Conditioning)",
    11: "Discus (Ill-conditioned)",
    12: "Bent Cigar",
    13: "Sharp Ridge",
    14: "Different Powers",
    15: "Rastrigin (Multi-modal)",
    16: "Weierstrass",
    17: "Schaffers F7",
    18: "Schaffers F7 (Ill-conditioned)",
    19: "Griewank-Rosenbrock",
    20: "Schwefel",
    21: "Gallagher 101 (Deceptive)",
    22: "Gallagher 21",
    23: "Katsuura",
    24: "Lunacek bi-Rastrigin",
}


BBOB_CLASSES_ORDER = [
    "Separable",
    "Low Conditioning",
    "High Conditioning",
    "Multi-Modal (Global)",
    "Multi-Modal (Weak)",
]
