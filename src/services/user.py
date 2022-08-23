import asyncio
import typing
import uuid
from abc import abstractmethod

from src import entities


class UserRepositoryProtocol(typing.Protocol):
    @abstractmethod
    async def change_user_is_active(self, user_id: int, is_active: bool) -> None: ...

    @abstractmethod
    async def create_or_update_activation_token(self, user_id: int, token: uuid.UUID) -> entities.ActivationToken: ...

    @abstractmethod
    async def create_user(self, type_: entities.UserType, is_active: bool) -> entities.User: ...

    @abstractmethod
    async def get_user(self, id_: int) -> entities.User | None: ...

    @abstractmethod
    async def get_users(self, limit: int, offset: int) -> list[entities.User]: ...

    @abstractmethod
    async def get_activation_token(self, token: uuid.UUID) -> entities.ActivationToken | None: ...

    @abstractmethod
    async def delete_activation_token(self, token: uuid.UUID) -> None: ...


class UserService:
    def __init__(self, repository: UserRepositoryProtocol):
        self._repository = repository

    async def get_users(self, limit: int = 10, offset: int = 0) -> list[entities.User]:
        return await self._repository.get_users(limit, offset)

    async def change_user_activation(self, user_id: int, is_active: bool) -> None:
        user = await self._repository.get_user(user_id)
        if user is None:
            raise UserNotExist(user_id)
        await self._repository.change_user_is_active(user_id, is_active)

    async def create_user(self, type_: entities.UserType, is_active: bool = False) -> entities.User:
        return await self._repository.create_user(type_, is_active)

    async def create_activation_token(self, user_id: int) -> entities.ActivationToken:
        user = await self._repository.get_user(user_id)
        if user is None:
            raise UserNotExist(user_id)

        if user.is_active:
            raise UserAlreadyActivated(user_id)

        token = await self._repository.create_or_update_activation_token(user_id, uuid.uuid4())
        return token

    async def activate_user_by_token(self, token: uuid.UUID) -> None:
        activation_token = await self._repository.get_activation_token(token)
        if not activation_token:
            raise InvalidActivationToken(token)

        user = await self._repository.get_user(activation_token.user_id)
        if user.is_active:
            raise UserAlreadyActivated(user.id)

        await asyncio.gather(
            self._repository.change_user_is_active(user.id, is_active=True),
            self._repository.delete_activation_token(activation_token.token)
        )


class UserNotExist(Exception):
    def __init__(self, user_id: int):
        super().__init__(f'User(id={user_id}) not exist.')


class UserAlreadyActivated(Exception):
    def __init__(self, user_id: int):
        super().__init__(f'User(id={user_id}) has already been activated.')


class InvalidActivationToken(Exception):
    def __init__(self, token: uuid.UUID):
        super().__init__(f'Provided token "{token}" is invalid.')
