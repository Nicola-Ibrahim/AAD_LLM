from enum import StrEnum


class NoiseModelEnum(StrEnum):
    MULTIPLICATIVE = "multiplicative"
    HOMOSCEDASTIC_ADDITIVE = "homoscedastic_additive"
    AWGN = "awgn"
