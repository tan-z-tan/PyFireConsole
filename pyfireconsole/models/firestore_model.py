from typing import Generic, Iterable, Optional, Type, TypeVar
from pydantic import BaseModel
import inflect
from pyfireconsole.queries.query_runner import QueryRunner


ModelType = TypeVar('ModelType', bound='PyfireDoc')


class PyfireCollection(Generic[ModelType]):
    model_class: Type[ModelType]
    _parent_model: 'PyfireDoc'
    _collection: Optional[Iterable[ModelType]]

    def __init__(self, model_class: Type[ModelType]):
        self.model_class = model_class

    def __iter__(self):
        self._collection = self._parent_model._get_subcollection(self)
        for model in self._collection:
            model._parent = self._parent_model
            yield model

    def obj_collection_name(self) -> str:
        if self._parent_model is None:
            raise Exception("Collection parent model is not set")
        return f"{self._parent_model.obj_collection_name()}/{self._parent_model.id}/{inflect.engine().plural(self.model_class.__name__).lower()}"

    def where(self, field: str, operator: str, value: str) -> list[ModelType]:
        docs = QueryRunner(self.obj_collection_name()).where(field, operator, value)
        return [self.model_class.model_validate(d) for d in docs]

    def set_parent(self, parent_model: 'PyfireDoc'):
        self._parent_model = parent_model
        self._collection = None  # Invalidate cached data


class DocumentRef(BaseModel, Generic[ModelType]):
    path: str

    # TODO: Implement reference class so that we can do this like this:
    # book.user_ref.get() => User object


class PyfireDoc(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: str  # Firestore document id
    _parent: Optional['PyfireDoc'] = None  # when a model is a subcollection, this is the parent model

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

    def _get_subcollection(self, collection: PyfireCollection) -> Iterable[ModelType]:
        collection_name = f"{self.obj_collection_name()}/{self.id}/{inflect.engine().plural(collection.model_class.__name__).lower()}"
        docs = QueryRunner(collection_name).all()
        for doc in docs:
            yield collection.model_class(**doc)

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
        d = QueryRunner(cls.collection_name()).get(id)

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
        docs = QueryRunner(cls.collection_name()).where(field, operator, value)
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
