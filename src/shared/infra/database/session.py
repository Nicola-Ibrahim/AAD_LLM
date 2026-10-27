"""Translate persistence failures without changing session/transaction semantics."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from shared.application.errors import StorageError


@contextmanager
def session_scope(
    factory: sessionmaker[Session], operation: str, *, transaction: bool = False
) -> Iterator[Session]:
    try:
        with factory.begin() if transaction else factory() as session:
            yield session
    except SQLAlchemyError as error:
        raise StorageError(f"Database operation failed: {operation}") from error
