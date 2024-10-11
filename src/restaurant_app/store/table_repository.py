from contextlib import AbstractContextManager
from typing import Callable, List, Self

from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from .entities import TableEntity


class TableRepository(BaseRepository):

    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], session: Session = None):
        super().__init__(session_factory=session_factory, session=session)

    def new_session(self, session: Session) -> Self:
        return TableRepository(session_factory=None, session=session)

    def get_table_by_id(self, id: int) -> TableEntity:
        with self.get_session() as session:
            return session.get(TableEntity, id)

    def get_tables_for_restaurant(self, restaurant_id: int) -> List[TableEntity]:
        with self.get_session() as session:
            return session.query(TableEntity).filter(TableEntity.restaurant_id == restaurant_id).all()

    def get_tables_with_capacity(self, capacity: int, restaurant_id: int) -> List[TableEntity]:
        if capacity <= 0:
            return []
        with self.get_session() as session:
            tables = (
                session.query(TableEntity)
                .filter(TableEntity.restaurant_id == restaurant_id)
                .filter(TableEntity.seats >= capacity)
                .all()
            )
            if tables is None:
                tables = []
            return tables

    def save(self, table: TableEntity) -> TableEntity:
        with self.get_session() as session:
            table_id = table.id or 0
            if table_id > 0:
                existing = session.get(TableEntity, table_id)
                if existing is not None:
                    existing.table_number = table.table_number
                    existing.retaurant = table.restaurant
                    session.add(existing)
                    return existing
            else:
                # lookup the table by its number
                existing = (
                    session.query(TableEntity)
                    .filter(TableEntity.table_number == table.table_number)
                    .filter(TableEntity.restaurant_id == table.restaurant.id)
                    .first()
                )
                if existing is not None:
                    existing.table_number = table.table_number
                    session.add(existing)
                    return existing

            # new or not found
            session.add(table)
            session.flush()
        return table
