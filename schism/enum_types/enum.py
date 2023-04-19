from typing import Any, Type


def _create_sub_type(base_type: Type, enum_type: Type) -> Type:
    return type(base_type.__name__, (base_type, enum_type), {})


class Enum:
    def __init_subclass__(cls, **_):
        for name, value in vars(cls).items():
            match value:
                case type():
                    setattr(cls, name, _create_sub_type(value, cls))