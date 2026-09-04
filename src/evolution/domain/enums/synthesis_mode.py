from enum import StrEnum


class SynthesisMode(StrEnum):
    CLEAN = "clean"
    NOISY = "noisy"
    IMPLICIT = "implicit"
