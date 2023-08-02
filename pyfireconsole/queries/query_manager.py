from typing import Dict
from pyfireconsole.queries.query import Query, _recursive_to_dict
from pyfireconsole.db.connection import conn


class QueryManager:
    def __init__(self, model_class_str: str):
        self.collection = conn.collection(model_class_str)
        self.query = Query(self.collection)

    def get(self, id: str) -> Dict | None:
        return self.query.get(id)

    def where(self, field: str, operator: str, value: str) -> list[Dict]:
        return self.query.where(field, operator, value)

    def all(self) -> list[Dict]:
        return self.query.all()

    @staticmethod
    def get_from_path(path: str) -> Dict | None:
        doc_ref = conn.document(path)
        doc = doc_ref.get()
        if doc.exists:
            return dict(_recursive_to_dict(doc) or {}, id=doc.id)
        return None
