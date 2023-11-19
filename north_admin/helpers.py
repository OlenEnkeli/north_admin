from typing import Callable

from pydantic import BaseModel
from random_unicode_emoji import random_emoji


def set_origin_to_pydantic_schema(schema: BaseModel, function: Callable) -> Callable:
    function.__annotations__['origin'] = schema
    return function


def generate_random_emoji():
    return str(random_emoji(count=1)[0][0])
