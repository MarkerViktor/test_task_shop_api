import decimal
import typing
from abc import abstractmethod

from src import entities
from src.services.user import UserService, UserNotExist


class BillingRepositoryProtocol(typing.Protocol):
    @abstractmethod
    async def create_payment_account(self, user_id: int) -> entities.PaymentAccount: ...

    @abstractmethod
    async def get_payment_account(self, id_: int) -> entities.PaymentAccount | None: ...

    @abstractmethod
    async def get_user_payment_accounts(self, user_id: int) -> list[entities.PaymentAccount]: ...

    @abstractmethod
    async def get_transactions(self, payment_account_id: int, limit: int, offset: int) -> list[entities.Transaction]:
        ...

    @abstractmethod
    async def change_balance(self, payment_account_id: int, amount: decimal.Decimal) -> entities.Transaction:
        # raises NoEnoughMoney exception if not enough money at the account.
        ...


class BillingService:
    def __init__(self, repository: BillingRepositoryProtocol, user_service: UserService):
        self._repository = repository
        self._user_service = user_service

    async def create_payment_account(self, user_id: int) -> entities.PaymentAccount:
        try:
            user = await self._user_service.get_user(user_id)
        except UserNotExist as e:
            raise OwnerNotExist(user_id) from e
        payment_account = await self._repository.create_payment_account(user.id)
        return payment_account

    async def do_transaction(self, payment_account_id: int, amount: decimal.Decimal) -> entities.Transaction:
        payment_account = await self.get_payment_account(payment_account_id)
        transaction = await self._repository.change_balance(payment_account.id, amount)
        return transaction

    async def get_payment_account(self, payment_account_id: int) -> entities.PaymentAccount:
        payment_account = await self._repository.get_payment_account(payment_account_id)
        if payment_account is None:
            raise PaymentAccountNotExist(payment_account_id)
        return payment_account

    async def get_payment_accounts(self, user_id: int) -> list[entities.PaymentAccount]:
        try:
            user = await self._user_service.get_user(user_id)
        except UserNotExist as e:
            raise OwnerNotExist(user_id) from e
        return await self._repository.get_user_payment_accounts(user.id)

    async def get_transactions(self, payment_account_id: int, limit: int, offset: int) -> list[entities.Transaction]:
        payment_account = await self.get_payment_account(payment_account_id)
        transactions = await self._repository.get_transactions(payment_account.id, limit, offset)
        return transactions


class PaymentAccountNotExist(Exception):
    def __init__(self, payment_account_id: int):
        super().__init__(f'Payment account (id="{payment_account_id}") not exist.')


class NoEnoughMoney(Exception):
    def __init__(self, payments_account_id: int, amount: decimal.Decimal):
        super().__init__(f'No enough money at payments_account (id={payments_account_id}) change {amount}.')


class OwnerNotExist(Exception):
    def __init__(self, user_id: int):
        super().__init__(f"User (id={user_id}) not exist.")
