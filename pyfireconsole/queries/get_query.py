from pyfireconsole.queries.abstract_query import AbstractQuery, _doc_to_dict


class DocNotFoundException(Exception):
    pass


class GetQuery(AbstractQuery):
    def __init__(self, collection_key: str, doc_id: str):
        self.collection_key = collection_key
        self.doc_id = doc_id

    def exec(self) -> dict | None:
        doc_ref = self.collection_ref(self.collection_key).document(self.doc_id)
        doc = doc_ref.get()
        if doc.exists:
            return dict(_doc_to_dict(doc) or {}, id=doc.id)
        raise DocNotFoundException(f"Document with id {self.doc_id} not found")
