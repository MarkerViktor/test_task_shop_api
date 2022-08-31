import dataclasses
import decimal
import typing
from abc import abstractmethod

from src import entities


class ShopRepositoryProtocol(typing.Protocol):
    @abstractmethod
    async def check_product_exist(self, id_: int) -> bool: ...

    @abstractmethod
    async def create_product(self, fields: 'ProductCreationFields') -> entities.Product: ...

    @abstractmethod
    async def get_product(self, id_: int) -> entities.Product | None: ...

    @abstractmethod
    async def get_products(self, limit: int, offset: int) -> list[entities.Product]: ...

    @abstractmethod
    async def patch_product(self, id_: int, fields: 'ProductPatchFields') -> None: ...


class ShopService:
    def __init__(self, repository: ShopRepositoryProtocol):
        self._repository = repository

    async def get_product(self, id_: int) -> entities.Product | None:
        return await self._repository.get_product(id_)

    async def get_products(self, limit: int, offset: int) -> list[entities.Product]:
        return await self._repository.get_products(limit, offset)

    async def create_product(self, fields: 'ProductCreationFields') -> entities.Product:
        return await self._repository.create_product(fields)

    async def patch_product(self, id_: int, fields: 'ProductPatchFields') -> None:
        exist = await self._repository.check_product_exist(id_)
        if not exist:
            raise ProductNotExist(id_)
        await self._repository.patch_product(id_, fields)


@dataclasses.dataclass
class ProductCreationFields:
    title: str
    description: str
    price: decimal.Decimal


@dataclasses.dataclass
class ProductPatchFields:
    title: str | None = None
    description: str | None = None
    price: str | None = None


class ProductNotExist(Exception):
    def __init__(self, product_id: int):
        super().__init__(f'Product(id={product_id}) not exist.')
