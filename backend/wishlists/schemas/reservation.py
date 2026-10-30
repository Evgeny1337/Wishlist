from ninja import Schema
from pydantic import Field, PositiveInt


class WishReservationResponse(Schema):
    wish: PositiveInt = Field(description="id Желания")
    is_reserved: bool = Field(description="Статус резервации")


class WishReserveDeleteResponse(Schema):
    wish: PositiveInt = Field(description="id Удаленного желания")
