from typing import Generic, Iterable, Optional, Type, TypeVar, get_origin

import inflect
from pydantic import BaseModel

from pyfireconsole.queries.get_query import DocNotFoundException
from pyfireconsole.queries.query_runner import QueryRunner
from pyfireconsole.queries.where_clouse import WhereCondition

ModelType = TypeVar('ModelType', bound='PyfireDoc')


class PyfireCollection(Generic[ModelType]):
    model_class: Type[ModelType]
    _parent_model: Optional['PyfireDoc'] = None
    _collection: Optional[Iterable[dict]] = None
    _where_cond: Optional[WhereCondition] = None

    def __init__(self, model_class: Type[ModelType]):
        self.model_class = model_class

    def obj_ref_key(self) -> str:
        """ Represents the key of firestore entity """
        return self.obj_collection_name()

    def set_parent(self, parent_model: 'PyfireDoc'):
        self._parent_model = parent_model

    def obj_collection_name(self) -> str:
        leaf_collection_name = self.model_class.collection_name()
        if self._parent_model is None:
            return leaf_collection_name  # e.g. "users"
        else:
            return f"{self._parent_model.obj_ref_key()}/{leaf_collection_name}"  # e.g. "users/123/books"

    def __iter__(self):
        if self._where_cond is not None:
            self._collection = QueryRunner(self.obj_ref_key()).where(self._where_cond.field, self._where_cond.operator, self._where_cond.value)
        else:
            self._collection = QueryRunner(self.obj_ref_key()).all()

        for doc in self._collection:
            doc = self.model_class.model_field_load(doc)
            obj = self.model_class(**doc)
            obj._parent = self
            yield obj

    def first(self) -> ModelType | None:
        try:
            return next(iter(self))
        except StopIteration:
            return None

    def where(self, field: str, operator: str, value: str) -> 'PyfireCollection[ModelType]':
        coll = PyfireCollection(self.model_class)
        coll._where_cond = WhereCondition(field, operator, value)
        if self._parent_model is not None:
            coll.set_parent(self._parent_model)

        return coll

    def add(self, entity: ModelType) -> ModelType:
        assert isinstance(entity, self.model_class)

        entity._parent = self
        data = entity.model_field_dump()
        if entity.id is None:
            _id = QueryRunner(self.obj_collection_name()).create(data)
            if _id:
                entity.id = _id
        else:
            raise ValueError("Could not save document")

        return entity

    def __str__(self) -> str:
        if self._parent_model is None:
            return f"{self.__class__.__name__}[{self.model_class.__name__}]"
        return f"{self.__class__.__name__}[{self.model_class.__name__}](parent={self._parent_model.__class__.__name__})"


class DocumentRef(BaseModel, Generic[ModelType]):
    path: str

    # TODO: Implement reference class so that we can do this like this:
    # book.user_ref.get() => User object


class PyfireDoc(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: Optional[str] = None  # Firestore document id
    _parent: Optional[PyfireCollection] = None  # when a model is a subcollection, this is the parent model

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
        """ Represents the key of firestore entity """
        return f"{self.obj_collection_name()}/{self.id}"

    def obj_collection_name(self) -> str:
        """ Represents the name of firestore collection """
        db_name = self.__class__.collection_name()
        if self._parent is None:
            return f"{db_name}"
        else:
            return self._parent.obj_ref_key()

    def model_field_dump(self) -> dict:
        """
        Returns the model fields as dict. This is used for saving the model to firestore.
        Does not include collection fields.
        """
        data = self.model_dump()

        for name, _ in self.__annotations__.items():
            attr = getattr(self, name, None)
            if isinstance(attr, PyfireCollection):
                data.pop(name)
        # if "id" in data:  # TODO when original doc has id field. This should be False?
        #     data.pop('id')

        return data

    @classmethod
    def model_field_load(cls, data: dict) -> dict:
        """
        Filters out collection fields from the data dict.
        """
        for name, klass in cls.__annotations__.items():
            if name not in data:
                continue
            if get_origin(klass) == PyfireCollection:
                data.pop(name)
        return data

    def save(self) -> 'PyfireDoc':
        data = self.model_field_dump()
        if self.id is None:
            _id = QueryRunner(self.obj_collection_name()).create(data)
            if _id:
                self.id = _id
        else:
            _id = QueryRunner(self.obj_collection_name()).save(self.id, data)

        if _id is None:
            raise ValueError("Could not save document")
        return self

    @classmethod
    def new(cls, **kwargs) -> 'PyfireDoc':
        doc = cls(**kwargs)
        return doc

    @classmethod
    def find(cls, id: str, allow_empty: bool = False) -> 'PyfireDoc':
        try:
            d = QueryRunner(cls.collection_name()).get(id)
            if d is None:
                raise DocNotFoundException(f"Document {cls.collection_name()}/{id} not found")
            d = cls.model_field_load(d)
        except DocNotFoundException as e:
            if allow_empty:
                return cls.empty_doc(id)
            else:
                raise e
        return cls.model_validate(d)

    @classmethod
    def first(cls) -> Optional['PyfireDoc']:
        coll = PyfireCollection(cls)
        return coll.first()

    @classmethod
    def empty_doc(cls, id) -> 'PyfireDoc':
        doc = cls.model_construct(id=id)
        doc._setup_collections()
        return doc

    @classmethod
    def where(cls, field: str, operator: str, value: str) -> PyfireCollection['PyfireDoc']:
        coll = PyfireCollection(cls)
        coll._where_cond = WhereCondition(field, operator, value)
        return coll

    @classmethod
    def collection_name(cls) -> str:
        """
        Override this method to change the name of the collection in Firestore
        """
        return inflect.engine().plural(cls.__name__).lower()
