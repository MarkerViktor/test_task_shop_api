import databases
import sanic

from src import config
from src.handlers.user import api_user
from src.repositories.user import UserRepository
from src.services.user import UserService


async def init_db(app: sanic.Sanic):
    await app.ctx.db.connect()

async def deinit_db(app: sanic.Sanic):
    await app.ctx.db.disconnect()


def init() -> sanic.Sanic:
    app = sanic.Sanic(__name__)

    app.ctx.db = databases.Database(config.DB_URL)
    app.register_listener(init_db, 'before_server_start')
    app.register_listener(deinit_db, 'before_server_stop')

    app.ctx.user_service = UserService(
        user_repository=UserRepository(app.ctx.db)
    )

    app.blueprint(api_user)

    return app


if __name__ == '__main__':
    init().run('127.0.0.1', 8080, auto_reload=True)
