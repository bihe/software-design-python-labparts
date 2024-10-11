from contextlib import AbstractContextManager
from typing import Callable, List, Self

from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from .entities import MenuEntity


class MenuRepository(BaseRepository):

    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], session: Session = None):
        super().__init__(session_factory=session_factory, session=session)

    def new_session(self, session: Session) -> Self:
        return MenuRepository(session_factory=None, session=session)

    def save(self, menu: MenuEntity) -> MenuEntity:
        menu_to_save = None
        with self.get_session() as session:
            menu_id = menu.id or 0
            menu_to_save = MenuEntity()
            if menu_id > 0:
                menu_to_save = session.get(MenuEntity, id)
                if menu_to_save is None:
                    menu_to_save = MenuEntity()
            else:
                # lookup the menu-entry by name and category
                menu_to_save = (
                    session.query(MenuEntity)
                    .filter(MenuEntity.name == menu.name)
                    .filter(MenuEntity.category == menu.category)
                    .first()
                )
                if menu_to_save is None:
                    menu_to_save = MenuEntity()

            menu_to_save.name = menu.name
            menu_to_save.category = menu.category
            menu_to_save.price = menu.price
            menu_to_save.restaurant = menu.restaurant
            session.add(menu_to_save)
            session.flush()
        return menu_to_save

    def get_menu_by_name(self, name: str, res_id: int) -> MenuEntity:
        menu = None
        with self.get_session() as session:
            menu = (
                session.query(MenuEntity)
                .filter(MenuEntity.name == name)
                .filter(MenuEntity.restaurant_id == res_id)
                .first()
            )
        return menu

    def get_menu_list(self, res_id: int) -> List[MenuEntity]:
        menus: List[MenuEntity] = []
        with self.get_session() as session:
            menus = (
                session.query(MenuEntity)
                .filter(MenuEntity.restaurant_id == res_id)
                .order_by(MenuEntity.category, MenuEntity.name)
                .all()
            )
        return menus
