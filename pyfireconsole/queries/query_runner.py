from typing import Any, Dict, Generator

from google.cloud.firestore_v1.base_query import BaseQuery
from google.cloud.firestore_v1.document import DocumentSnapshot

from pyfireconsole.db.connection import conn
from pyfireconsole.queries.abstract_query import _doc_to_dict
from pyfireconsole.queries.all_query import AllQuery
from pyfireconsole.queries.delete_query import DeleteQuery
from pyfireconsole.queries.get_query import GetQuery
from pyfireconsole.queries.order_query import OrderQuery
from pyfireconsole.queries.save_query import SaveQuery
from pyfireconsole.queries.where_query import WhereQuery


class QueryRunner:
    def __init__(self, collection_key: str):
        self.conn = conn
        self.collection_key = collection_key
        self.query = None

    def get(self, id: str) -> Dict | None:
        return GetQuery(self.collection_key, id).set_conn(self.conn).exec()

    def where(self, field: str, operator: str, value: str) -> 'QueryRunner':
        self.query = WhereQuery(self.query or self.collection_key, field, operator, value).set_conn(self.conn).exec()
        return self

    def order(self, field: str, direction: str) -> 'QueryRunner':
        self.query = OrderQuery(self.query or self.collection_key, field, direction).set_conn(self.conn).exec()
        return self

    def all(self) -> 'QueryRunner':
        self.query = AllQuery(self.query or self.collection_key).set_conn(self.conn).exec()
        return self

    def limit(self, limit: int) -> 'QueryRunner':
        """
        Apply a limit to the query.
        Args:
            limit (int): The maximum number of documents to retrieve.
        Returns:
            QueryRunner: The current QueryRunner instance.
        """
        self.query = self.query.limit(limit) if self.query else self.conn.collection(self.collection_key).limit(limit)
        return self

    def save(self, id: str, data: dict) -> str | None:
        return SaveQuery(self.collection_key, id, data).set_conn(self.conn).exec()

    def create(self, data: dict) -> str | None:
        return SaveQuery(self.collection_key, None, data).set_conn(self.conn).exec()

    def delete(self, id: str) -> None:
        return DeleteQuery(self.collection_key, id).set_conn(self.conn).exec()

    def iter(self, limit: int = 1000) -> Generator[Dict[str, Any], None, None]:
        docs = self.query.stream()

        docs = self.query.limit(limit).stream()

        for doc in docs:
            yield dict(_doc_to_dict(doc) or {}, id=doc.id)
