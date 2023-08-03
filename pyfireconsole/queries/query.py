from google.cloud.firestore_v1 import DocumentSnapshot, DocumentReference, CollectionReference  # ignore this line
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import Any, Dict, Optional


class Query:
    def __init__(self, collection: CollectionReference):
        self.collection = collection

    def all(self):
        docs = self.collection.get()
        return [(doc.id, doc.to_dict()) for doc in docs]

    def get(self, id: str) -> Optional[Dict]:
        doc_ref: DocumentReference = self.collection.document(id)
        doc = doc_ref.get()
        if doc.exists:
            return dict(_recursive_to_dict(doc) or {}, id=doc.id)
        return None
    
    def where(self, field: str, operator: str, value: str) -> list[Optional[Dict[str, Any]]]:
        docs = self.collection.where(filter=FieldFilter(field, operator, value)).stream()
        return [dict(_recursive_to_dict(doc) or {}, id=doc.id) for doc in docs]

    def create(self, **kwargs) -> Optional[Dict]:
        doc_ref: DocumentReference = self.collection.document()
        doc_ref.set(kwargs)
        return self.get(doc_ref.id)

    def update(self, id: str, **kwargs) -> Optional[Dict]:
        doc_ref: DocumentReference = self.collection.document(id)
        doc_ref.update(kwargs)
        return self.get(id)

    def delete(self, id: str) -> None:
        doc_ref: DocumentReference = self.collection.document(id)
        doc_ref.delete()


def _recursive_to_dict(doc: DocumentSnapshot) -> Optional[Dict]:
    data = doc.to_dict()
    if data is None:
        return None

    for key, value in data.items():
        if isinstance(value, DocumentReference):
            data[key] = {
                "path": value.path,
            }
    return data
