import sanic

from src.services import auth


async def authenticate_user(r: sanic.Request) -> None:
    auth_service: auth.AuthService = r.app.ctx.auth_service

    if auth_header := r.headers.get('Authentication'):
        token = auth_header.removeprefix('Bearer').strip()
        r.ctx.auth = await auth_service.authenticate(token)
    else:
        r.ctx.auth = None
