from typing import Any, Literal, Optional
from datetime import datetime

from django.db.models import Q
from ninja import Schema, ModelSchema, FilterSchema, FilterConfigDict
from pydantic import Field, PositiveInt, HttpUrl

from wishlists.models import WishList, Wish, Event, WishListAccess


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
    priority: Literal[1, 2, 3] = Field(description="Градация важности", default=Wish.WishPriority.LOW)


class WishResponse(ModelSchema):
    wishlist_id: int = Field(description="ID Вишлиста")
    is_reserved: bool = Field(description="Статус резервирования")
    reserved_by_me: bool = Field(description="Забронировано мной")

    @staticmethod
    def resolve_is_reserved(obj):
        reservation = list(obj.reservation.all())
        return len(reservation) > 0

    @staticmethod
    def resolve_reserved_by_me(obj, context):
        request = context["request"]
        reservation = list(obj.reservation.all())
        if len(reservation) > 0:
            reservation_profile = reservation[0].profile
            return reservation_profile.pk == request.auth.pk
        return False

    class Meta:
        model = Wish
        fields = ["id", "title", "url", "note", "created_at", "priority"]


class PathWish(Schema):
    wishlist_id: PositiveInt = Field(description="ID Вишлиста")
    wish_id: PositiveInt = Field(description="ID Желания")


class WishUpdateRequest(Schema):
    title: str | None = Field(description="Заголовок", default=None, min_length=1)
    url: HttpUrl | None = Field(description="Ссылка", default=None)
    note: str | None = Field(description="Описание", default=None)
    priority: Literal[1, 2, 3] | None = Field(description="Градация важности", default=None)


class WishReservationResponse(Schema):
    wish: int = Field(description="id Желания")
    is_reserved: bool = Field(description="Статус резервации")


class WishDeleteReserveResponse(Schema):
    wish: int = Field(description="id Удаленного желания")


class EventRequest(Schema):
    title: str = Field(description="Наименование", min_length=1)
    wishlist: PositiveInt = Field(description="ID Вишлиста")
    starts_at: datetime = Field(description="Дата события")


class EventUpdateRequest(Schema):
    title: str | None = Field(description="Наименование", min_length=1, default=None)
    wishlist: PositiveInt | None = Field(description="ID Вишлиста", default=None)
    starts_at: datetime | None = Field(description="Дата события", default=None)


class EventDeleteResponse(Schema):
    deleted_count: PositiveInt = Field(description="Количество удаленных")
    details: dict[str, int] = Field(description="Количество удаленных объектов")


class EventResponse(ModelSchema):
    wishlist_id: int = Field(description="ID Вишлиста")

    class Meta:
        model = Event
        fields = ["id", "title", "created_at", "starts_at"]


class WishListQueryParams(FilterSchema):
    priority: int | None = Field(ge=Wish.WishPriority.LOW, le=Wish.WishPriority.HIGH, default=None)
    is_reserved: Optional[bool] = None

    def filter_is_reserved(self, value: bool):
        return Q(reservation__isnull=not value)

    model_config = FilterConfigDict(expression_connector="AND")


class WishlistAccessResponse(ModelSchema):
    class Meta:
        model = WishListAccess
        fields = ["id", "wishlist", 'profile']


class WishListAccessRequest(Schema):
    profile: int = Field(description="Id профиля")


class WishListAccessDeleteResponse(Schema):
    wishlist: int = Field(description="Id удаленного вишлиста")
    profile: int = Field(description="Id удаленного профиля")


