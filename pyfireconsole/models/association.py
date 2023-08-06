from typing import Any, Type, Union

import inflect

from pyfireconsole.models.pyfire_model import PyfireDoc


_pending_relationships: list[Any] = []


def belongs_to(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str):
    def decorator(cls):
        if isinstance(model_class_or_name, str):
            _pending_relationships.append((cls, "belongs_to", model_class_or_name, db_field))
        else:
            _apply_belongs_to(model_class_or_name, db_field)(cls)
        return cls
    return decorator


def has_one(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str):
    def decorator(cls):
        if isinstance(model_class_or_name, str):
            _pending_relationships.append((cls, "has_one", model_class_or_name, db_field))
        else:
            _apply_has_one(model_class_or_name, db_field)(cls)
        return cls
    return decorator


def has_many(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str):
    def decorator(cls):
        if isinstance(model_class_or_name, str):
            _pending_relationships.append((cls, "has_many", model_class_or_name, db_field))
        else:
            _apply_has_many(model_class_or_name, db_field)(cls)
        return cls
    return decorator


def resolve_pyfire_model_names(global_context: dict[str, Any]):
    global _pending_relationships
    for cls, relationship_type, model_name, db_field in _pending_relationships:
        model_class = global_context[model_name]
        if relationship_type == "belongs_to":
            _apply_belongs_to(model_class, db_field)(cls)
        elif relationship_type == "has_one":
            _apply_has_one(model_class, db_field)(cls)
        elif relationship_type == "has_many":
            _apply_has_many(model_class, db_field)(cls)
    _pending_relationships = []


def _resolve_model_class(model_class_or_name: Union[str, Type[PyfireDoc]]) -> Type[PyfireDoc]:
    if isinstance(model_class_or_name, str):
        # Get the actual model class from its name
        return globals().get(model_class_or_name)
    return model_class_or_name


def _apply_belongs_to(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str):
    def decorator(cls):
        model_class = _resolve_model_class(model_class_or_name)

        def getter_method(self):
            model_id = getattr(self, db_field)
            if model_id:
                return model_class.find(model_id)
            else:
                return None

        attr_name = model_class.__name__.lower()
        setattr(cls, attr_name, property(getter_method))
        return cls
    return decorator


def _apply_has_one(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str):
    def decorator(cls):
        model_class = _resolve_model_class(model_class_or_name)

        def getter_method(self):
            model_instance = model_class.where(db_field, "==", self.id).first()
            return model_instance

        attr_name = model_class.__name__.lower()
        setattr(cls, attr_name, property(getter_method))
        return cls
    return decorator


def _apply_has_many(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str):
    def decorator(cls):
        model_class = _resolve_model_class(model_class_or_name)

        def getter_method(self):
            return model_class.where(db_field, "==", self.id)

        attr_name = f"{model_class.__name__.lower()}s"
        setattr(cls, attr_name, property(getter_method))
        return cls
    return decorator


# def _apply_has_many(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str):
#     def decorator(cls):
#         def getter_method(self):
#             if isinstance(model_class_or_name, str):
#                 # Get the actual model class from its name
#                 breakpoint()
#                 model_class = globals()[model_class_or_name]
#             else:
#                 model_class = model_class_or_name

#             # Assuming `where` is a class method of `model_class` that filters by the given conditions
#             return model_class.where(db_field, "==", self.id)

#         if isinstance(model_class_or_name, str):
#             attr_name = inflect.engine().plural(model_class_or_name).lower()
#         else:
#             attr_name = inflect.engine().plural(model_class_or_name.__name__).lower()

#         setattr(cls, attr_name, property(getter_method))
#         return cls
#     return decorator


# def _apply_has_one(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str):
#     def decorator(cls):
#         def getter_method(self):
#             if isinstance(model_class_or_name, str):
#                 # Get the actual model class from its name
#                 model_class = globals()[model_class_or_name]
#             else:
#                 model_class = model_class_or_name

#             # Here, we assume that the `first` method of `model_class.where` returns the first result that matches the conditions.
#             return model_class.where(db_field, "==", self.id).first()

#         if isinstance(model_class_or_name, str):
#             attr_name = model_class_or_name.lower()
#         else:
#             attr_name = model_class_or_name.__name__.lower()

#         setattr(cls, attr_name, property(getter_method))
#         return cls
#     return decorator


# def _apply_belongs_to(model_class_or_name: Union[str, Type[PyfireDoc]], db_field: str):
#     def decorator(cls):
#         def getter_method(self):
#             if isinstance(model_class_or_name, str):
#                 # Get the actual model class from its name
#                 model_class = globals()[model_class_or_name]
#             else:
#                 model_class = model_class_or_name

#             model_id = getattr(self, db_field)
#             if model_id:
#                 return model_class.find(model_id)
#             else:
#                 return None

#         if isinstance(model_class_or_name, str):
#             attr_name = model_class_or_name.lower()
#         else:
#             attr_name = model_class_or_name.__name__.lower()

#         setattr(cls, attr_name, property(getter_method))
#         return cls
#     return decorator
