import pytest

from .repository_test_helpers import create_restaurant_data, get_database
from .restaurant_repository import RestaurantRepository


# this example uses the unit_of_work pattern where all
# actions/changes within the unit_of_work scope are using the same
# session in a transaction context.
# if there is an error during the invocation, a rollback is performed and
# no changes are stored in the database.
def test_restaurant_repository_crud_unit_of_work():

    managed_session = get_database().managed_session
    restaurant_repo = RestaurantRepository(managed_session)

    def work_in_transaction(session):
        # we create a new repository here which uses the
        # session of the unit_of_work scope as a parameter
        repo = restaurant_repo.new_session(session)

        res = create_restaurant_data()
        addr = res.address
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
        assert updated_restaurant.modified is not None

        # update the address
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

    # perform all actions in an atomic
    restaurant_repo.unit_of_work(work_in_transaction)

    all_restaurants = restaurant_repo.get_all_restaurants()
    assert len(all_restaurants) == 1


# show that an error/exception during the unit_of_work scope will rollback
# the whole database interaction.
def test_restaurant_repository_crud_unit_of_work_rollback():

    managed_session = get_database().managed_session
    restaurant_repo = RestaurantRepository(managed_session)

    def work_in_transaction_with_error(session):
        # we create a new repository here which uses the
        # session of the unit_of_work scope as a parameter
        repo = restaurant_repo.new_session(session)

        res = create_restaurant_data()
        repo.save(res)
        repo.sync()

        all_restaurants = repo.get_all_restaurants()
        assert len(all_restaurants) == 1

        raise Exception("error during unit_of_work")

    # the invocation results in an error
    with pytest.raises(Exception):
        restaurant_repo.unit_of_work(work_in_transaction_with_error)

    all_restaurants = restaurant_repo.get_all_restaurants()
    # because of the error, the restaurant was not created
    assert len(all_restaurants) == 0


# this test uses the auto_commit feature. with this approach we do NOT need
# to use the unit_of_work pattern because each operation is performed within
# a transaction.
def test_restaurant_repository_crud_auto_commit():
    managed_session = get_database(auto_commit=True).managed_session
    repo = RestaurantRepository(session_factory=managed_session)

    res = create_restaurant_data()
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
    assert updated_restaurant.modified is not None

    # update the address
    updated_restaurant.address.street += " updated"
    repo.save(updated_restaurant)

    updated_restaurant_address = repo.get_restaurant_by_id(updated_restaurant.id)
    updated_address = updated_restaurant_address.address
    assert "Hauptstraße 1 updated" == updated_address.street

    # lookup the address
    repo.sync()
    addr_lookup = repo.find_address(updated_address)
    assert addr_lookup is not None
    assert updated_address.street == addr_lookup.street
    assert updated_address.city == addr_lookup.city
    assert updated_address.zip == addr_lookup.zip
    assert updated_address.country == addr_lookup.country

    all_restaurants = repo.get_all_restaurants()
    assert len(all_restaurants) == 1
