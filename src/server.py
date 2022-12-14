import databases
import sanic

from src import config
from src.handlers.auth import api_auth
from src.handlers.user import api_user
from src.middlewares.auth import authenticate_user
from src.repositories.auth import AuthRepository
from src.repositories.user import UserRepository
from src.services.auth import AuthService
from src.services.user import UserService


async def init_db(app: sanic.Sanic):
    await app.ctx.db.connect()

async def deinit_db(app: sanic.Sanic):
    await app.ctx.db.disconnect()


def init() -> sanic.Sanic:
    app = sanic.Sanic('shop_api')

    app.ctx.db = databases.Database(config.DB_URL)
    app.register_listener(init_db, 'before_server_start')
    app.register_listener(deinit_db, 'before_server_stop')

    app.ctx.user_service = UserService(
        repository=UserRepository(app.ctx.db)
    )

    app.ctx.auth_service = AuthService(
        repository=AuthRepository(app.ctx.db),
        user_service=app.ctx.user_service,
    )

    app.register_middleware(authenticate_user, 'request')

    app.blueprint(api_user)
    app.blueprint(api_auth)

    return app
