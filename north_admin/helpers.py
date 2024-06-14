import json
from datetime import datetime as dt
from json import JSONDecodeError
from typing import Any, Callable, Type

from fastapi import HTTPException, Query
from pydantic import BaseModel
from random_unicode_emoji import random_emoji


def set_origin_to_pydantic_schema(schema: Type[BaseModel], function: Callable) -> Callable:
    function.__annotations__["origin"] = schema
    return function


def generate_random_emoji() -> str:
    return str(random_emoji(count=1)[0][0])


def filters_dict(filters: str = Query(...)) -> dict[str, Any]:
    try:
        return json.loads(filters)
    except JSONDecodeError as error:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid json in filters params: {error}",
        ) from error


def dt_to_int(datetime: dt) -> int:
    return int(datetime.timestamp())
