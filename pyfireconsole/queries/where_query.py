from google.cloud.firestore_v1.base_query import BaseQuery, FieldFilter
from google.cloud.firestore_v1.collection import CollectionReference

from pyfireconsole.queries.abstract_query import AbstractQuery


class WhereQuery(AbstractQuery):
    def __init__(self, collection_key_or_query: str | BaseQuery, field: str, operator: str, value: str):
        self.collection_key_or_query = collection_key_or_query
        self.field = field
        self.operator = operator
        self.value = value

    def exec(self) -> BaseQuery:
        base = self.collection_ref(self.collection_key_or_query)

        return base.where(
            # We can't use FieldFilter because we use python-mock-firestore lib for testing
            # filter=FieldFilter(self.field, self.operator, self.value)
            self.field, self.operator, self.value
        )
