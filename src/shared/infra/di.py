"""Shared Dishka resources; scientific and application code never access containers."""

from collections.abc import Iterator
from contextlib import contextmanager

from dishka import AnyOf, Container, Provider, Scope, make_container, provide
from sqlalchemy.orm import Session, sessionmaker

from shared.domain.interfaces.problem_factory import ProblemFactory
from shared.infra.database import Database
from shared.infra.problems.factory import BBOBProblemFactory


class SharedProvider(Provider):
    problem_factory = provide(
        BBOBProblemFactory, provides=AnyOf[BBOBProblemFactory, ProblemFactory], scope=Scope.APP
    )

    @provide(scope=Scope.APP)
    def database(self) -> Iterator[Database]:
        database = Database()
        try:
            yield database
        finally:
            database.dispose()

    @provide(scope=Scope.APP)
    def session_factory(self, database: Database) -> sessionmaker[Session]:
        return database.session_factory


@contextmanager
def container_scope(
    *providers: Provider,
    context: dict[type, object],
    request_context: dict[type, object],
) -> Iterator[Container]:
    """Own one application container and one notebook/job request scope."""
    root = make_container(SharedProvider(), *providers, context=context)
    try:
        with root(context=request_context) as request:
            yield request
    finally:
        root.close()
