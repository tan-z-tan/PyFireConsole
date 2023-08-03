from datetime import datetime
from typing import Optional
from pyfireconsole.models.firestore_model import Collection, DocumentRef, FirestoreModel
from pyfireconsole.db.connection import FirestoreConnection
from pyfireconsole import PyFireConsole

class User(FirestoreModel):
    name: str
    email: str

class Publisher(FirestoreModel):
    name: str
    address: Optional[str]

class Tag(FirestoreModel):
    name: str

class Book(FirestoreModel):
    title: str
    user_id: str
    FirestoreModel.belongs_to(User)  # Make accessible via book.user
    published_at: datetime
    authors: list[str]
    tags: Collection[Tag] = Collection(Tag)
    publisher_ref: DocumentRef[Publisher]


FirestoreConnection().initialize(project_id="YOUR_PROJECT_ID")
PyFireConsole().run()
