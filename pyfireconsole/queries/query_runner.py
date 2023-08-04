from typing import Dict

from pyfireconsole.db.connection import conn
from pyfireconsole.queries.all_query import AllQuery
from pyfireconsole.queries.get_query import GetQuery
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
