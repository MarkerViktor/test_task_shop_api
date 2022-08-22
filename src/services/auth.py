import dataclasses
import hashlib
import os
import typing
from abc import abstractmethod

import jwt

from src import config
from src import entities
from src.services.user import UserService


class AuthRepositoryProtocol(typing.Protocol):
    @abstractmethod
    async def get_credentials_by_login(self, login: str) -> entities.AuthCredentials | None: ...

    @abstractmethod
    async def create_credentials(self, user_id: int, login: str, password_hash: bytes) -> entities.AuthCredentials: ...


class AuthService:
    def __init__(self, repository: AuthRepositoryProtocol, user_service: UserService):
        self._repository = repository
        self._user_service = user_service

    async def sign_in(self, login: str, password: str) -> 'SignInResult':
        credentials = await self._repository.get_credentials_by_login(login)
        if credentials is None:
            raise UserNotExist(f'User with login "{login}" does not exist.')
        saved_hash, salt = _split_to_hash_and_salt(credentials.password_hash)
        if saved_hash != _hash_password(password, salt):
            raise InvalidPassword(f'Provided password "{password}" is invalid.')
        token = _generate_jwt_token(credentials.user_id)
        return SignInResult(token)

    async def sign_up(self, login: str, password: str) -> 'SignUpResult':
        credentials = await self._repository.get_credentials_by_login(login)
        if credentials is not None:
            raise UserAlreadyExist(f'User with login "{login}" has already exist.')
        user = await self._user_service.create_user(
            type_=entities.UserType.regular,
            is_active=False,
        )
        salt = _generate_salt()
        password_hash = _hash_password(password, salt) + salt
        await self._repository.create_credentials(user.id, login, password_hash)
        return SignUpResult('test')

def _generate_salt() -> bytes:
    return os.urandom(config.PASSWORD_SALT_LENGTH)

def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        hash_name=config.PASSWORD_HASH_ALGORITHM,
        password=password.encode('utf-8'),
        salt=salt,
        iterations=config.PASSWORD_HASH_ITERATIONS,
    )

def _split_to_hash_and_salt(data: bytes) -> tuple[bytes, bytes]:
    salt_length = config.PASSWORD_SALT_LENGTH
    return data[:salt_length], data[salt_length:]

def _generate_jwt_token(user_id: int) -> str:
    return jwt.encode({'user_id': user_id}, config.JWT_SECRET)


@dataclasses.dataclass
class SignInResult:
    token: str

class InvalidPassword(Exception):
    pass

class UserNotExist(Exception):
    pass


@dataclasses.dataclass
class SignUpResult:
    activation_code: str

class UserAlreadyExist(Exception):
    pass
