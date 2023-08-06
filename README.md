[![Python package](https://github.com/tan-z-tan/PyFireConsole/actions/workflows/test.yml/badge.svg)](https://github.com/tan-z-tan/PyFireConsole/actions/workflows/test.yml)

<h1 style="text-align: center;">
  <img src="https://raw.githubusercontent.com/tan-z-tan/pyfireconsole/main/logo.png" alt="PyFireConsole">
</h1>

## Introduction
Inspired by Rails console, PyFireConsole provides a seamless interface to Google's Firestore in Python, simplifying tasks such as connection, ORM, and data associations. It makes managing Firestore a breeze.

## Features
- Model Definition and ORM: Define your Firestore data models within Python and use object-relational mapping (ORM) for easier data manipulation and querying.
- Data Associations: Effortlessly manage relationships between your Firestore data models.
- Interactive Console: Inspired by the Rails console, PyFireConsole provides a console for interactive data manipulation and querying, making it simple to perform tasks on your Firestore data.

## Installation
```sh
pip install pyfireconsole
```

## Getting Started
```python
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


# Initialize FirestoreConnection using your default credentials of gcloud. (use `gcloud auth application-default login` or set GOOGLE_APPLICATION_CREDENTIALS)
FirestoreConnection().initialize(project_id="YOUR-PROJECT-ID")

# Or you can specify service_account_key_path
# FirestoreConnection().initialize(service_account_key_path="./service-account.json", project_id="YOUR-PROJECT-ID")

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
```

We assume that you have a firestore database with the following structure:
```
=== Firestore Database ===
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
```

## Interactive Console
PyFireConsole comes with an interactive console that allows developer to view and manipulate Firestore data in a live and easily.
This feature is inspired by the Rails console.

How to setup interactive console:

```python
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


FirestoreConnection().initialize(project_id="YOUR_PROJECT_ID")
PyFireConsole().run()
```


Alternatively, you can define your model files in `app/models/` and initialize the console as follows:

```python
from pyfireconsole.db.connection import FirestoreConnection
from pyfireconsole import PyFireConsole
from pyfireconsole.models.association import resolve_pyfire_model_names

# Resolve PyfireModel names
resolve_pyfire_model_names(globals())


FirestoreConnection().initialize(project_id="YOUR-PROJECT-ID")
PyFireConsole(model_dir="app/models").run()
```

Through the interactive console, you can conveniently test and experiment with your Firestore data models.

## Contributing
Your contributions to PyFireConsole are warmly welcomed! Feel free to submit a pull request directly if you have any improvements or features to suggest. For any questions or issues, please create an issue on Github. Thank you for your interest in improving PyFireConsole!

## License
PyFireConsole is released under the MIT License.

This means you are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software. This permission is granted provided that the above copyright notice and this permission notice are included in all copies or substantial portions of the software.
