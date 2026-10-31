"""Focused contract tests for the generic workflow result."""

import json

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from shared.application.result import Error, Result


def test_success_dispatches_only_success_callback() -> None:
    result = Result.success(7)
    called: list[str] = []

    output = result.on(
        lambda value: called.append(f"success:{value}") or value * 2,
        lambda error: called.append("failure") or error.code,
    )

    assert isinstance(result, Result)
    assert result.is_success
    assert output == 14
    assert called == ["success:7"]
    assert result.model_dump() == {"value": 7, "error": None}


def test_failure_dispatches_only_failure_callback_and_keeps_cause_private() -> None:
    cause = ValueError("token sk-secret123")
    result = Result.failure("compute", cause)
    called: list[str] = []

    output = result.on(
        lambda value: called.append("success") or value,
        lambda error: called.append("failure") or error.message,
    )

    assert isinstance(result, Result)
    assert not result.is_success
    assert called == ["failure"]
    assert output == "ValueError: token [REDACTED]"
    assert result.error._original_exception is cause
    assert "_original_exception" not in result.model_dump_json()
    assert json.loads(result.model_dump_json()) == {
        "value": None,
        "error": {
            "operation": "compute",
            "code": "ValueError",
            "message": "ValueError: token [REDACTED]",
            "diagnostic_log": None,
        },
    }


@pytest.mark.parametrize("variant", ["success", "failure"])
def test_callback_exceptions_propagate(variant: str) -> None:
    result = Result.success(1) if variant == "success" else Result.failure("op", ValueError("x"))

    def raise_callback(_value: object) -> None:
        raise RuntimeError("callback failed")

    with pytest.raises(RuntimeError, match="callback failed"):
        result.on(raise_callback, raise_callback)


def test_generic_results_hold_value_and_error() -> None:
    success: Result[list[int]] = Result.success([1, 2])
    failure: Result[list[int]] = Result.failure("read", OSError("gone"))

    assert success.value == [1, 2]
    assert success.error is None
    assert failure.error.code == "OSError"
    assert failure.value is None


def test_empty_and_mixed_results_are_rejected() -> None:
    error = Error(operation="x", code="x", message="x")
    with pytest.raises(ValidationError):
        Result[int]()
    with pytest.raises(ValidationError):
        Result[int](value=1, error=error)
    with pytest.raises(ValidationError):
        Result.success(None)


@pytest.mark.parametrize("value", [0, False, "", [], {}])
def test_falsey_values_are_successful(value: object) -> None:
    result = Result.success(value)
    assert result.is_success
    assert result.on(lambda data: data, lambda error: error) == value


def test_parameterized_result_validates_and_serializes_both_variants() -> None:
    adapter = TypeAdapter(Result[int])
    success = adapter.validate_python({"value": 12})
    failure = adapter.validate_python(
        {"error": {"operation": "read", "code": "OSError", "message": "missing"}}
    )

    assert isinstance(success, Result)
    assert isinstance(failure, Result)
    assert adapter.dump_json(success) == b'{"value":12,"error":null}'
    assert adapter.dump_json(failure) == (
        b'{"value":null,"error":{"operation":"read","code":"OSError","message":"missing","diagnostic_log":null}}'
    )
    with pytest.raises(ValidationError):
        adapter.validate_python({"value": "twelve"})
    with pytest.raises(ValidationError):
        Result[int].success("twelve")


def test_parameterized_result_embeds_in_pydantic_model() -> None:
    class Envelope(BaseModel):
        result: Result[int]

    envelope = Envelope(result={"value": 8})
    assert isinstance(envelope.result, Result)
    assert envelope.model_dump_json() == '{"result":{"value":8,"error":null}}'

    cause = OSError("missing")
    failed_envelope = Envelope(result=Result[int].failure("read", cause))
    assert isinstance(failed_envelope.result, Result)
    assert failed_envelope.result.error._original_exception is cause
    assert failed_envelope.model_dump_json() == (
        '{"result":{"value":null,"error":{"operation":"read","code":"OSError",'
        '"message":"OSError: missing","diagnostic_log":null}}}'
    )


def test_unparameterized_result_factory_accepts_arbitrary_values() -> None:
    result = Result.success(["a", 2])
    assert result.value == ["a", 2]


def test_error_sanitize_and_provider_description_rules() -> None:
    assert Error.sanitize("Bearer abc sk-123") == "[REDACTED] [REDACTED]"

    class ProviderError(Exception):
        __module__ = "httpx"

    assert Error.describe(ProviderError("private body")) == (
        "ProviderError: external provider details omitted"
    )
