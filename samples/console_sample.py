from datetime import datetime
from typing import Optional
from pyfireconsole.models.firestore_model import PyfireCollection, DocumentRef, PyfireDoc
from pyfireconsole.db.connection import FirestoreConnection
from pyfireconsole import PyFireConsole

class User(PyfireDoc):
    name: str
    email: str

class Publisher(PyfireDoc):
    name: str
    address: Optional[str]

class Tag(PyfireDoc):
    name: str

class Book(PyfireDoc):
    title: str
    user_id: str
    PyfireDoc.belongs_to(User)  # Make accessible via book.user
    published_at: datetime
    authors: list[str]
    tags: PyfireCollection[Tag] = PyfireCollection(Tag)
    publisher_ref: DocumentRef[Publisher]


FirestoreConnection().initialize(project_id="YOUR_PROJECT_ID")
PyFireConsole().run()
