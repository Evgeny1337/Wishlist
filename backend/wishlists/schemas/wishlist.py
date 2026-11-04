from ninja import ModelSchema, Schema
from pydantic import Field

from wishlists.models import WishList
from wishlists.schemas.event import EventResponse


class WishListCreateRequest(Schema):
    title: str = Field(description="Заголовок", min_length=1)
    is_anonymous: bool = Field(
        description="Скрывать, кто зарезервировал желание",
        default=False,
    )


class WishListUpdateRequest(Schema):
    title: str | None = Field(description="Заголовок", default=None, min_length=1)
    is_anonymous: bool | None = Field(
        description="Скрывать, кто зарезервировал желание",
        default=None,
    )


class WishListResponse(ModelSchema):
    events: list[EventResponse] = []
    is_owner: bool = Field(description="Статус владельца")

    class Meta:
        model = WishList
        fields = ["id", "owner", "title", "created_at", "is_anonymous"]

    @staticmethod
    def resolve_is_owner(obj, context):
        return obj.owner.pk == context['request'].auth.pk