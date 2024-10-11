from contextlib import AbstractContextManager
from typing import Callable, List, Self

from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from .entities import AddressEntity, RestaurantEntity


class RestaurantRepository(BaseRepository):

    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], session: Session = None):
        super().__init__(session_factory=session_factory, session=session)

    def new_session(self, session: Session) -> Self:
        return RestaurantRepository(session_factory=None, session=session)

    def get_restaurant_by_id(self, id: int) -> RestaurantEntity:
        with self.get_session() as session:
            return session.get(RestaurantEntity, id)

    def find_restaurants_by_name_and_address(self, name: str, addr: AddressEntity) -> RestaurantEntity:
        res_lookup = None
        with self.get_session() as session:
            addr_lookup = self.find_address(addr)
            if addr_lookup is None:
                return None
            res_lookup = (
                session.query(RestaurantEntity)
                .filter(RestaurantEntity.name == name)
                .filter(RestaurantEntity.address_id == addr_lookup.id)
                .first()
            )
        return res_lookup

    def get_all_restaurants(self) -> List[RestaurantEntity]:
        restaurants: List[RestaurantEntity] = []
        with self.get_session() as session:
            restaurants = session.query(RestaurantEntity).all()
        return restaurants

    def find_address(self, address: AddressEntity) -> AddressEntity:
        """use the fields in the supplied model to lookup the address"""
        found_address = None
        with self.get_session() as session:
            found_address = (
                session.query(AddressEntity)
                .filter(AddressEntity.street == address.street)
                .filter(AddressEntity.city == address.city)
                .filter(AddressEntity.zip == address.zip)
                .filter(AddressEntity.country == address.country)
                .first()
            )
        return found_address

    def save(self, restaurant: RestaurantEntity) -> RestaurantEntity:
        with self.get_session() as session:
            restaurant_id = restaurant.id or 0
            if restaurant_id > 0:
                existing = session.get(RestaurantEntity, restaurant_id)
                if existing is not None:
                    existing.name = restaurant.name
                    existing.open_from = restaurant.open_from
                    existing.open_until = restaurant.open_until
                    existing.open_days = restaurant.open_days
                    # existing.modified = datetime.datetime.now(datetime.UTC)
                    existing.address = self._handle_address(restaurant.address, session)
                    session.add(existing)
                    return existing

            # new or not found
            restaurant.address = self._handle_address(restaurant.address, session)
            session.add(restaurant)
            session.flush()
        return restaurant

    def _handle_address(self, address: AddressEntity, session: Session) -> AddressEntity:
        addr = address
        # an id was supplied, load the object from the db
        if address.id is not None:
            addr = session.get(AddressEntity, address.id)
            if addr is None:
                # could not load the address from the database
                # we just overwrite the address with a new object
                addr = address
                addr.id = None  # overwrite the id
        else:
            # no existing reference to address
            addr = address
            addr.id = None  # overwrite the id
        session.add(addr)
        return addr
