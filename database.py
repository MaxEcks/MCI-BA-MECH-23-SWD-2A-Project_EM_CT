import os
from tinydb import TinyDB
from tinydb.table import Table
from tinydb.storages import JSONStorage
from tinydb_serialization import SerializationMiddleware

serializer = SerializationMiddleware(JSONStorage)

class DatabaseConnector:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.json')
            cls.__instance._db = None
        return cls.__instance
    
    def get_db(self) -> TinyDB:
        """
        Stellt sicher, dass wir nur EINE TinyDB-Instanz haben
        und gibt sie zurück.
        """
        if self._db is None:
            self._db = TinyDB(self.path, storage=serializer)
        return self._db

    def get_table(self, table_name: str) -> Table:
        """
        Gibt eine TinyDB-Tabelle zurück.
        """
        db = self.get_db()
        return db.table(table_name)
    
    def close(self):
        """
        Schließt die TinyDB-Instanz und setzt sie auf None.
        Danach kann man database.json kopieren / löschen.
        """
        if self._db is not None:
            self._db.close()
            self._db = None