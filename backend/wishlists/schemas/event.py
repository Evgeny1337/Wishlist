from datetime import datetime, timezone

from ninja import ModelSchema, Schema
from pydantic import Field, PositiveInt

from wishlists.models import Event, EventAccess


class EventResponse(ModelSchema):
    wishlist_id: PositiveInt = Field(description="ID Вишлиста")
    is_expired: bool = Field(description="Просроченое событие")
    days_left: int | None = Field(description="Осталось дней")

    class Meta:
        model = Event
        fields = ["id", "title", "created_at", "starts_at"]

    @staticmethod
    def resolve_is_expired(obj):
        date_now = datetime.now(timezone.utc).date()
        event_date = obj.starts_at.date()
        return date_now > event_date

    @staticmethod
    def resolve_days_left(obj):
        today = datetime.now(timezone.utc).date()
        event_day = obj.starts_at.date()
        diff = (event_day - today).days
        return diff if diff >= 0 else None


class EventCreateRequest(Schema):
    title: str = Field(description="Наименование", min_length=1)
    wishlist: PositiveInt = Field(description="ID Вишлиста")
    starts_at: datetime = Field(description="Дата события")


class EventUpdateRequest(Schema):
    title: str | None = Field(description="Наименование", min_length=1, default=None)
    wishlist: PositiveInt | None = Field(description="ID Вишлиста", default=None)
    starts_at: datetime | None = Field(description="Дата события", default=None)


class EventAccessRequest(Schema):
    profile: PositiveInt = Field(description="Id профиля")


class EventAccessResponse(ModelSchema):
    class Meta:
        model = EventAccess
        fields = "__all__"
