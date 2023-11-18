from typing import Coroutine,  Callable

from pydantic import BaseModel


def set_origin_to_pydantic_schema(schema: BaseModel, function: Callable) -> Callable:
    function.__annotations__['origin'] = schema
    return function