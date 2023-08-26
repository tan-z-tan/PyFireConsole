[![Python package](https://github.com/tan-z-tan/PyFireConsole/actions/workflows/test.yml/badge.svg)](https://github.com/tan-z-tan/PyFireConsole/actions/workflows/test.yml)

<h1 style="text-align: center;">
  <img src="https://raw.githubusercontent.com/tan-z-tan/pyfireconsole/main/logo.png" alt="PyFireConsole">
</h1>

## Introduction
Inspired by Rails console, PyFireConsole provides a seamless interface to Google's Firestore in Python, simplifying tasks such as connection, ORM, and data associations. It makes managing Firestore a breeze.

<img src="https://github.com/tan-z-tan/PyFireConsole/assets/2078683/1e4e51a0-ac3f-4f75-96f3-6cf72fa627b6"></img>

## Features
- Model Definition and ORM: Define your Firestore data models within Python and use object-relational mapping (ORM) for easier data manipulation and querying.
- Data Associations: Effortlessly manage relationships between your Firestore data models.
- Interactive Console: Inspired by the Rails console, PyFireConsole provides a console for interactive data manipulation and querying, making it simple to perform tasks on your Firestore data.

## Installation
```sh
pip install pyfireconsole
```

## Getting Started
### Connect to Firestore
First of all, you need to initialize `FirestoreConnection` with your project id.
```python
# Initialize FirestoreConnection using your default credentials of gcloud. (use `gcloud auth application-default login` or set GOOGLE_APPLICATION_CREDENTIALS)
FirestoreConnection().initialize(project_id="YOUR-PROJECT-ID")

# Or you can specify service_account_key_path
FirestoreConnection().initialize(service_account_key_path="./service-account.json", project_id="YOUR-PROJECT-ID")
```

### Find a document by id
Like Rails, you can define your model class by inheriting `PyfireDoc` class.
```python
from pyfireconsole.models.pyfire_model import PyfireDoc

class User(PyfireDoc):
    name: str
    email: str
    role: str = "user"

# Find a document by id
user = User.find("XXX")
#=> User[users/XXX](id='XXX', name='John', email='john@example.com', role='user')

# Nested document can be accessed by path
user = User.find("companies/ZZZ/users/YYY")
#=> User[companies/ZZZ/users/YYY](id='YYY', name='John', email='john@example.com', role='user')
```

### Where query
You can use `where` method to query documents.
```python
admin_users = User.where("role", "==", "admin")
#=> PyfireCollection<User>[users]

# admin_user is iterable
for user in admin_users:
    print(user)
    #=> User[users/YYYYYYYYYY](id='YYYYYYYYYY', name='Mary', email='mary@example.com', role='admin')
```

### Sub collection
You can define sub collection of a document by using `PyfireCollection` class.
```python
from pyfireconsole.models.pyfire_model import PyfireCollection, DocumentRef, PyfireDoc

# Tag is sub collection of Book
class Tag(PyfireDoc):
    name: str

class Book(PyfireDoc):
    title: str
    user_id: str
    published_at: datetime
    tags: PyfireCollection[Tag] = PyfireCollection(Tag)  # Specify sub collection type


book = Book.find("XXXX")
for tag in book.tags:
    print(tag)
    #=> Tag[books/XXXX/tags/YYYY](id='YYYY', name='Python')
```

### has_many, belongs_to
You can define data associations by using `has_many` and `belongs_to` decorators.

Now `book.user` returns `User` object, and `user.books` returns `PyfireCollection[Book]` object.

```python
from pyfireconsole.models.association import belongs_to, has_many, resolve_pyfire_model_names
from pyfireconsole.models.pyfire_model import PyfireCollection, DocumentRef, PyfireDoc


@has_many('Book', db_field="user_id", attr_name="my_books")
class User(PyfireDoc):
    name: str
    email: str

class Tag(PyfireDoc):
    name: str

@belongs_to(User, "user_id")
class Book(PyfireDoc):
    title: str
    user_id: str
    published_at: datetime
    tags: PyfireCollection[Tag] = PyfireCollection(Tag)

# call this to resolve model names (this is because of python's circular import problem)
resolve_pyfire_model_names(globals())

user = User.find("YYYY")
user.my_books
=> PyfireCollection[Book][books]

user.my_books.first.user
=> User[users/XXXX](id='XXXX', name='John', email="john@example.com")
```

### as_json
You can convert PyfireDoc object to json serializable dict by using `as_json` method.
```python
# dump all admin users, not including sub collection
User.all().as_json()

# dump all admin users, not including sub collection
User.where("role", "==", "admin").as_json()

# dump all admin users, including sub collection
User.where("role", "==", "admin").as_json(recursive=True)

# you can also dump custom attributes
class User(PyfireDoc):
    name: str
    email: str

    def email_domain(self):
        return self.email.split("@")[1]

User.where("role", "==", "admin").as_json(recursive=True, include=["email_domain"])
```

### Empty document
You can instantiate empty document by using `allow_empty` option. The sub collection of empty document can be accessed.

```python
# This is empty document which doesn't exist in firestore but sub collection exists.
user = User.find("XXXXX", allow_empty=True)

# You can't access empty document's attributes
# user.name => AttributeError: 'User' object has no attribute 'name'

# You can access sub collection of empty document
print([n.title for n in user.books])
```

### Example
We assume that you have a firestore database with the following structure:

```
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

```python
from datetime import datetime
from typing import Optional
from pyfireconsole.models.association import belongs_to
from pyfireconsole.models.pyfire_model import PyfireCollection, DocumentRef, PyfireDoc
from pyfireconsole.db.connection import FirestoreConnection


# Define models
# PyfireDoc is a subclass of Pydantic(2.x) BaseModel. You can use Pydantic's features.
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

print("==================== where & order ====================")
print(Book.where("title", "==", "test").order("published_at", "ASCENDING"))  # => Book[] Make sure to create index in firestore for compound queries

print("==================== has_many ====================")
print(book.tags)  # => PyfireCollection[Tag]
print(book.tags.first)  # => Tag
```

## Interactive Console
PyFireConsole comes with an interactive console that allows developer to view and manipulate Firestore data in a live and easily.
This feature is inspired by the Rails console.

First, you need to define your models.
```python
# app/models/models.py

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
```

Start interactive console by using `pyfireconsole` command.
```bash
pyfireconsole --model-dir app/models
```
This command loads all python classes in `app/models` directory and starts interactive console.

- --model-di: model directory path
- --project-id: project id (optional)
- --service-account-key-path: service account key path (optional)

### Invoke console from your code
You can also call `PyFireConsole().run()` from your code.

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
# Call this function when you define your models by using str class name. e.g. @has_many('Book', "user_id")
resolve_pyfire_model_names(globals())


FirestoreConnection().initialize(project_id="YOUR_PROJECT_ID")
PyFireConsole().run()
```

Through the interactive console, you can conveniently test and experiment with your Firestore data models.

## Contributing
Your contributions to PyFireConsole are warmly welcomed! Feel free to submit a pull request directly if you have any improvements or features to suggest. For any questions or issues, please create an issue on Github. Thank you for your interest in improving PyFireConsole!

## License
PyFireConsole is released under the MIT License.

This means you are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software. This permission is granted provided that the above copyright notice and this permission notice are included in all copies or substantial portions of the software.
