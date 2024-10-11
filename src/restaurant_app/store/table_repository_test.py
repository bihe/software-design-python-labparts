from typing import Any, List

from .entities import TableEntity
from .repository_test_helpers import create_restaurant_data, get_database
from .restaurant_repository import RestaurantRepository
from .table_repository import TableRepository


def test_table_repository_crud():
    managed_session = get_database().managed_session
    repo = TableRepository(managed_session)
    restaurant_repo = RestaurantRepository(managed_session)

    def action(session) -> List[Any]:
        res_repo = restaurant_repo.new_session(session)
        table_repo = repo.new_session(session)

        res = create_restaurant_data()
        res = res_repo.save(res)
        res_repo.sync()

        table_repo.save(TableEntity(table_number="Table1", seats=4, restaurant=res))
        table_repo.save(TableEntity(table_number="Table2", seats=6, restaurant=res))

        result = []
        result.append(res.id)
        return result

    result = repo.unit_of_work(action)
    restaurant_id = result[0]
    tables = repo.get_tables_for_restaurant(restaurant_id)
    assert len(tables) == 2
    assert tables[0].table_number == "Table1" and tables[0].seats == 4
    assert tables[1].table_number == "Table2" and tables[1].seats == 6

    table1 = repo.get_table_by_id(tables[0].id)
    assert table1.table_number == "Table1" and table1.seats == 4

    tables_with_capacity = repo.get_tables_with_capacity(3, restaurant_id)
    assert len(tables_with_capacity) == 2

    tables_with_capacity = repo.get_tables_with_capacity(4, restaurant_id)
    assert len(tables_with_capacity) == 2

    tables_with_capacity = repo.get_tables_with_capacity(5, restaurant_id)
    assert len(tables_with_capacity) == 1

    tables_with_capacity = repo.get_tables_with_capacity(6, restaurant_id)
    assert len(tables_with_capacity) == 1

    tables_with_capacity = repo.get_tables_with_capacity(7, restaurant_id)
    assert len(tables_with_capacity) == 0
