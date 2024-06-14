from typing import Type

from fastapi import HTTPException
from north_admin.types import ModelType


class NorthAdminError(Exception):
    error_text: str = "Common exception"

    def __str__(self) -> str:
        return f"NorthAdmin: {self.error_text}"


class NoDefinedPKError(NorthAdminError):
    def __init__(self, model_id: str) -> None:
        self.error_text = (
            f"Can`t determinate pkey field for {model_id} model."
            "Try to set it manually."
        )


class NoSoftDeleteFieldError(NorthAdminError):
    def __init__(self, model_id: str) -> None:
        self.error_text = f"To make soft delete for {model_id} model awailable set soft_delete_column params"


class NothingToUpdateError(NorthAdminError):
    def __init__(self, item_id: int | str, model_id: str) -> None:
        self.error_text = f"Nothing to update at {item_id} item of {model_id} model"


class PKeyMustBeInListError(NorthAdminError):
    def __init__(self, model_id: str) -> None:
        self.error_text = f"PKey field must be in list endpoint of {model_id}"


class ItemNotFoundExceptionError(HTTPException):
    def __init__(
        self,
        model: ModelType,
        item_id: str | int,
    ) -> None:
        super().__init__(
            status_code=404,
            detail=f"Can`t find {model.__table__} with id {item_id} - it`s not exists or unavailable.",
        )


class CantConvertTypeError(HTTPException):
    def __init__(
        self,
        model: ModelType,
        origin_type: Type,
        target_type: Type,
    ) -> None:
        super().__init__(
            status_code=422,
            detail=f"Can`t convert PKey field in {model.__table__} model from {origin_type} to {target_type}",
        )


class DatabaseInternalError(HTTPException):
    model: ModelType
    exception: Exception

    def __init__(
        self,
        model: ModelType,
        exception: Exception,
    ) -> None:
        super().__init__(
            status_code=500,
            detail=f"Internal DB error during proccessing {model.__table__} object - {exception!s}",
        )
