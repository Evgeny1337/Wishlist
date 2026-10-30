from typing import Any

from ninja import Schema
from pydantic import Field, PositiveInt


class DetailSchema(Schema):
    detail: str = Field(description="Сообщение об ошибке")


class ValidationErrorSchema(Schema):
    detail: list[Any] = Field(description="Список ошибок валидации")


class DeletedResponse(Schema):
    deleted_count: PositiveInt = Field(description="Количество удаленных")
    details: dict[str, int] = Field(description="Количество удаленных объектов")
