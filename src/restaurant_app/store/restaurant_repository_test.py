from .repository_test_helpers import create_restaurant_data, get_database
from .restaurant_repository import RestaurantRepository


def test_restaurant_repository_crud():

    managed_session = get_database().managed_session
    restaurant_repo = RestaurantRepository(managed_session)

    def action(session):
        res = create_restaurant_data()
        addr = res.address
        repo = restaurant_repo.new_session(session)
        saved = repo.save(res)
        repo.sync()

        all_restaurants = repo.get_all_restaurants()
        assert len(all_restaurants) == 1

        find_restaurant = repo.get_restaurant_by_id(saved.id)
        assert find_restaurant.name == res.name
        assert find_restaurant.modified is None

        # update the name of the restaurant
        find_restaurant.name += " updated"
        repo.save(find_restaurant)
        repo.sync()

        updated_restaurant = repo.get_restaurant_by_id(find_restaurant.id)
        assert "Test-Restaurant updated" == updated_restaurant.name
        assert find_restaurant.modified is not None

        # updat the address
        updated_restaurant.address.street += " updated"
        repo.save(updated_restaurant)

        updated_address = repo.get_restaurant_by_id(updated_restaurant.id)
        assert "Hauptstraße 1 updated" == updated_address.address.street

        # lookup the address
        repo.sync()  # want to "read" within the transaction
        addr_lookup = repo.find_address(addr)
        assert addr_lookup is not None
        assert addr.street == addr_lookup.street
        assert addr.city == addr_lookup.city
        assert addr.zip == addr_lookup.zip
        assert addr.country == addr_lookup.country

    restaurant_repo.unit_of_work(action)

    all_restaurants = restaurant_repo.get_all_restaurants()
    assert len(all_restaurants) == 1
