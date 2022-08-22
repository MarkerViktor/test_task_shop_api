from src import entities
from src.db import auth_credentials
from src.repositories.base import BaseRepository
from src.services.auth import AuthRepositoryProtocol


class AuthRepository(AuthRepositoryProtocol, BaseRepository):
    async def get_credentials_by_login(self, login: str) -> entities.AuthCredentials | None:
        query = auth_credentials.select().where(auth_credentials.c.login == login)
        record = await self.db.fetch_one(query)
        return entities.AuthCredentials.from_db(record) if record else None

    async def create_credentials(self, user_id: int, login: str, password_hash: bytes) -> entities.AuthCredentials:
        query = auth_credentials.insert()\
            .values(user_id=user_id, login=login, password_hash=password_hash)\
            .returning(auth_credentials)
        record = await self.db.fetch_one(query)
        return entities.AuthCredentials.from_db(record)