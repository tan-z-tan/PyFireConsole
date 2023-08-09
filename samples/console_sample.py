from datetime import datetime
from typing import Optional
from pyfireconsole.models.association import belongs_to, has_many, resolve_pyfire_model_names
from pyfireconsole.models.pyfire_model import PyfireCollection, DocumentRef, PyfireDoc
from pyfireconsole.db.connection import FirestoreConnection
from pyfireconsole import PyFireConsole


@has_many('Book', "user_id")
class User(PyfireDoc):
    name: str
    email: str


class Publisher(PyfireDoc):
    name: str
    address: Optional[str]


class Tag(PyfireDoc):
    name: str


@belongs_to(User, "user_id")
class Book(PyfireDoc):
    title: str
    user_id: str
    published_at: datetime
    authors: list[str]
    tags: PyfireCollection[Tag] = PyfireCollection(Tag)
    publisher_ref: DocumentRef[Publisher]


# Resolve PyfireModel names
# Call this function when you define your models by using str class name.
# e.g. @has_many('Book', "user_id")
resolve_pyfire_model_names(globals())


FirestoreConnection().initialize(project_id="promptr-dev-prod")
PyFireConsole().run()
