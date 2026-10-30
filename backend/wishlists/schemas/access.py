from ninja import ModelSchema, Schema
from pydantic import Field, PositiveInt

from wishlists.models import WishListAccess


class WishListAccessRequest(Schema):
    profile: PositiveInt = Field(description="Id профиля")


class WishListAccessResponse(ModelSchema):
    class Meta:
        model = WishListAccess
        fields = ["id", "wishlist", "profile"]


class WishListAccessDeleteResponse(Schema):
    wishlist: PositiveInt = Field(description="Id удаленного вишлиста")
    profile: PositiveInt = Field(description="Id удаленного профиля")
