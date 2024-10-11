from contextlib import AbstractContextManager, contextmanager
from typing import Callable

from sqlalchemy import create_engine, orm
from sqlalchemy.orm import Session, registry

from ..infrastructure.logger import LOG

mapper_registry = registry()
Base = mapper_registry.generate_base()


class SqlAlchemyDatbase:
    """
    Setup SQLAlchemy with scoped sessions usable for a web-applicaton context
    https://www.sqlalchemy.org/
    """

    def __init__(self, db_url: str, echo: bool) -> None:
        self._engine = create_engine(db_url, echo=echo)

        # https://docs.sqlalchemy.org/en/20/orm/contextual.html
        # create user-defined scoped session
        # the scope in our case is the request by the web-framework
        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            ),
        )

    def create_database(self) -> None:
        Base.metadata.create_all(self._engine)

    def drop_database(self) -> None:
        Base.metadata.drop_all(self._engine)

    # provide a function to access a session via the session_factory
    # https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager
    @contextmanager
    def managed_session(self) -> Callable[..., AbstractContextManager[Session]]:  # type: ignore
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            LOG.exception("Session rollback because of exception")
            session.rollback()
            raise
        finally:
            session.close()
