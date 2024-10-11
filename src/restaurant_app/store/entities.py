import datetime
from dataclasses import dataclass
from typing import List

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

relation_menu_order = Table(
    "REL_MENU_ORDER",
    Base.metadata,
    Column("menu_id", ForeignKey("MENU.id"), primary_key=True),
    Column("order_id", ForeignKey("TABLE_ORDER.id"), primary_key=True),
)

relation_table_reservation = Table(
    "REL_TABLE_RESERVATION",
    Base.metadata,
    Column("table_id", ForeignKey("GUEST_TABLE.id"), primary_key=True),
    Column("reservation_id", ForeignKey("RESERVATION.id"), primary_key=True),
)


def current_datetime() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class BaseEntity(Base):
    """abstract base-class defining common columns for all entities"""

    __abstract__ = True

    # https://datawookie.dev/blog/2023/05/column-order-inheritance-declarative-base/
    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True, nullable=False, unique=True, sort_order=-1
    )
    created: Mapped[datetime.datetime] = mapped_column(nullable=False, default=current_datetime)
    modified: Mapped[datetime.datetime] = mapped_column(nullable=True, onupdate=current_datetime)


@dataclass
class RestaurantEntity(BaseEntity):
    __tablename__ = "RESTAURANT"

    name: Mapped[str] = mapped_column("name", String(255))
    open_from: Mapped[datetime.time] = mapped_column("open_from")
    open_until: Mapped[datetime.time] = mapped_column("open_until")
    # a deliminated list of week-days the restaurant is open
    open_days: Mapped[str] = mapped_column("open_days", String(255))

    address_id: Mapped[int] = mapped_column(ForeignKey("ADDRESS.id"))
    # as those tables form the "basic-data" or "master-data" of a restaurant
    # they are fetched as well when a restaurant is queried
    # if the option for lazy is not defined, SqlAlchemy can raise an error if
    # objects are accessed outstide of a SqlAlchemy Session
    # @see https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
    address: Mapped["AddressEntity"] = relationship(back_populates="restaurants", lazy="joined")
    menus: Mapped[List["MenuEntity"]] = relationship(
        back_populates="restaurant", lazy="joined", cascade="all, delete-orphan"
    )
    tables: Mapped[List["TableEntity"]] = relationship(
        back_populates="restaurant", lazy="joined", cascade="all, delete-orphan"
    )


@dataclass
class AddressEntity(BaseEntity):
    __tablename__ = "ADDRESS"

    street: Mapped[str] = mapped_column("street", String(255))
    city: Mapped[str] = mapped_column("city", String(255))
    zip: Mapped[str] = mapped_column("zip", String(25))
    country: Mapped[str] = mapped_column("country", String(2))

    restaurants: Mapped[List["RestaurantEntity"]] = relationship(back_populates="address")


@dataclass
class MenuEntity(BaseEntity):
    __tablename__ = "MENU"

    name: Mapped[str] = mapped_column("name", String(255))
    price: Mapped[float] = mapped_column("price")
    category: Mapped[str] = mapped_column("category", String(255))

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("RESTAURANT.id"))
    restaurant: Mapped["RestaurantEntity"] = relationship()

    orders: Mapped[List["OrderEntity"]] = relationship(secondary=relation_menu_order, back_populates="menus")


@dataclass
class TableEntity(BaseEntity):
    __tablename__ = "GUEST_TABLE"

    table_number: Mapped[str] = mapped_column("table_number", String(255))
    seats: Mapped[int] = mapped_column("seats")

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("RESTAURANT.id"))
    restaurant: Mapped[RestaurantEntity] = relationship(back_populates="tables")

    reservations: Mapped[List["ReservationEntity"]] = relationship(
        secondary=relation_table_reservation, back_populates="tables"
    )

    orders: Mapped[List["OrderEntity"]] = relationship(back_populates="table")


@dataclass
class ReservationEntity(BaseEntity):
    __tablename__ = "RESERVATION"

    reservation_date: Mapped[datetime.datetime] = mapped_column("reservation_date")
    time_from: Mapped[datetime.time] = mapped_column("time_from")
    time_until: Mapped[datetime.time] = mapped_column("time_until")
    people: Mapped[int] = mapped_column("people")
    reservation_name: Mapped[str] = mapped_column("reservation_name", String(255))
    reservation_number: Mapped[str] = mapped_column("reservation_number", String(10), unique=True)

    tables: Mapped[List["TableEntity"]] = relationship(
        secondary=relation_table_reservation, back_populates="reservations", lazy="joined"
    )


@dataclass
class OrderEntity(BaseEntity):
    __tablename__ = "TABLE_ORDER"

    total: Mapped[float] = mapped_column("total")
    waiter: Mapped[str] = mapped_column("waiter", String(255))

    table_id: Mapped[int] = mapped_column(ForeignKey("GUEST_TABLE.id"))
    table: Mapped["TableEntity"] = relationship(back_populates="orders")

    menus: Mapped[List["MenuEntity"]] = relationship(secondary=relation_menu_order, back_populates="orders")
