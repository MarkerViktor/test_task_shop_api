from .base import BaseRepository
from src.services.user import UserRepositoryProtocol
from src import entities
from src.db import user


class UserRepository(UserRepositoryProtocol, BaseRepository):
    async def change_user_is_activated(self, user_id: int, is_active: bool) -> None:
        query = user.update().where(user.c.id == user_id).values(is_active=is_active)
        await self.db.execute(query)

    async def check_user_exist(self, user_id: int) -> bool:
        query = user.select().where(user.c.id == user_id)
        record = await self.db.fetch_one(query)
        return record is not None

    async def get_users(self, limit: int, offset: int) -> list[entities.User]:
        query = user.select().limit(limit).offset(offset)
        records = await self.db.fetch_all(query)
        return [entities.User.from_db(r) for r in records]
