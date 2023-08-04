from google.cloud.firestore_v1.base_query import FieldFilter

from pyfireconsole.queries.abstract_query import AbstractQuery, _doc_to_dict


class WhereQuery(AbstractQuery):
    def __init__(self, collection_key: str, field: str, operator: str, value: str):
        self.collection_key = collection_key
        self.field = field
        self.operator = operator
        self.value = value

    def exec(self) -> list[dict]:
        docs = self.collection_ref(self.collection_key).where(
            # We can't use FieldFilter because we use python-mock-firestore lib for testing
            # filter=FieldFilter(self.field, self.operator, self.value)
            self.field, self.operator, self.value
        ).stream()
        return [dict(_doc_to_dict(doc) or {}, id=doc.id) for doc in docs]
