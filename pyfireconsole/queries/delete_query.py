from pyfireconsole.queries.abstract_query import AbstractQuery


class DeleteQuery(AbstractQuery):
    def __init__(self, collection_key: str, doc_id: str):
        self.collection_key = collection_key
        self.doc_id = doc_id

    def exec(self) -> bool:
        doc_ref = self.collection_ref(self.collection_key).document(self.doc_id)
        if doc_ref.get().exists:
            doc_ref.delete()
            return not self.collection_ref(self.collection_key).document(self.doc_id).get().exists
        return False
