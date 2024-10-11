import datetime
from typing import Any, List

from .entities import ReservationEntity, TableEntity
from .repository_test_helpers import create_restaurant_data, get_database
from .reservation_repo import ReservationRepository
from .restaurant_repository import RestaurantRepository
from .table_repository import TableRepository


def test_reservation_repository_crud():

    repo = ReservationRepository(get_database().managed_session)

    def action(session) -> List[Any]:
        reservation_repo = repo.new_session(session)
        res = reservation_repo.save(
            ReservationEntity(
                reservation_date=datetime.datetime.now(),
                time_from=datetime.time(20, 0, 0),
                time_until=datetime.time(22, 0, 0),
                people=4,
                reservation_name="Test",
                reservation_number="1234",
            )
        )
        reservation_repo.sync()
        assert res.id > 0
        assert res.reservation_name == "Test"
        assert res.reservation_number == "1234"

        # update the entry
        res.reservation_name = "Test_update"
        res.time_until = datetime.time(23, 0, 0)
        res.people = 3
        update = reservation_repo.save(res)

        assert update.reservation_name == "Test_update"
        assert update.time_until == datetime.time(23, 0, 0)
        assert update.people == 3

        result = []
        result.append(update.id)
        return result

    res_id = repo.unit_of_work(action)
    print(res_id)
    find = repo.get_reservation_by_id(res_id)
    assert find is not None
    assert find.reservation_name == "Test_update"
    assert find.time_until == datetime.time(23, 0, 0)

    find = repo.get_reservation_by_number("1234")
    assert find is not None
    assert find.reservation_name == "Test_update"
    assert find.time_until == datetime.time(23, 0, 0)

    assert repo.is_reservation_number_in_use("1234")
    assert not repo.is_reservation_number_in_use("2345")


def test_reservations_for_date_time():
    managed_session = get_database().managed_session
    repo = ReservationRepository(managed_session)
    repo_restaurant = RestaurantRepository(managed_session)
    repo_table = TableRepository(managed_session)

    def action(session) -> List[Any]:
        reservation_repo = repo.new_session(session)
        res_repo = repo_restaurant.new_session(session)
        table_repo = repo_table.new_session(session)

        restaurant = create_restaurant_data()
        restaurant = res_repo.save(restaurant)
        res_repo.sync()

        table = table_repo.save(TableEntity(table_number="Table1", seats=4, restaurant=restaurant))
        table_repo.sync()

        date = datetime.date(2024, 9, 10)

        res = ReservationEntity(
            reservation_date=date,
            time_from=datetime.time(20, 0, 0),
            time_until=datetime.time(22, 0, 0),
            people=4,
            reservation_name="Test1",
            reservation_number="1234",
        )
        res.tables.append(table)
        res = reservation_repo.save(res)

        res = ReservationEntity(
            reservation_date=date,
            time_from=datetime.time(18, 0, 0),
            time_until=datetime.time(19, 0, 0),
            people=4,
            reservation_name="Test2",
            reservation_number="5678",
        )
        res.tables.append(table)
        res = reservation_repo.save(res)

        res = ReservationEntity(
            reservation_date=date,
            time_from=datetime.time(22, 0, 0),
            time_until=datetime.time(23, 0, 0),
            people=4,
            reservation_name="Test3",
            reservation_number="9876",
        )
        res.tables.append(table)
        res = reservation_repo.save(res)

        reservation_repo.sync()

        print(res)

        result = []
        result.append(restaurant.id)
        result.append(table.id)
        return result

    result = repo.unit_of_work(action)
    table_id = result[1]
    restaurant_id = result[0]
    assert table_id > 0 and restaurant_id > 0

    # get all the reservations
    reservations = repo.get_reservation_for_restaurant(restaurant_id)
    assert len(reservations) == 3

    # find me the reservations
    reservations = repo.get_table_reservations_for_date(datetime.date(2024, 9, 10), table_id)
    assert len(reservations) == 3
    assert reservations[0].time_from == datetime.time(18, 0, 0)
    assert reservations[2].time_from == datetime.time(22, 0, 0)

    # different date does not provide reservation
    reservations = repo.get_table_reservations_for_date(datetime.date(2024, 9, 11), table_id)
    assert len(reservations) == 0

    # undefined table results in no reservations
    reservations = repo.get_table_reservations_for_date(datetime.date(2024, 9, 10), -1)
    assert len(reservations) == 0
