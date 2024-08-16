from typing import Generic, Iterable, Optional, Type, TypeVar, get_origin

import inflection
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from pydantic import BaseModel, ConfigDict

from pyfireconsole.queries.get_query import DocNotFoundException
from pyfireconsole.queries.order_query import OrderCondition, OrderDirection
from pyfireconsole.queries.query_runner import QueryRunner
from pyfireconsole.queries.where_clouse import WhereCondition

ModelType = TypeVar('ModelType', bound='PyfireDoc')


class PyfireCollection(Generic[ModelType]):
    model_class: Type[ModelType]
    _parent_model: Optional['PyfireDoc'] = None
    _collection: Optional[Iterable[dict]] = None
    _where_cond: Optional[WhereCondition] = None
    _order_cond: Optional[OrderCondition] = None
    _limit: int = 1000  # default limit to prevent loading too large collections

    def __init__(self, model_class: Type[ModelType]):
        self.model_class = model_class

    def obj_ref_key(self) -> str:
        """
        Represents the key of firestore entity
        Returns:
            str: The Firestore entity key.
        """
        return self.obj_collection_name()

    def set_parent(self, parent_model: 'PyfireDoc'):
        self._parent_model = parent_model

    def obj_collection_name(self) -> str:
        """
        Get the Firestore collection name for the object.

        Returns:
            str: The Firestore collection name.
        """
        leaf_collection_name = self.model_class.collection_name()
        if self._parent_model is None:
            return leaf_collection_name  # e.g. "users"
        else:
            return f"{self._parent_model.obj_ref_key()}/{leaf_collection_name}"  # e.g. "users/123/books"

    def __iter__(self):
        """
        Iterator to loop through the collection.

        Yields:
            ModelType: The current document in the collection iteration.
        """
        query = QueryRunner(self.obj_ref_key())
        if self._where_cond is not None:
            query = query.where(self._where_cond.field, self._where_cond.operator, self._where_cond.value)
        else:
            query = query.all()

        if self._order_cond is not None:
            query = query.order(self._order_cond.field, self._order_cond.direction)

        self._collection = query.limit(self._limit).iter()

        self._collection = query.iter()

        for doc in self._collection:
            doc = self.model_class._doc_field_load(doc)
            obj = self.model_class(**doc)
            obj._parent = self
            yield obj

    def as_json(self, recursive: bool = False, include: list[str] = [], excepts: list[str] = []) -> list[dict]:
        """
        Dump the collection to a list of dictionaries.

        Args:
            recursive (bool): Whether to dump the collection recursively.
            include (list[str]): A list of fields to include in the dump.

        Returns:
            list[dict]: The collection as a list of dictionaries.
        """
        return [obj.as_json(recursive, include, excepts) for obj in self]

    def first(self) -> ModelType | None:
        """
        Get the first document in the collection.

        Returns:
            ModelType or None: The first document or None if the collection is empty.
        """
        try:
            return next(iter(self))
        except StopIteration:
            return None

    def where(self, field: str, operator: str, value: str) -> 'PyfireCollection[ModelType]':
        """
        Filter the collection based on the given condition.

        Args:
            field (str): The field name to apply the filter on.
            operator (str): The comparison operator (e.g., '==', '>', '<').
            value (str): The value to compare against.

        Returns:
            PyfireCollection[ModelType]: A new PyfireCollection instance with the applied filter.
        """
        coll = PyfireCollection(self.model_class)
        coll._where_cond = WhereCondition(field, operator, value)
        if self._parent_model is not None:
            coll.set_parent(self._parent_model)

        return coll

    def order(self, field: str, direction: str = 'ASCENDING') -> 'PyfireCollection[ModelType]':
        """
        Order the collection based on the given condition.

        Args:
            field (str): The field name to apply the order on.
            direction (str): The order direction, 'ASCENDING' or 'DESCENDING'. Defaults to 'ASCENDING'.

        Returns:
            PyfireCollection[ModelType]: A new PyfireCollection instance with the applied order.
        """
        coll = PyfireCollection(self.model_class)
        coll._where_cond = self._where_cond
        coll._order_cond = OrderCondition(field, direction)
        if self._parent_model is not None:
            coll.set_parent(self._parent_model)

        return coll

    def all(self) -> 'PyfireCollection[ModelType]':
        """
        Get all documents in the collection.

        Returns:
            PyfireCollection[ModelType]: A new PyfireCollection instance containing all documents.
        """
        coll = PyfireCollection(self.model_class)
        coll._where_cond = self._where_cond
        coll._order_cond = self._order_cond
        coll._limit = self._limit
        if self._parent_model is not None:
            coll.set_parent(self._parent_model)

        return coll

    def to_a(self, limit: int = 1000) -> list[ModelType]:
        """
        Convert the collection to a list.

        Returns:
            list[ModelType]: The collection as a list.
        """
        return list(self)

    def add(self, entity: ModelType) -> ModelType:
        """
        Add a new document to the collection.

        Args:
            entity (ModelType): The document to be added.

        Returns:
            ModelType: The added document.
        """
        assert isinstance(entity, self.model_class)

        entity._parent = self
        data = entity.as_json(recursive=False)
        if entity.id is None:
            _id = QueryRunner(self.obj_collection_name()).create(data)
            if _id:
                entity.id = _id
        else:
            raise ValueError("Could not save document")

        return entity

    def __str__(self) -> str:
        return f"{self.__class__.__name__}<{self.model_class.__name__}>[{self.obj_ref_key()}]"


