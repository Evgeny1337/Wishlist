from typing import Any

from ninja import Schema, ModelSchema
from pydantic import Field, PositiveInt, HttpUrl

from wishlists.models import WishList, Wish


class DetailSchema(Schema):
    detail: str = Field(description="Сообщение об ошибке")


class ValidationErrorSchema(Schema):
    detail: list[Any] = Field(description="Список ошибок валидации")


class DeletedResponse(Schema):
    deleted_count: PositiveInt = Field(description="Количество удаленных")
    details: dict[str, int] = Field(description="Количество удаленных объектов")


class WishListCreateRequest(Schema):
    title: str = Field(description="Заголовок", min_length=1)


class WishListResponseSchema(ModelSchema):
    class Meta:
        model = WishList
        fields = ["id", "owner", "title", "created_at"]


class WishCreateRequest(Schema):
    title: str = Field(description="Заголовок", min_length=1)
    url: HttpUrl | None = Field(description="Ссылка", default=None)
    note: str = Field(description="Описание", default="")


class WishResponse(ModelSchema):
    wishlist_id: int = Field(description="ID Вишлиста")

    class Meta:
        model = Wish
        fields = ["id", "title", "url", "note", "created_at"]


class PathWish(Schema):
    wishlist_id: PositiveInt = Field(description="ID Вишлиста")
    wish_id: PositiveInt = Field(description="ID Желания")


class WishUpdateRequest(Schema):
    title: str | None = Field(description="Заголовок", default=None, min_length=1)
    url: HttpUrl | None = Field(description="Ссылка", default=None)
    note: str | None = Field(description="Описание", default=None)


class WishReservationResponse(Schema):
    wish: int = Field(description="id Желания")
    is_reserved: bool = Field(description="Статус резервации")


class WishDeleteReserveResponse(Schema):
    wish: int = Field(description="id Удаленного желания")

