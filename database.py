import os
from tinydb import TinyDB
from tinydb.table import Table
from tinydb.storages import JSONStorage
from tinydb_serialization import SerializationMiddleware

class DatabaseConnector:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mechanism_database.json')
        return cls.__instance

    def get_table(self, table_name: str) -> Table:
        return TinyDB(self.__instance.path, storage=serializer).table(table_name)

serializer = SerializationMiddleware(JSONStorage)
