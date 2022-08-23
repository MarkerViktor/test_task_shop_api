import uuid
from dataclasses import asdict

import pydantic
import sanic
from sanic import exceptions

from src.handlers.utils import require, PydanticQuery
from src.services import user


api_user = sanic.Blueprint('api_user')


@api_user.get('/users/')
async def get_users(r: sanic.Request) -> sanic.HTTPResponse:
    user_service: user.UserService = r.app.ctx.user_service
    limit, offset = r.args.get('limit'), r.args.get('offset')
    users = await user_service.get_users(limit, offset)
    users_as_dicts = list(asdict(u) for u in users)
    return sanic.json(users_as_dicts)


@api_user.post('/user/<user_id:int>/activate', name='activate user')
@api_user.post('/user/<user_id:int>/deactivate', name='deactivate user')
async def activate_user(r: sanic.Request, user_id: int) -> sanic.HTTPResponse:
    user_service: user.UserService = r.app.ctx.user_service
    is_active = False if r.name.endswith('deactivate user') else True
    try:
        await user_service.change_user_activation(user_id, is_active)
    except user.UserNotExist as e:
        raise exceptions.NotFound(e)
    return sanic.HTTPResponse(status=200)


class ActivateByLinkQuery(pydantic.BaseModel):
    token: uuid.UUID

@api_user.get('/user/activate/')
@require(query=PydanticQuery(ActivateByLinkQuery))
async def activate_user_by_token(r: sanic.Request, query: ActivateByLinkQuery) -> sanic.HTTPResponse:
    user_service: user.UserService = r.app.ctx.user_service
    try:
        await user_service.activate_user_by_token(query.token)
    except (user.InvalidActivationToken, user.UserAlreadyActivated) as e:
        raise exceptions.NotFound(e)
    else:
        return sanic.HTTPResponse(status=200)
