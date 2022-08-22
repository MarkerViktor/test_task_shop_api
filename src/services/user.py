import typing
from abc import abstractmethod

from src import entities


class UserRepositoryProtocol(typing.Protocol):
    @abstractmethod
    async def get_users(self, limit: int, offset: int) -> list[entities.User]: ...

    @abstractmethod
    async def check_user_exist(self, user_id: int) -> bool: ...

    @abstractmethod
    async def change_user_is_activated(self, user_id: int, is_active: bool) -> None: ...


class UserNotExist(Exception):
    pass

class UserService:
    def __init__(self, user_repository: UserRepositoryProtocol):
        self.repository = user_repository

    async def get_users(self, limit: int = 10, offset: int = 0) -> list[entities.User]:
        return await self.repository.get_users(limit, offset)

    async def change_user_activation(self, user_id: int, is_active: bool) -> None:
        if not await self.repository.check_user_exist(user_id):
            raise UserNotExist(f'User(id={user_id}) not exist.')
        await self.repository.change_user_is_activated(user_id, is_active)
