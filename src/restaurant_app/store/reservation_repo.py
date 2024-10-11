import datetime
from contextlib import AbstractContextManager
from typing import Callable, List, Self

from sqlalchemy import extract
from sqlalchemy.orm import Session, aliased

from .base_repository import BaseRepository
from .entities import ReservationEntity, TableEntity


class ReservationRepository(BaseRepository):

    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], session: Session = None):
        super().__init__(session_factory=session_factory, session=session)

    def new_session(self, session: Session) -> Self:
        return ReservationRepository(session_factory=None, session=session)

    def save(self, reservation: ReservationEntity) -> ReservationEntity:
        with self.get_session() as session:
            reservation_id = reservation.id or 0
            if reservation_id > 0:
                existing = session.get(ReservationEntity, reservation_id)
                if existing is not None:
                    existing.reservation_name = reservation.reservation_name
                    existing.reservation_number = reservation.reservation_number
                    existing.reservation_date = reservation.reservation_date
                    existing.people = reservation.people
                    existing.time_from = reservation.time_from
                    existing.time_until = reservation.time_until
                    session.add(existing)
                    return existing
            else:
                # lookup the reservation by its number
                existing = (
                    session.query(ReservationEntity)
                    .filter(ReservationEntity.reservation_number == reservation.reservation_number)
                    .first()
                )
                if existing is not None:
                    existing.reservation_name = reservation.reservation_name
                    existing.reservation_date = reservation.reservation_date
                    existing.people = reservation.people
                    existing.time_from = reservation.time_from
                    existing.time_until = reservation.time_until
                    session.add(existing)
                    return existing

            # new or not found
            session.add(reservation)
            session.flush()
        return reservation

    def delete(self, reservation_id: int):
        with self.get_session() as session:
            reservation = session.get(ReservationEntity, reservation_id)
            if reservation is not None:
                session.delete(reservation)

    def get_reservation_by_id(self, id: int) -> ReservationEntity:
        with self.get_session() as session:
            return session.get(ReservationEntity, id)

    def get_reservation_for_restaurant(self, restaurant_id: int) -> ReservationEntity:
        with self.get_session() as session:
            return (
                session.query(ReservationEntity)
                .join(TableEntity, ReservationEntity.tables)
                .where(TableEntity.restaurant_id == restaurant_id)
                .order_by(ReservationEntity.reservation_date.asc())
                .order_by(ReservationEntity.time_from.asc())
                .order_by(TableEntity.table_number)
                .all()
            )

    def get_reservation_by_number(self, number: int) -> ReservationEntity:
        with self.get_session() as session:
            return session.query(ReservationEntity).filter(ReservationEntity.reservation_number == number).first()

    def is_reservation_number_in_use(self, number: str) -> bool:
        with self.get_session() as session:
            if (
                session.query(ReservationEntity.reservation_number)
                .filter(ReservationEntity.reservation_number == number)
                .scalar()
                is None
            ):
                return False
            return True

    def get_table_reservations_for_date(self, date: datetime.date, table_id: int) -> List[ReservationEntity]:
        """determine if there is a reservation for the given date/time and the table"""
        with self.get_session() as session:
            table_alias = aliased(TableEntity)

            reservations = (
                session.query(ReservationEntity)
                .join(table_alias, ReservationEntity.tables)
                .where(table_alias.id == table_id)
                .where(
                    # https://github.com/sqlalchemy/sqlalchemy/discussions/8067
                    (extract("year", ReservationEntity.reservation_date) == date.year)
                    & (extract("month", ReservationEntity.reservation_date) == date.month)
                    & (extract("day", ReservationEntity.reservation_date) == date.day)
                )
                .order_by(ReservationEntity.time_from.asc())
            ).all()
            return reservations
