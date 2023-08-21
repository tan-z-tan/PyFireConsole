
from enum import Enum

from pyfireconsole.queries.abstract_query import AbstractQuery, _doc_to_dict


class OrderDirection(str, Enum):
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


class OrderQuery(AbstractQuery):
    def __init__(self, collection_key: str, field: str, direction: OrderDirection):
        self.collection_key = collection_key
        self.field = field
        self.direction = direction

    def exec(self):
        docs = self.collection_ref(self.collection_key).order_by(
            self.field, direction=self.direction
        ).stream()
        return [dict(_doc_to_dict(doc) or {}, id=doc.id) for doc in docs]
