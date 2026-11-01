from ninja import ModelSchema, Schema
from pydantic import Field

from wishlists.models import WishList
from wishlists.schemas.event import EventResponse


class WishListCreateRequest(Schema):
    title: str = Field(description="Заголовок", min_length=1)
    is_anonymous: bool | None = Field(description="Не показывать бронь", default=None)


class WishListUpdateRequest(Schema):
    title: str | None = Field(description="Заголовок", default=None, min_length=1)
    is_anonymous: bool | None = Field(description="Не показывать бронь", default=None)

class WishListResponse(ModelSchema):
    events: list[EventResponse] = []
    is_owner: bool = Field(description="Мой вишлист")

    @staticmethod
    def resolve_is_owner(obj, context):
        return obj.owner_id == context["request"].auth.pk

    class Meta:
        model = WishList
        fields = ["id", "owner", "title", "created_at", "is_anonymous"]
