from typing import Any, Optional, Type, Union

import inflection

from pyfireconsole.models.pyfire_model import PyfireDoc

# Pending relationships (defined with string class names) are stored here.
# call resolve_pyfire_model_names() to resolve them.
_pending_relationships: list[Any] = []


def belongs_to(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str, attr_name: Optional[str] = None):
    def decorator(cls):
        if isinstance(model_class_or_name, str):
            _pending_relationships.append((cls, "belongs_to", model_class_or_name, db_field, attr_name))
        else:
            _apply_belongs_to(model_class_or_name, db_field)(cls)
        return cls
    return decorator


def has_one(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str, attr_name: Optional[str] = None):
    def decorator(cls):
        if isinstance(model_class_or_name, str):
            _pending_relationships.append((cls, "has_one", model_class_or_name, db_field, attr_name))
        else:
            _apply_has_one(model_class_or_name, db_field)(cls)
        return cls
    return decorator


def has_many(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str, attr_name: Optional[str] = None):
    def decorator(cls):
        if isinstance(model_class_or_name, str):
            _pending_relationships.append((cls, "has_many", model_class_or_name, db_field, attr_name))
        else:
            _apply_has_many(model_class_or_name, db_field, attr_name)(cls)
        return cls
    return decorator


def resolve_pyfire_model_names(global_context: dict[str, Any]):
    """
    Resolve all PyfireDoc subclasses in the global context.
    Call this function after all PyfireDoc subclasses are defined and before running the console.
    class_name in string format is resolved to the actual class.
    """
    global _pending_relationships
    for cls, relationship_type, model_name, db_field, attr in _pending_relationships:
        # if cls is a PyfireDoc. call model_rebuild() to ensure that the model is built.
        if issubclass(cls, PyfireDoc):
            cls.model_rebuild()

        if model_name in global_context:
            model_class = global_context[model_name]
            if relationship_type == "belongs_to":
                _apply_belongs_to(model_class, db_field, attr)(cls)
            elif relationship_type == "has_one":
                _apply_has_one(model_class, db_field, attr)(cls)
            elif relationship_type == "has_many":
                _apply_has_many(model_class, db_field, attr)(cls)
    _pending_relationships = []


def _apply_belongs_to(model_class: Type[PyfireDoc], db_field: str, attr: Optional[str] = None):
    def decorator(cls):
        def getter_method(self):
            model_id = getattr(self, db_field)
            if model_id:
                return model_class.find(model_id)
            else:
                return None

        attr_name = attr or model_class.__name__.lower()
        setattr(cls, attr_name, property(getter_method))
        return cls
    return decorator


def _apply_has_one(model_class: Type[PyfireDoc], db_field: str, attr: Optional[str] = None):
    def decorator(cls):
        def getter_method(self):
            model_instance = model_class.where(db_field, "==", self.id).first()
            return model_instance

        attr_name = attr or model_class.__name__.lower()
        setattr(cls, attr_name, property(getter_method))
        return cls
    return decorator


def _apply_has_many(model_class: Type[PyfireDoc], db_field: str, attr: Optional[str] = None):
    def decorator(cls):
        def getter_method(self):
            return model_class.where(db_field, "==", self.id)

        attr_name = attr or inflection.pluralize(model_class.__name__.lower())
        setattr(cls, attr_name, property(getter_method))
        return cls
    return decorator
