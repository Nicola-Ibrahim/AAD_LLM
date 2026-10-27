"""Solver origin used by scientific comparisons, independent of display names."""

from enum import StrEnum


class SolverKind(StrEnum):
    CLASSICAL = "classical"
    GENERATED = "generated"
