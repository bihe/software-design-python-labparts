from typing import Any, List

from .entities import MenuEntity
from .menu_repository import MenuRepository
from .repository_test_helpers import create_restaurant_data, get_database
from .restaurant_repository import RestaurantRepository


def test_menu_repository_crud():
    managed_session = get_database().managed_session
    repo = MenuRepository(managed_session)
    repo_restaurant = RestaurantRepository(managed_session)

    def action(session) -> List[Any]:
        res_repo = repo_restaurant.new_session(session)
        menu_repo = repo.new_session(session)

        res = create_restaurant_data()
        res = res_repo.save(res)
        res_repo.sync()

        menu = MenuEntity(name="MenuEntry1", category="Category1", price=14.50, restaurant=res)
        menu = menu_repo.save(menu)
        res_repo.sync()

        menu_lookup = menu_repo.get_menu_by_name("MenuEntry1", res.id)
        assert menu_lookup is not None
        assert menu_lookup.category == menu.category
        assert menu_lookup.price == menu.price

        menus = menu_repo.get_menu_list(res.id)
        assert len(menus) == 1
        result = []
        result.append(res.id)
        return result

    result = repo.unit_of_work(action)
    menus = repo.get_menu_list(result[0])
    assert len(menus) == 1
