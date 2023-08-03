from typing import Generic, Iterable, Optional, Type, TypeVar
from pydantic import BaseModel
import inflect
from pyfireconsole.queries.query_manager import QueryManager


ModelType = TypeVar('ModelType', bound='FirestoreModel')


class Collection(Generic[ModelType]):
    parent_model: Optional['FirestoreModel'] = None
    model_class: Optional[Type[ModelType]] = None
    _collection: Optional[Iterable[ModelType]] = None

    def __init__(self, model_class: Type[ModelType]):
        self.model_class = model_class

    def __iter__(self):
        self._collection = self.parent_model._get_subcollection(self)
        for model in self._collection:
            model._parent = self.parent_model
            yield model

    @classmethod
    def __get_validators__(cls):
        breakpoint()
        yield cls.validate

    @classmethod
    def validate(cls, v, _):
        breakpoint()
        if isinstance(v, cls):
            return v

        if isinstance(v, Type) and issubclass(v, FirestoreModel):
            return cls(v)

        raise ValueError("Invalid value for a Collection field")

    def set_parent(self, parent_model: 'FirestoreModel'):
        self.parent_model = parent_model
        self._collection = None  # Invalidate cached data


class DocumentRef(BaseModel, Generic[ModelType]):
    path: str

    # TODO: Implement reference class so that we can do this like this:
    # book.user_ref.get() => User object


class FirestoreModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: str
    _parent: Optional['FirestoreModel'] = None  # when a model is a subcollection, this is the parent model

    def __init__(self, **data):
        super().__init__(**data)
        self._setup_collections()

    def _setup_collections(self):
        # Set the parent of all the collections
        for name, _ in self.__annotations__.items():
            attr = getattr(self, name)
            if isinstance(attr, Collection):
                attr.set_parent(self)
            elif isinstance(attr, DocumentRef):
                pass

    def _get_subcollection(self, collection: Collection) -> Iterable[ModelType]:
        collection_name = f"{self.obj_collection_name()}/{self.id}/{inflect.engine().plural(collection.model_class.__name__).lower()}"
        query_manager = QueryManager(collection_name)
        for id, data in query_manager.all():
            yield collection.model_class(**data, id=id)

    def obj_collection_name(self) -> str:
        db_name = self.__class__.collection_name()
        if self._parent is None:
            return db_name
        else:
            return f"{self._parent.obj_collection_name()}/{self._parent.id}/{db_name}"

    def save(self):
        raise NotImplementedError("save() is not implemented")

    @classmethod
    def find(cls, id: str, allow_empty: bool = False) -> ModelType:
        query_manager = QueryManager(cls.collection_name())
        d = query_manager.get(id)

        if d is None:
            if allow_empty:
                empty_doc = cls.model_construct(id=id)
                empty_doc._setup_collections()
                return empty_doc
            else:
                raise ValueError(f"Could not find {cls.__name__} with id {id}")
        return cls.model_validate(d)

    @classmethod
    def empty_doc(cls, id) -> ModelType:
        return cls(id=id)

    @classmethod
    def where(cls, field: str, operator: str, value: str) -> list[ModelType]:
        query_manager = QueryManager(cls.collection_name())
        docs = query_manager.where(field, operator, value)
        return [cls.model_validate(d) for d in docs]

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
