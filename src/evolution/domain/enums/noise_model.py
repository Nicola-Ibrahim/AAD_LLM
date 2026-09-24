from enum import StrEnum


class NoiseModelEnum(StrEnum):
    HETEROSCEDASTIC = "heteroscedastic"
    HOMOSCEDASTIC_ADDITIVE = "homoscedastic_additive"
    AWGN = "awgn"
    NONE = "none"
