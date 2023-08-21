from typing import Dict, Optional

from google.cloud.firestore_v1.base_query import BaseQuery
from google.cloud.firestore_v1.document import DocumentReference, DocumentSnapshot

from pyfireconsole.db.connection import FirestoreConnection


class AbstractQuery:
    def set_conn(self, conn: FirestoreConnection) -> "AbstractQuery":
        self.conn = conn
        return self

    def collection_ref(self, collection_key_or_query: str | BaseQuery) -> DocumentReference | BaseQuery:
        if isinstance(collection_key_or_query, str):
            return self.conn.collection(collection_key_or_query)
        else:
            return collection_key_or_query

    def exec(self):
        raise NotImplementedError


def _doc_to_dict(obj: DocumentSnapshot):
    """
    Convert a DocumentSnapshot to a python dictionary.
    """
    return dict(_recursive_to_dict(obj) or {}, id=obj.id)


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
