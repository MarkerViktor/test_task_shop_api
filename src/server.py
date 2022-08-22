import os

import databases
import sanic


async def init_db(app: sanic.Sanic):
    await app.ctx.db.connect()

async def deinit_db(app: sanic.Sanic):
    await app.ctx.db.disconnect()


def init() -> sanic.Sanic:
    app = sanic.Sanic(__name__)

    app.ctx.db = databases.Database(os.environ['DB_URL'])
    app.register_listener(init_db, 'before_server_start')
    app.register_listener(deinit_db, 'before_server_stop')

    return app


if __name__ == '__main__':
    init().run('127.0.0.1', 8080, auto_reload=True)
