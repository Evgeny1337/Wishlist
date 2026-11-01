from typing import Literal, Optional

from django.db.models import Q
from ninja import FilterConfigDict, FilterSchema, ModelSchema, Schema
from pydantic import Field, HttpUrl, PositiveInt

from wishlists.models import Wish
from .profiles import ProfileResponse


class WishCreateRequest(Schema):
    title: str = Field(description="Заголовок", min_length=1)
    url: HttpUrl | None = Field(description="Ссылка", default=None)
    note: str = Field(description="Описание", default="")
    priority: Literal[1, 2, 3] = Field(
        description="Градация важности",
        default=Wish.WishPriority.LOW,
    )


class WishUpdateRequest(Schema):
    title: str | None = Field(description="Заголовок", default=None, min_length=1)
    url: HttpUrl | None = Field(description="Ссылка", default=None)
    note: str | None = Field(description="Описание", default=None)
    priority: Literal[1, 2, 3] | None = Field(
        description="Градация важности",
        default=None,
    )


class WishResponse(ModelSchema):
    wishlist_id: int = Field(description="ID Вишлиста")
    is_reserved: bool | None = Field(description="Статус резервирования", default=None)
    reserved_by_me: bool | None = Field(description="Забронировано мной", default=None)
    reserved_by_user: ProfileResponse | None = Field(description="Кем забронировано", default=None)

    @staticmethod
    def resolve_reserved_by_user(obj):
        if obj.wishlist.is_anonymous:
            return None
        reservation = obj.reservation.all().first()
        return reservation.profile if reservation else None

    @staticmethod
    def resolve_is_reserved(obj):
        return obj.reservation.all().first() is not None

    @staticmethod
    def resolve_reserved_by_me(obj, context):
        reservation = obj.reservation.all().first()
        if reservation is None:
            return False
        return reservation.profile_id == context["request"].auth.pk

    class Meta:
        model = Wish
        fields = [
            "id",
            "title",
            "url",
            "note",
            "created_at",
            "priority",
            "preview_title",
            "preview_image_url",
        ]


class WishPath(Schema):
    wishlist_id: PositiveInt = Field(description="ID Вишлиста")
    wish_id: PositiveInt = Field(description="ID Желания")


class WishListQueryParams(FilterSchema):
    priority: int | None = Field(
        ge=Wish.WishPriority.LOW,
        le=Wish.WishPriority.HIGH,
        default=None,
    )
    is_reserved: Optional[bool] = None

    def filter_is_reserved(self, value: bool):
        return Q(reservation__isnull=not value)

    model_config = FilterConfigDict(expression_connector="AND")
