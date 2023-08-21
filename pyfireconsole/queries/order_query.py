
from enum import Enum

from pyfireconsole.queries.abstract_query import AbstractQuery
from google.cloud.firestore_v1.base_query import BaseQuery


class OrderDirection(str, Enum):
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


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
