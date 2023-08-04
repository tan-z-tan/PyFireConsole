from datetime import datetime
from typing import Optional
from pyfireconsole.db.connection import FirestoreConnection
from pyfireconsole.models.pyfire_model import DocumentRef, PyfireCollection, PyfireDoc
from mockfirestore import MockFirestore  # type: ignore


class I18n_Name(PyfireDoc):
    lang: str
    value: str


class Tag(PyfireDoc):
    name: str
    i18n_names: Optional[PyfireCollection[I18n_Name]] = PyfireCollection(I18n_Name)


class User(PyfireDoc):
    name: str
    email: str


class Publisher(PyfireDoc):
    name: str
    address: Optional[str]


class Book(PyfireDoc):
    title: str
    user_id: str
    published_at: datetime
    authors: list[str]
    edit_info: Optional[dict[str, object]]
    tags: PyfireCollection[Tag] = PyfireCollection(Tag)
    publisher_ref: DocumentRef[Publisher] | str
    PyfireDoc.belongs_to(User)  # book.user


def test_find():
    mock_db = MockFirestore()
    FirestoreConnection().set_db(mock_db)

    book = Book.where("name", "==", "test")
    assert book.__class__ == PyfireCollection
