from contextlib import AbstractContextManager, contextmanager
from typing import Callable

from sqlalchemy import create_engine, orm
from sqlalchemy.orm import Session, registry

from ..infrastructure.logger import LOG

mapper_registry = registry()
Base = mapper_registry.generate_base()


class SqlAlchemyDatabase:
    """
    Setup SQLAlchemy with scoped sessions usable for a web-application context
    https://www.sqlalchemy.org/
    """

    def __init__(self, db_url: str, echo: bool = False, auto_commit: bool = False) -> None:
        self._engine = create_engine(db_url, echo=echo)
        # if auto_commit is set to True, every session invocation of
        # managed_session will start and complete a transaction automatically
        # without the need to explicitly start one.
        self._auto_commit = auto_commit

        # https://docs.sqlalchemy.org/en/20/orm/contextual.html
        # create user-defined scoped session
        # the scope in our case is the request by the web-framework (thread)
        # the sessionmaker is a function which provides a new Session when it is called
        self._session_factory = orm.scoped_session(
            # the sessionmaker provides a function to create a new Session
            # https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.sessionmaker
            orm.sessionmaker(
                autocommit=False,  # we cannot set autocommit to True, this leads to an error in SqlAlchemy
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
        """
        provides a function to acquire a new Session to work with
        """
        session: Session = self._session_factory()
        try:
            if self._auto_commit:
                session.begin()
                session.expire_on_commit = False

            # yield returns a generator function which can be executed
            # yield: https://sentry.io/answers/python-yield-keyword/
            yield session

            if self._auto_commit:
                session.commit()
        except Exception:
            LOG.exception("Session rollback because of exception")
            session.rollback()
            raise
        finally:
            session.close()
