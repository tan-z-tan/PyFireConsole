from datetime import datetime
from typing import Optional
from pyfireconsole.models.association import belongs_to
from pyfireconsole.models.pyfire_model import PyfireCollection, DocumentRef, PyfireDoc
from pyfireconsole.db.connection import FirestoreConnection

"""
We assume that you have a firestore database with the following structure:
- users Collection
    - {user_id} Document
        - name: str
        - email: str
- publishers Collection
    - {publisher_id} Document
        - name: str
        - address: str
- books Collection
    - {book_id} Document
        - title: str
        - user_id: str
        - published_at: datetime
        - authors: list[str]
        - tags: Sub Collection
            - {tag_id} Document
                - name: str
        - publisher_ref: Reference
"""


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


FirestoreConnection().initialize(project_id="promptr-dev-prod")
# or you can specify service_account_key_path
# FirestoreConnection().initialize(service_account_key_path="./serviceaccount.json", project_id="YOUR_PROJECT_ID")

print("==================== find ====================")
book = Book.find("XlvQHeGi3cODbI4MQpI3")  # => Book
print(book.model_dump())  # => dict
print(f"ID: {book.id} | Title: {book.title} | Authors: {book.authors} | Published At: {book.published_at.isoformat()}")

print("==================== belongs_to ====================")
print(book.user)  # => User
print(book.user.name)  # => str

print("==================== reference ====================")
print(book.publisher_ref)  # => DocumentRef
print(book.publisher_ref.path)  # => str (So far, we can't access publisher_ref.name directly for ref type)

print("==================== where ====================")
print(Book.where("title", "==", "test"))  # => Book[] Make sure to create index in firestore for compound queries
