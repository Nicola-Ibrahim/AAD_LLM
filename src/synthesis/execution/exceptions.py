from domain.exceptions import BaseDomainException


class AlgorithmExecutionException(BaseDomainException):
    """Base exception for all candidate algorithm execution failures."""

    pass


class AlgorithmTimeoutException(AlgorithmExecutionException):
    """Raised when candidate algorithm execution exceeds wall-clock execution budget."""

    pass


class CodeValidationException(AlgorithmExecutionException):
    """Raised when LLM-generated code fails structural, syntax, or compilation validation."""

    pass
