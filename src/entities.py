import dataclasses
import decimal
import enum
import uuid


class UserType(str, enum.Enum):
    regular = 'regular'
    admin = 'admin'


@dataclasses.dataclass
class User:
    id: int
    type: UserType
    is_active: bool

    @classmethod
    def from_db(cls, record) -> 'User':
        return cls(record.id, UserType(record.type), record.is_active)


@dataclasses.dataclass
class Product:
    id: int
    title: str
    description: str
    price_rub: decimal.Decimal

    @classmethod
    def from_db(cls, record) -> 'Product':
        return cls(record.id, record.title, record.description, decimal.Decimal(record.price_rub))


@dataclasses.dataclass
class PaymentAccount:
    id: int
    user_id: int
    balance_rub: decimal.Decimal


@dataclasses.dataclass
class Transaction:
    id: int
    payment_account_id: int
    amount_rub: decimal.Decimal


@dataclasses.dataclass
class AuthCredentials:
    id: int
    user_id: int
    login: str
    password_hash: bytes

    @classmethod
    def from_db(cls, record) -> 'AuthCredentials':
        return cls(record.id, record.user_id, record.login, record.password_hash)


@dataclasses.dataclass
class ActivationToken:
    token: uuid.UUID
    user_id: int

    @classmethod
    def from_db(cls, record) -> 'ActivationToken':
        return cls(record.token, record.user_id)
