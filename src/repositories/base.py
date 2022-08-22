import databases


class BaseRepository:
    def __init__(self, database: databases.Database):
        self.db = database
