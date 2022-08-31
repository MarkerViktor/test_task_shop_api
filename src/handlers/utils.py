import abc
import functools
import typing

import databases
import pydantic
import sanic
from sanic import exceptions

from src import entities
from src.services.auth import AuthResult

Handler = typing.Callable[[sanic.Request, ...], typing.Awaitable[sanic.HTTPResponse]]

class HandlerRequirement(abc.ABC):
    @abc.abstractmethod
    async def prepare_requirement(self, r: sanic.Request) -> sanic.HTTPResponse | typing.Any: ...


class require:
    def __init__(self, *checkers: HandlerRequirement, **requirements: HandlerRequirement):
        self._checkers = checkers
        self._requirements = requirements  # Результат передаётся как keyword-аргументы в обработчик

    def __call__(self, handler: Handler) -> Handler:
        @functools.wraps(handler)
        async def wrapper_handler(request: sanic.Request, *args, **kwargs) -> sanic.HTTPResponse | typing.Any:
            nonlocal self, handler

            for checker in self._checkers:
                checker_result = await checker.prepare_requirement(request)
                if isinstance(checker_result, sanic.HTTPResponse):
                    return checker_result

            requirements_kwargs = {}
            for name, requirement in self._requirements.items():
                preparing_result = await requirement.prepare_requirement(request)
                if isinstance(preparing_result, sanic.HTTPResponse):
                    return preparing_result
                requirements_kwargs[name] = preparing_result
            return await handler(request, *args, **kwargs, **requirements_kwargs)
        return wrapper_handler


def pydantic_response(data: pydantic.BaseModel) -> sanic.HTTPResponse:
    return sanic.json(data.dict())


class PydanticJson(HandlerRequirement):
    def __init__(self, pydantic_model: typing.Type[pydantic.BaseModel]):
        self._pydantic_model = pydantic_model

    async def prepare_requirement(self, r: sanic.Request) -> pydantic.BaseModel:
        try:
            pydantic_data = self._pydantic_model.parse_obj(r.json)
        except pydantic.ValidationError as e:
            raise exceptions.BadRequest(f'Json data has wrong schema or types:\n{e}')
        return pydantic_data


class PydanticQuery(HandlerRequirement):
    def __init__(self, pydantic_model: typing.Type[pydantic.BaseModel]):
        self._pydantic_model = pydantic_model

    async def prepare_requirement(self, r: sanic.Request) -> pydantic.BaseModel:
        query_args = {
            key: (value if len(value) > 1 else value[0])
            for key, value in r.args.items()
        }
        try:
            pydantic_data = self._pydantic_model.parse_obj(query_args)
        except pydantic.ValidationError as e:
            raise exceptions.BadRequest(f'Json data has wrong schema or types:\n{e}')
        return pydantic_data


class Auth(HandlerRequirement):
    def __init__(self, *, allowed: typing.Sequence[entities.UserType] = None,
                 denied: typing.Sequence[entities.UserType] = None):
        assert not all((allowed is not None, denied is not None)), 'Provided both of allowed and denied.'
        self._allowed = allowed
        self._denied = denied

    async def prepare_requirement(self, r: sanic.Request) -> sanic.HTTPResponse | AuthResult:
        auth: AuthResult = r.ctx.auth
        if auth is None:
            raise exceptions.Unauthorized('"Authentication" header is absent.')
        if not auth.token_is_valid:
            raise exceptions.Unauthorized('Bad authentication credentials.')

        not_allowed = self._allowed is not None and auth.user_type not in self._allowed
        denied = self._denied is not None and auth.user_type in self._denied
        if not_allowed or denied:
            raise exceptions.Forbidden('Bad user type.')

        return auth


def transaction(handler: Handler) -> Handler:
    @functools.wraps(handler)
    async def wrapper(request: sanic.Request, *args, **kwargs) -> sanic.HTTPResponse:
        db: databases.Database = request.app.ctx.db
        async with db.transaction():
            return await handler(request, *args, *kwargs)
    return wrapper
