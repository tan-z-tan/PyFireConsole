from pyfireconsole.queries.abstract_query import AbstractQuery, _doc_to_dict


class AllQuery(AbstractQuery):
    def __init__(self, collection_key: str):
        self.collection_key = collection_key

    def exec(self) -> list[dict]:
        docs = self.collection_ref(self.collection_key).stream()
        return [dict(_doc_to_dict(doc) or {}, id=doc.id) for doc in docs]
