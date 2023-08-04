from datetime import datetime
from typing import Optional

import pytest
from pyfireconsole.db.connection import FirestoreConnection, NotConnectedException
from pyfireconsole.models.pyfire_model import DocumentRef, PyfireCollection, PyfireDoc
from mockfirestore import MockFirestore

from pyfireconsole.queries.get_query import DocNotFoundException  # type: ignore


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
    address: Optional[str] = None


class Book(PyfireDoc):
    title: str
    user_id: str
    published_at: datetime
    authors: list[str]
    edit_info: Optional[dict[str, object]] = None
    tags: PyfireCollection[Tag] = PyfireCollection(Tag)
    publisher_ref: DocumentRef[Publisher] | str
    PyfireDoc.belongs_to(User)  # book.user


def test_no_connection():
    """
    When there is no connection, it should raise NotConnectedException
    """
    with pytest.raises(NotConnectedException):
        Book.find("12345")


def test_save_find():
    # We use mockfirestore to mock firestore operations.
    # From now on the tests, db is available.
    FirestoreConnection().set_db(MockFirestore())

    # case: create a document
    book = Book.new({
        "title": "Math",
        "user_id": "12345",
        "published_at": datetime.now(),
        "authors": ["John", "Mary"],
        "publisher_ref": "publisher/12345",
    }).save()
    assert book.__class__ == Book
    assert book.title == "Math"
    assert book.id is not None

    book2 = Book.new({
        "title": "History",
        "user_id": "12345",
        "published_at": datetime.now(),
        "authors": ["John", "Mary"],
        "publisher_ref": "publisher/abcde",
    }).save()
    assert book2.__class__ == Book
    assert book2.title == "History"
    assert book2.id is not None

    # find
    found_book = Book.find(book.id)
    assert found_book.__class__ == Book
    assert found_book.title == "Math"
    assert found_book.id == book.id

    # where
    books = Book.where("title", "==", "Math")
    assert books.__class__ == PyfireCollection
    assert len([b for b in books]) == 1


def test_find_not_found():
    # case: there is no document
    with pytest.raises(DocNotFoundException):
        Book.find("99999")
