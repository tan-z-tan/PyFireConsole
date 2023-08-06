from typing import Optional

from pyfireconsole.queries.abstract_query import AbstractQuery


class SaveQuery(AbstractQuery):

    def __init__(self, collection_key: str, doc_id: Optional[str], data: dict):
        self.collection_key = collection_key
        self.doc_id = doc_id
        self.data = data

    def exec(self) -> str:
        if self.doc_id:
            doc_ref = self.collection_ref(self.collection_key).document(self.doc_id)
        else:
            doc_ref = self.collection_ref(self.collection_key).document()

        doc_ref.set(self.data)
        return doc_ref.id
