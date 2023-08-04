from typing import Generic, Iterable, Optional, Type, TypeVar

import inflect
from pydantic import BaseModel

from pyfireconsole.queries.query_runner import QueryRunner

ModelType = TypeVar('ModelType', bound='PyfireDoc')


class PyfireCollection(Generic[ModelType]):
    model_class: Type[ModelType]
    _parent_model: Optional['PyfireDoc']
    _collection: Iterable[ModelType] = []

    def __init__(self, model_class: Type[ModelType]):
        self.model_class = model_class
        self._parent_model = None

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
        docs = QueryRunner(self.obj_ref_key()).all()

        for doc in docs:
            obj = self.model_class(**doc)
            obj._parent = self._parent_model
            yield obj

    def where(self, field: str, operator: str, value: str) -> 'PyfireCollection[ModelType]':
        coll = PyfireCollection(self.model_class)
        if self._parent_model is not None:
            coll.set_parent(self._parent_model)
        docs = QueryRunner(self.obj_collection_name()).where(field, operator, value)
        coll._collection = [self.model_class.model_validate(d) for d in docs]
        return coll

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

    id: str  # Firestore document id
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
        db_name = self.__class__.collection_name()
        if self._parent is None:
            return f"{db_name}/{self.id}"
        else:
            return f"{self._parent.obj_ref_key()}/{db_name}/{self.id}"

    def save(self) -> None:
        raise NotImplementedError

    @classmethod
    def find(cls, id: str, allow_empty: bool = False) -> 'PyfireDoc':
        d = QueryRunner(cls.collection_name()).get(id)

        if d is None:
            if allow_empty:
                return cls.empty_doc(id)
            else:
                raise ValueError(f"Could not find {cls.__name__} with id {id}")
        return cls.model_validate(d)

    @classmethod
    def empty_doc(cls, id) -> 'PyfireDoc':
        doc = cls.model_construct(id=id)
        doc._setup_collections()
        return doc

    @classmethod
    def where(cls, field: str, operator: str, value: str) -> PyfireCollection['PyfireDoc']:
        coll = PyfireCollection(cls)
        docs = QueryRunner(cls.collection_name()).where(field, operator, value)
        coll._collection = [cls.model_validate(d) for d in docs]
        return coll
        # docs = QueryRunner(cls.collection_name()).where(field, operator, value)
        # return [cls.model_validate(d) for d in docs]

    @classmethod
    def collection_name(cls) -> str:
        """
        Override this method to change the name of the collection in Firestore
        """
        return inflect.engine().plural(cls.__name__).lower()

    @classmethod
    def belongs_to(cls, model_class: Type[ModelType], db_field: Optional[str] = None, attr_name: Optional[str] = None):
        def getter_method(self):
            model_id = getattr(self, db_field)
            if model_id:
                return model_class.find(model_id)
            else:
                return None

        db_field = db_field or f"{model_class.__name__.lower()}_id"
        attr_name = attr_name or model_class.__name__.lower()
        setattr(cls, model_class.__name__.lower(), property(getter_method))

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({super().__str__()})"
