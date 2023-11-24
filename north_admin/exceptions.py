from fastapi import HTTPException
from north_admin.types import ModelType


class NorthAdminException(Exception):
    error_text: str = 'Common exception'

    def __str__(self) -> str:
        return f'NorthAdmin: {self.error_text}'


class NoDefinedPKException(NorthAdminException):
    def __init__(self, model_id: str):
        self.error_text = (
            f'Can`t determinate pkey field for {model_id} model.'
            'Try to set it manually.'
        )


class NoSoftDeleteField(NorthAdminException):
    def __init__(self, model_id: str):
        self.error_text = f'To make soft delete for {model_id} model awailable set soft_delete_column params'


class NothingToUpdate(NorthAdminException):
    def __init__(self, item_id: int | str, model_id: str):
        self.error_text = f'Nothing to update at {item_id} item of {model_id} model'


class PKeyMustBeInList(NorthAdminException):
    def __init__(self, model_id: str):
        self.error_text = f'PKey field must be in list endpoint of {model_id}'


class ItemNotFoundException(HTTPException):
    def __init__(
        self,
        model: ModelType,
        item_id: str | int,
    ):
        super().__init__(
            status_code=404,
            detail=f'Can`t find {model.__table__} with id {item_id} - it`s not exists or unavailable.',
        )


class DatabaseInternalException(HTTPException):
    model: ModelType
    exception: Exception

    def __init__(
        self,
        model: ModelType,
        exception: Exception,
    ):
        super().__init__(
            status_code=500,
            detail=f'Internal DB error during proccessing {model.__table__} object - {str(exception)}',
        )
