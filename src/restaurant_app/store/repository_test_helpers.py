from datetime import time

from .database import SqlAlchemyDatabase
from .entities import AddressEntity, RestaurantEntity


def create_restaurant_data() -> RestaurantEntity:
    addr = AddressEntity(city="Salzburg", street="Hauptstraße 1", zip=5020, country="AT")
    res = RestaurantEntity(
        name="Test-Restaurant",
        open_from=time(10, 0, 0),
        open_until=time(22, 0, 0),
        open_days="MONDAY;TUESDAY",
        address=addr,
    )
    return res


def get_database():
    db = SqlAlchemyDatabase("sqlite://", False)
    db.create_database()
    return db
