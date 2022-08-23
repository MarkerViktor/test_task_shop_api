import uuid

from sqlalchemy.dialects.postgresql import insert

from src import entities
from src.db import user, activation_token
from src.repositories.base import BaseRepository
from src.services.user import UserRepositoryProtocol


class UserRepository(UserRepositoryProtocol, BaseRepository):
    async def create_or_update_activation_token(self, user_id: int, token: uuid.UUID) -> entities.ActivationToken:
        query = insert(activation_token)\
            .values(user_id=user_id, token=token)\
            .on_conflict_do_update(index_elements=[activation_token.c.user_id],
                                   set_={activation_token.c.token: token})\
            .returning(activation_token)
        record = await self.db.fetch_one(query)
        return entities.ActivationToken.from_db(record)

    async def get_user(self, id_: int) -> entities.User | None:
        query = user.select().where(user.c.id == id_)
        record = await self.db.fetch_one(query)
        return entities.User.from_db(record) if record else None

    async def get_activation_token(self, token: uuid.UUID) -> entities.ActivationToken | None:
        query = activation_token.select().where(activation_token.c.token == token)
        record = await self.db.fetch_one(query)
        return entities.ActivationToken.from_db(record) if record else None

    async def delete_activation_token(self, token: uuid.UUID) -> None:
        queue = activation_token.delete().where(activation_token.c.token == token)
        await self.db.execute(queue)

    async def create_user(self, type_: entities.UserType, is_active: bool) -> entities.User:
        query = user.insert().values(type=type_, is_active=is_active).returning(user)
        record = await self.db.fetch_one(query)
        return entities.User.from_db(record)

    async def change_user_is_active(self, user_id: int, is_active: bool) -> None:
        query = user.update().where(user.c.id == user_id).values(is_active=is_active)
        await self.db.execute(query)

    async def get_users(self, limit: int, offset: int) -> list[entities.User]:
        query = user.select().limit(limit).offset(offset)
        records = await self.db.fetch_all(query)
        return [entities.User.from_db(r) for r in records]
