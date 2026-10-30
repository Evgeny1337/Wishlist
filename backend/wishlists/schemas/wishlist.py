from ninja import ModelSchema, Schema
from pydantic import Field

from wishlists.models import WishList
from wishlists.schemas.event import EventResponse


class WishListCreateRequest(Schema):
    title: str = Field(description="Заголовок", min_length=1)


class WishListResponse(ModelSchema):
    events: list[EventResponse] = []

    class Meta:
        model = WishList
        fields = ["id", "owner", "title", "created_at"]
