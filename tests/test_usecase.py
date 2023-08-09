from datetime import datetime
from typing import Optional

import pytest
from pyfireconsole.db.connection import FirestoreConnection, NotConnectedException
from pyfireconsole.models.association import belongs_to, has_many, resolve_pyfire_model_names
from pyfireconsole.models.pyfire_model import DocumentRef, PyfireCollection, PyfireDoc
from mockfirestore import MockFirestore

from pyfireconsole.queries.get_query import DocNotFoundException  # type: ignore


class I18n_Name(PyfireDoc):
    lang: str
    value: str


class Tag(PyfireDoc):
    name: str
    i18n_names: PyfireCollection[I18n_Name] = PyfireCollection(I18n_Name)


@has_many('Book', "user_id", "my_books")
class User(PyfireDoc):
    name: str
    email: str


class Publisher(PyfireDoc):
    name: str
    address: Optional[str] = None


@belongs_to(User, "user_id")
class Book(PyfireDoc):
    title: str
    user_id: str
    published_at: datetime
    authors: list[str]
    edit_info: Optional[dict[str, object]] = None
    tags: PyfireCollection[Tag] = PyfireCollection(Tag)
    publisher_ref: DocumentRef[Publisher] | str


resolve_pyfire_model_names(globals())


# ================== test ====================

@pytest.fixture
def mock_db():
    db = MockFirestore()
    FirestoreConnection().set_db(db)
    yield db
    db.reset()


def test_no_connection():
    """
    When there is no connection, it should raise NotConnectedException
    """
    with pytest.raises(NotConnectedException):
        Book.find("12345")


def test_save_find(mock_db):
    # case: create a document
    book = Book.new(
        title="Math",
        user_id="12345",
        published_at=datetime.now(),
        authors=["John", "Mary"],
        publisher_ref="publisher/12345",
    ).save()
    assert book.__class__ == Book
    assert book.title == "Math"
    assert book.id is not None

    book2 = Book.new(
        title="History",
        user_id="12345",
        published_at=datetime.now(),
        authors=["John", "Mary"],
        publisher_ref="publisher/abcde",
    ).save()
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


def test_find_not_found(mock_db):
    # case: there is no document
    with pytest.raises(DocNotFoundException):
        Book.find("99999")


def test_subcollection(mock_db):
    book = Book.new(
        title="Math",
        user_id="12345",
        published_at=datetime.now(),
        authors=["John", "Mary"],
        publisher_ref="publisher/12345",
    ).save()

    book.tags.add(Tag.new(name="mathmatics"))
    book.tags.add(Tag.new(name="textbook"))
    # book.save()

    assert len([t for t in book.tags]) == 2

    tag_names = [tag.name for tag in book.tags]
    assert "mathmatics" in tag_names
    assert "textbook" in tag_names


def test_deep_subcollection(mock_db):
    book = Book.new(
        title="Math",
        user_id="12345",
        published_at=datetime.now(),
        authors=["John", "Mary"],
        publisher_ref="publisher/12345",
    ).save()

    tag = book.tags.add(Tag.new(name="mathmatics"))

    tag.i18n_names.add(I18n_Name(lang="en", value="Mathmatics"))
    tag.i18n_names.add(I18n_Name(lang="ja", value="数学"))

    assert sorted([n.lang for n in tag.i18n_names]) == sorted(["en", "ja"])

    i18n_names = []
    for t in book.tags:
        print(t)
        for name in t.i18n_names:
            i18n_names.append(name.value)
    assert sorted(i18n_names) == sorted(["Mathmatics", "数学"])


def test_first(mock_db):
    mock_db = MockFirestore()
    mock_db.reset()

    user1 = User.new(
        name="John",
        email="",
    ).save()
    user2 = User.new(
        name="Mary",
        email="",
    ).save()

    user = User.first()

    assert user.id in [user1.id, user2.id]


def test_as_json(mock_db):
    book = Book.new(
        title="Math",
        user_id="12345",
        published_at=datetime.now(),
        authors=["John", "Mary"],
        publisher_ref="publisher/12345",
    ).save()
    tag = book.tags.add(Tag.new(name="mathmatics"))
    user = User.new(
        id=book.user_id,
        name="John",
        email="",
    ).save()

    assert user.as_json() == {
        "id": "12345",
        "name": "John",
        "email": "",
    }

    assert book.as_json() == {
        "id": book.id,
        "title": "Math",
        "user_id": "12345",
        "published_at": book.published_at,
        "authors": ["John", "Mary"],
        "edit_info": None,
        "publisher_ref": "publisher/12345",
    }

    assert book.as_json(include=['user']) == {
        "id": book.id,
        "title": "Math",
        "user_id": "12345",
        "published_at": book.published_at,
        "authors": ["John", "Mary"],
        "edit_info": None,
        "publisher_ref": "publisher/12345",
        "user": {"id": user.id, "name": "John", "email": ""},
    }

    assert book.as_json(excepts=['id', 'published_at', 'edit_info']) == {
        "title": "Math",
        "user_id": "12345",
        "authors": ["John", "Mary"],
        "publisher_ref": "publisher/12345",
    }

    assert book.as_json(recursive=True) == {
        "id": book.id,
        "title": "Math",
        "user_id": "12345",
        "published_at": book.published_at,
        "authors": ["John", "Mary"],
        "edit_info": None,
        "publisher_ref": "publisher/12345",
        "tags": [{"id": tag.id, "name": "mathmatics", "i18n_names": []}],
    }

    assert book.as_json(recursive=True, include=["user"]) == {
        "id": book.id,
        "title": "Math",
        "user_id": "12345",
        "published_at": book.published_at,
        "authors": ["John", "Mary"],
        "edit_info": None,
        "publisher_ref": "publisher/12345",
        "tags": [{"id": tag.id, "name": "mathmatics", "i18n_names": []}],
        "user": {"id": user.id, "name": "John", "email": ""},
    }

    with pytest.raises(AttributeError):
        book.as_json(recursive=True, include=["invalid_field"])


def test_belongs_to(mock_db):
    user = User.new(
        name="John",
        email="",
    ).save()

    book = Book.new(
        title="Math",
        user_id=user.id,
        published_at=datetime.now(),
        authors=["John", "Mary"],
        publisher_ref="publisher/12345",
    ).save()

    assert book.user.name == "John"
    assert book.user.email == ""


def test_has_many(mock_db):
    user = User.new(
        name="John",
        email="",
    ).save()

    Book.new(
        title="Math",
        user_id=user.id,
        published_at=datetime.now(),
        authors=["John", "Mary"],
        publisher_ref="publisher/12345",
    ).save()

    Book.new(
        title="History",
        user_id=user.id,
        published_at=datetime.now(),
        authors=["John", "Mary"],
        publisher_ref="publisher/12345",
    ).save()

    assert len([b for b in user.my_books]) == 2
    assert sorted([b.title for b in user.my_books]) == sorted(["Math", "History"])


def test_delete(mock_db):
    user = User.new(
        name="John",
        email="",
    ).save()

    book1 = Book.new(
        title="Math",
        user_id=user.id,
        published_at=datetime.now(),
        authors=["John", "Mary"],
        publisher_ref="publisher/12345",
    ).save()

    _book2 = Book.new(
        title="History",
        user_id=user.id,
        published_at=datetime.now(),
        authors=["John", "Mary"],
        publisher_ref="publisher/12345",
    ).save()

    assert len([b for b in user.my_books]) == 2
    book1.delete()
    assert len([b for b in user.my_books]) == 1
    assert user.my_books.first().title == "History"

    with pytest.raises(DocNotFoundException):
        Book.find(book1.id)
