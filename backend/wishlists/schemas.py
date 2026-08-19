from typing import Any, Literal, Optional
from datetime import datetime

from django.db.models import Q
from ninja import Schema, ModelSchema, FilterSchema, FilterConfigDict
from pydantic import Field, PositiveInt, HttpUrl, model_validator

from wishlists.models import WishList, Wish, Event, WishListAccess, EventAccess, GiftPlan, GiftPlanItem


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
        fields = ["id", "title", "url", "note", "created_at", "priority", 'preview_title', 'preview_image_url']


class PathWish(Schema):
    wishlist_id: PositiveInt = Field(description="ID Вишлиста")
    wish_id: PositiveInt = Field(description="ID Желания")


class WishUpdateRequest(Schema):
    title: str | None = Field(description="Заголовок", default=None, min_length=1)
    url: HttpUrl | None = Field(description="Ссылка", default=None)
    note: str | None = Field(description="Описание", default=None)
    priority: Literal[1, 2, 3] | None = Field(description="Градация важности", default=None)


class WishReservationResponse(Schema):
    wish: PositiveInt = Field(description="id Желания")
    is_reserved: bool = Field(description="Статус резервации")


class WishDeleteReserveResponse(Schema):
    wish: PositiveInt = Field(description="id Удаленного желания")


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
    wishlist_id: PositiveInt = Field(description="ID Вишлиста")

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
    profile: PositiveInt = Field(description="Id профиля")


class WishListAccessDeleteResponse(Schema):
    wishlist: PositiveInt = Field(description="Id удаленного вишлиста")
    profile: PositiveInt = Field(description="Id удаленного профиля")


class EventAccessRequest(Schema):
    profile: PositiveInt = Field(description="Id профиля")


class EventAccessResponse(ModelSchema):
    class Meta:
        model = EventAccess
        fields = '__all__'


class GiftPlanRequest(Schema):
    title: str = Field(description="Заголовок")
    occurs_at: datetime = Field(description="Дата события")


class GiftPlanResponse(ModelSchema):
    class Meta:
        model = GiftPlan
        fields = ['id', 'title', 'occurs_at', 'created_at']


class GiftPlanUpdateRequest(Schema):
    title: Optional[str] = None
    occurs_at: Optional[datetime] = None


class GiftPlanDeleteResponse(Schema):
    plan_id: PositiveInt = Field(description="Id Удаленного события")


class GiftPlanItemRequest(Schema):
    title: str | None = Field(description="Заголовок подарка к событию", default=None)
    url: HttpUrl | None = Field(description="Ссылка на подарок", default=None)
    wish: PositiveInt | None = Field(description="Id желания", default=None)

    @model_validator(mode="after")
    def wish_or_manual(self):
        if self.wish is None and not self.title:
            raise ValueError("Нужен wish либо title")
        return self


class GiftPlanItemResponse(ModelSchema):
    url: str = Field(description="Ссылка на сайт")
    class Meta:
        model = GiftPlanItem
        fields = ['id', 'title', 'url', 'created_at', 'wish']



class GiftPlanItemPatchDeletePath(Schema):
    plan_id: PositiveInt = Field(description="Id события")
    item_id: PositiveInt = Field(description="Id подарка к событию")


class GiftPlanItemDeleteResponse(Schema):
    item_id: PositiveInt = Field(description="Id удаленного подарка")








