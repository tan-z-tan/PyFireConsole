from typing import Dict

from pyfireconsole.db.connection import conn
from pyfireconsole.queries.all_query import AllQuery
from pyfireconsole.queries.delete_query import DeleteQuery
from pyfireconsole.queries.get_query import GetQuery
from pyfireconsole.queries.save_query import SaveQuery
from pyfireconsole.queries.where_query import WhereQuery


class QueryRunner:
    def __init__(self, collection_key: str):
        self.conn = conn
        self.collection_key = collection_key

    def get(self, id: str) -> Dict | None:
        return GetQuery(self.collection_key, id).set_conn(self.conn).exec()

    def where(self, field: str, operator: str, value: str) -> list[Dict]:
        return WhereQuery(self.collection_key, field, operator, value).set_conn(self.conn).exec()

    def all(self) -> list[Dict]:
        return AllQuery(self.collection_key).set_conn(self.conn).exec()

    def save(self, id: str, data: dict) -> str | None:
        return SaveQuery(self.collection_key, id, data).set_conn(self.conn).exec()

    def create(self, data: dict) -> str | None:
        return SaveQuery(self.collection_key, None, data).set_conn(self.conn).exec()

    def delete(self, id: str) -> None:
        return DeleteQuery(self.collection_key, id).set_conn(self.conn).exec()
