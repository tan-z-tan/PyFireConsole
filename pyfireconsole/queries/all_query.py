from google.cloud.firestore_v1.base_query import BaseQuery
from google.cloud.firestore_v1.collection import CollectionReference

from pyfireconsole.queries.abstract_query import AbstractQuery


class AllQuery(AbstractQuery):
    def __init__(self, collection_key_or_query: str | BaseQuery):
        self.collection_key_or_query = collection_key_or_query

    def exec(self) -> BaseQuery | CollectionReference:
        return self.collection_ref(self.collection_key_or_query)
