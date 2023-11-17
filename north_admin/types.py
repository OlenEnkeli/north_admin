from typing import Type
from enum import Enum

from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute

ModelType = Type[DeclarativeBase]


class AdminMethods(str, Enum):
    GET_LIST = 'get_list'
    GET_ONE = 'get_one'
    CREATE = 'create'
    UPDATE = 'update'
    SOFT_DELETE = 'soft_delete'
    DELETE = 'delete'


class FilterType(str, Enum):
    CHECKBOX = 'checkbox'
    GREATER_THEN = 'greater_then'
    LESS_THEN = 'less_then'


class FieldAPIType(str, Enum):
    INTEGER = 'integer'
    STRING = 'string'
    ENUM = 'enum'
    DATETIME = 'datetime'
    ARRAY = 'array'


def sqlalchemy_column_to_pydantic(column: InstrumentedAttribute) -> tuple[type, any]:
    """
    :param column: InstrumentedAttribute (SQLAlchemy column)
    :return: (python_type: type, default: any)
    """

    python_type: type | None = None
    default: any = None

    if hasattr(column.type, 'impl'):
        if hasattr(column.type.impl, 'python_type'):
            python_type = column.type.impl.python_type

    elif hasattr(column.type, 'python_type'):
        python_type = column.type.python_type

    if column.default is None and not column.nullable:
        default = ...

    return python_type, default
