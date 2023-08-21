
from enum import Enum

from google.cloud.firestore_v1.base_query import BaseQuery

from pyfireconsole.queries.abstract_query import AbstractQuery


class OrderDirection(str, Enum):
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


class OrderCondition:
    field: str
    direction: str

    def __init__(self, field: str, direction: str):
        self.field = field
        self.direction = direction


class OrderQuery(AbstractQuery):
    def __init__(self, collection_key_or_query: str | BaseQuery, field: str, direction: OrderDirection):
        self.collection_key_or_query = collection_key_or_query
        self.field = field
        self.direction = direction

    def exec(self):
        base = self.collection_ref(self.collection_key_or_query)

        return base.order_by(
            self.field, direction=self.direction
        )
