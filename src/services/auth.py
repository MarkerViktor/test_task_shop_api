import asyncio
import dataclasses
import hashlib
import os
import typing
import uuid
from abc import abstractmethod

import jwt

from src import config
from src import entities
from src.services.user import UserService


class AuthRepositoryProtocol(typing.Protocol):
    @abstractmethod
    async def create_credentials(self, user_id: int, login: str, password_hash: bytes) -> entities.AuthCredentials: ...

    @abstractmethod
    async def get_credentials_by_login(self, login: str) -> entities.AuthCredentials | None: ...


class AuthService:
    def __init__(self, repository: AuthRepositoryProtocol, user_service: UserService):
        self._repository = repository
        self._user_service = user_service

    async def sign_in(self, login: str, password: str) -> 'SignInResult':
        credentials = await self._repository.get_credentials_by_login(login)
        if credentials is None:
            raise LoginNotExist(login)

        saved_hash, salt = _split_to_hash_and_salt(credentials.password_hash)
        if saved_hash != _hash_password(password, salt):
            raise InvalidPassword(password)

        payload = {
            'user_id': credentials.user_id
        }
        token = _encode_jwt_token(payload)
        return SignInResult(auth_token=token)

    async def sign_up(self, login: str, password: str) -> 'SignUpResult':
        credentials = await self._repository.get_credentials_by_login(login)
        if credentials is not None:
            raise LoginAlreadyExist(login)

        user = await self._user_service.create_user(entities.UserType.regular, is_active=False)

        salt = _generate_salt()
        password_hash = _hash_password(password, salt) + salt

        _, activation_token = await asyncio.gather(
            self._repository.create_credentials(user.id, login, password_hash),
            self._user_service.create_activation_token(user.id)
        )
        return SignUpResult(activation_token=activation_token.token)


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

def _encode_jwt_token(payload: dict[str, typing.Any]) -> str:
    return jwt.encode(payload, config.JWT_SECRET, config.JWT_ALGORITHM)

def _decode_jwt_token(token: str) -> dict[str, typing.Any] | None:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, config.JWT_ALGORITHM)
    except jwt.exceptions.DecodeError:
        return None
    else:
        return payload


@dataclasses.dataclass
class SignInResult:
    auth_token: str

class InvalidPassword(Exception):
    def __init__(self, password: str):
        super().__init__(f'Provided password "{password}" is invalid.')

class LoginNotExist(Exception):
    def __init__(self, login: str):
        super().__init__(f'User with provided login "{login}" does not exist.')


@dataclasses.dataclass
class SignUpResult:
    activation_token: uuid.UUID

class LoginAlreadyExist(Exception):
    def __init__(self, login: str):
        super().__init__(f'User with provided login "{login}" has already exist.')