class DocumentRef(BaseModel, Generic[ModelType]):
    path: str

    @property
    def id(self) -> str:
        """
        Get the ID of the document from the path.

        Returns:
            str: The ID of the document.
        """
        return self.path.split('/')[-1]

    def get(self, model_class: Type[ModelType]) -> 'PyfireDoc':
        """
        Retrieve the document corresponding to the current reference.

        Args:
            model_class (Type[ModelType]): The class of the model to retrieve.

        Returns:
            PyfireDoc: The retrieved document.
        """
        return model_class.find(self.id)


class PyfireDoc(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[str] = None  # Firestore document id
    _parent: Optional[PyfireCollection] = None  # when a model is a subcollection, this is the parent model
    _path: Optional[str] = None  # firestore path

    def __init__(self, **data):
        super().__init__(**data)
        self._setup_collections()

    def _setup_collections(self):
        # Set the parent of all the collections
        for name, _ in self.__annotations__.items():
            attr = getattr(self, name, None)
            if isinstance(attr, PyfireCollection):
                attr.set_parent(self)
            elif isinstance(attr, DocumentRef):
                pass

    def obj_ref_key(self) -> str:
        """
        Represents the key of firestore entity

        Returns:
            str: The Firestore entity key.
        """
        if self._path is not None:
            return self._path
        else:
            return f"{self.obj_collection_name()}/{self.id}"

    def obj_collection_name(self) -> str:
        """
        Get the Firestore collection name for the document.

        Returns:
            str: The Firestore collection name.
        """
        if self._path is not None:
            return self._path.rsplit('/', 1)[0]
        else:
            db_name = self.__class__.collection_name()
            if self._parent is None:
                return f"{db_name}"
            else:
                return self._parent.obj_ref_key()

    def as_json(self, recursive: bool = False, include: list[str] = [], excepts: list[str] = []) -> dict:
        """
        Returns the model fields as dict. This is used for saving the model to firestore.

        Args:
            recursive (bool, optional): Whether to recursively dump the subcollections. Defaults to True.
            include (list[str], optional): A list of fields to include in the dump. Defaults to [].
            excepts (list[str], optional): A list of fields to exclude from the dump. Defaults to [].

        Returns:
            dict: The model fields as dict.
        """
        data = super().model_dump()

        for name, _klass in self.__annotations__.items():
            if name in excepts:
                continue

            attr = getattr(self, name, None)
            if isinstance(attr, PyfireCollection):
                if recursive:
                    data[name] = attr.as_json(recursive=True)
                else:
                    data.pop(name)
            elif isinstance(attr, DatetimeWithNanoseconds):
                data[name] = attr.rfc3339()
            if name in include:
                include.remove(name)

        for name in excepts:
            data.pop(name)

        for name in include:
            if name not in data:
                attr = getattr(self, name)
                if isinstance(attr, PyfireCollection):
                    data[name] = attr.as_json(recursive=recursive)
                elif isinstance(attr, PyfireDoc):
                    data[name] = attr.as_json(recursive=recursive)
                elif callable(attr):
                    data[name] = attr()
                else:
                    data[name] = attr

        return data

    @classmethod
    def _doc_field_load(cls, data: dict) -> dict:
        """
        Filters out non document fields from the data dict.
        """
        for name, klass in cls.__annotations__.items():
            if name not in data:
                continue
            if get_origin(klass) == PyfireCollection:
                data.pop(name)
        return data

    def save(self) -> 'PyfireDoc':
        """
        Save or update the current document in Firestore.

        Returns:
            PyfireDoc: The saved document.
        """
        data = self.as_json(recursive=False)
        if self.id is None:
            _id = QueryRunner(self.obj_collection_name()).create(data)
            if _id:
                self.id = _id
        else:
            _id = QueryRunner(self.obj_collection_name()).save(self.id, data)

        if _id is None:
            raise ValueError("Could not save document")
        return self

    def delete(self) -> bool:
        """
        Deletes the current document from Firestore.
        Returns True if deletion is successful, False otherwise.
        """
        if self.id is None:
            raise ValueError("Document ID is not set.")

        result = QueryRunner(self.obj_collection_name()).delete(self.id)
        return result

    def update(self, **kwargs) -> 'PyfireDoc':
        """
        Updates the current document with provided fields.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.save()
        return self

    @classmethod
    def count(cls) -> int:
        """
        Returns the count of documents in the collection.
        This only works for top level collections.
        """
        return len(QueryRunner(cls.collection_name()).all())

    @classmethod
    def exists(cls, id: str) -> bool:
        """
        Checks if a document exists by its ID.
        """
        try:
            cls.find(id)
            return True
        except DocNotFoundException:
            return False

    @classmethod
    def new(cls, **kwargs) -> 'PyfireDoc':
        """
        Create a new instance of the document without saving it to Firestore.

        Returns:
            PyfireDoc: The new document instance.
        """
        doc = cls(**kwargs)
        return doc

    @classmethod
    def find(cls, path: str, allow_empty: bool = False) -> 'PyfireDoc':
        """
        Find a document by its path or ID.

        Args:
            path (str): The document's path or ID.
            allow_empty (bool, optional): If True, returns an empty document if not found. Defaults to False.

        Returns:
            PyfireDoc: The found document.
        """
        if path.find('/') == -1:
            collection_name = cls.collection_name()
            id = path
            path = f"{collection_name}/{id}"
        else:
            collection_name, id = path.rsplit('/', 1)

        try:
            d = QueryRunner(collection_name).get(id)
            if d is None:
                raise DocNotFoundException(f"Document {collection_name}/{id} not found")
            d = cls._doc_field_load(d)
        except DocNotFoundException as e:
            if allow_empty:
                return cls._empty_doc(id)
            else:
                raise e
        obj = cls.model_validate(d)
        obj._path = path
        return obj

    @classmethod
    def first(cls) -> Optional['PyfireDoc']:
        """
        Get the first document in the collection.

        Returns:
            PyfireDoc or None: The first document or None if the collection is empty.
        """
        coll = PyfireCollection(cls)
        return coll.first()

    @classmethod
    def _empty_doc(cls, id) -> 'PyfireDoc':
        """
        Create an empty document with the given ID.

        Args:
            id (str): The ID for the empty document.

        Returns:
            PyfireDoc: The empty document.
        """
        doc = cls.model_construct(id=id)
        doc._setup_collections()
        return doc

    @classmethod
    def where(cls, field: str, operator: str, value: str) -> PyfireCollection['PyfireDoc']:
        """
        Filter the documents based on the given condition.

        Args:
            field (str): The field name to apply the filter on.
            operator (str): The comparison operator (e.g., '==', '>', '<').
            value (str): The value to compare against.

        Returns:
            PyfireCollection[PyfireDoc]: A PyfireCollection instance with the applied filter.
        """
        coll = PyfireCollection(cls)
        coll._where_cond = WhereCondition(field, operator, value)
        return coll

    @classmethod
    def order(cls, field: str, direction: OrderDirection = "ASCENDING") -> PyfireCollection['PyfireDoc']:
        """
        Order the documents based on the given field.

        Args:
            field (str): The field name to apply the order on.
            direction (str, optional): The order direction ('ASCENDING' or 'DESCENDING'). Defaults to 'ASCENDING'.

        Returns:
            PyfireCollection[PyfireDoc]: A PyfireCollection instance with the applied order.
        """
        # check if direction is valid
        direction = OrderDirection(direction)

        coll = PyfireCollection(cls)
        coll._order_cond = OrderCondition(field, direction)
        return coll

    @classmethod
    def all(cls) -> PyfireCollection['PyfireDoc']:
        """
        Get all documents in the collection.
        Be careful when using this method as it can be very slow for large collections.

        Returns:
            PyfireCollection[PyfireDoc]: A PyfireCollection instance containing all documents.
        """
        coll = PyfireCollection(cls)
        return coll

    @classmethod
    def collection_name(cls) -> str:
        """
        Override this method to change the name of the collection in Firestore

        Returns:
            str: The Firestore collection name.
        """
        return inflection.tableize(cls.__name__)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}[{self.obj_ref_key()}]({super.__str__(self).split('(', 1)[1]}"
