"""Domain Enum for BBOB Benchmark Functions."""

from enum import IntEnum


class BBOBFunction(IntEnum):
    """BBOB continuous test suite standard function IDs and metadata."""

    SPHERE = 1
    ELLIPSOIDAL = 2
    RASTRIGIN_SEPARABLE = 3
    BUECHE_RASTRIGIN = 4
    LINEAR_SLOPE = 5
    ATTRACTIVE_SECTOR = 6
    STEP_ELLIPSOIDAL = 7
    ROSENBROCK = 8
    ROSENBROCK_ROTATED = 9
    ELLIPSOIDAL_HIGH_COND = 10
    DISCUS = 11
    BENT_CIGAR = 12
    SHARP_RIDGE = 13
    DIFFERENT_POWERS = 14
    RASTRIGIN = 15
    WEIERSTRASS = 16
    SCHAFFERS_F7 = 17
    SCHAFFERS_F7_ILL_COND = 18
    GRIEWANK_ROSENBROCK = 19
    SCHWEFEL = 20
    GALLAGHER_101 = 21
    GALLAGHER_21 = 22
    KATUSHA = 23
    LUNACEK = 24

    @property
    def display_name(self) -> str:
        """Full descriptive name with mathematical property."""
        names = {
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
        return names.get(self.value, f"Function {self.value}")

    @property
    def short_name(self) -> str:
        """Short identifier for compact table representations."""
        return self.display_name.split()[0]

    @classmethod
    def get_display_name(cls, problem_id: int) -> str:
        """Helper to safely get display name for any integer ID."""
        try:
            return cls(problem_id).display_name
        except ValueError:
            return f"Function {problem_id}"

    @classmethod
    def get_short_name(cls, problem_id: int) -> str:
        """Helper to safely get short name for any integer ID."""
        try:
            return cls(problem_id).short_name
        except ValueError:
            return f"f{problem_id}"
