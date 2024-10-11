from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Any, Callable, List, Self

from sqlalchemy.orm import Session

from ..infrastructure.logger import LOG


# https://docs.python.org/3/reference/datamodel.html#context-managers
# found: https://www.pythonmorsels.com/creating-a-context-manager/
class SessionContextManager(AbstractContextManager):
    """Implementation of a context-manager as a wrapper for a session
    The context-manager does not release any resources, but is used to provide
    a uniform usage patter for provides Sessions
    """

    def __init__(self, session: Session):
        self._session = session

    def __enter__(self) -> Session:
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            info = (exc_type, exc_val, exc_tb)
            LOG.error("Exception occurred", exc_info=info)
        return False


class BaseRepository(ABC):

    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], session: Session = None):
        """
        provide a factory to create sessions or pass in an existing session
        """
        self._session_factory = session_factory
        self._session = None
        # a provided session is used if we run in a transaction
        # we still need to do some work to make it behave in a correct way
        if session is not None:
            # we wrap the provided session into a context-manager
            # as a result the derived repositories can work with the sesion
            # in the same way as with the session_factory
            # which is implemented as a context-manager: @see SqlAlchemyDatbase.managed_session
            self._session = SessionContextManager(session)

    def get_session(self) -> AbstractContextManager[Session]:
        # if we have an existing session return it
        # otherwise use the factory to create one
        # the session is implemented as a context-manager / same as the session_factory
        if self._session is not None:
            return self._session
        return self._session_factory()

    def unit_of_work(self, action: Callable[[Session], List[Any]]) -> List[Any]:
        result = None
        with self._session_factory() as session:
            result = action(session)
            session.commit()
        return result

    def sync(self):
        with self.get_session() as session:
            session.flush()

    @abstractmethod
    def new_session(self, session: Session) -> Self:
        """create a new repository with a given session"""
        pass
