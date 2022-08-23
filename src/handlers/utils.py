import abc
import functools
import typing

import pydantic
import sanic
from sanic import exceptions


Handler = typing.Callable[[sanic.Request, ...], typing.Awaitable[sanic.HTTPResponse]]

class ControllerRequirement(abc.ABC):
    @abc.abstractmethod
    async def prepare_requirement(self, request: sanic.Request) -> sanic.HTTPResponse | typing.Any: ...


class require:
    def __init__(self, *checkers: ControllerRequirement, **requirements: ControllerRequirement):
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


class PydanticBody(ControllerRequirement):
    def __init__(self, pydantic_model: typing.Type[pydantic.BaseModel]):
        self._pydantic_model = pydantic_model

    async def prepare_requirement(self, r: sanic.Request) -> pydantic.BaseModel:
        try:
            pydantic_data = self._pydantic_model.parse_obj(r.json)
        except pydantic.ValidationError as e:
            raise exceptions.BadRequest(f'Json data has wrong schema or types:\n{e}')
        return pydantic_data


class PydanticQuery(ControllerRequirement):
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
