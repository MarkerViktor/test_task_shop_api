import sanic
from sanic import exceptions
import pydantic

from src.handlers.utils import require, PydanticBody, pydantic_response
from src.services import auth

api_auth = sanic.Blueprint('api_auth')


class SignInRequest(pydantic.BaseModel):
    login: str
    password: str

class SignInResponse(pydantic.BaseModel):
    token: str

@api_auth.post('/sign_in/')
@require(payload=PydanticBody(SignInRequest))
async def sign_in(r: sanic.Request, payload: SignInRequest) -> sanic.HTTPResponse:
    auth_service: auth.AuthService = r.app.ctx.auth_service
    try:
        result = await auth_service.sign_in(payload.login, payload.password)
    except (auth.UserNotExist, auth.InvalidPassword) as e:
        raise exceptions.BadRequest(e)
    return pydantic_response(SignInResponse(token=result.token))


class SignUpRequest(pydantic.BaseModel):
    login: str
    password: str

class SignUpResponse(pydantic.BaseModel):
    activation_link: str

@api_auth.post('/sign_up/')
@require(payload=PydanticBody(SignUpRequest))
async def sign_up(r: sanic.Request, payload: SignUpRequest) -> sanic.HTTPResponse:
    auth_service: auth.AuthService = r.app.ctx.auth_service
    try:
        result = await auth_service.sign_up(payload.login, payload.password)
    except auth.UserAlreadyExist as e:
        raise exceptions.BadRequest(e)
    return pydantic_response(SignUpResponse(activation_link=result.activation_code))
