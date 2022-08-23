from src.server import init


if __name__ == '__main__':
    init().run('127.0.0.1', 8080, dev=True)