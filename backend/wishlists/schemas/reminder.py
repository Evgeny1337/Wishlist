from datetime import datetime
from typing import Optional

from ninja import ModelSchema, Schema
from pydantic import Field, PositiveInt

from wishlists.models import Reminder


class ReminderCreateRequest(Schema):
    title: Optional[str] = Field(description="Описание", default=None)
    remind_at: datetime = Field(description="Дата напоминания")
    event_id: PositiveInt | None = Field(
        description="Id события (опционально)",
        default=None,
    )


class ReminderUpdateRequest(Schema):
    title: Optional[str] = Field(description="Описание", default=None)
    remind_at: Optional[datetime] = Field(description="Дата напоминания", default=None)
    event_id: PositiveInt | None = Field(
        description="Id события (опционально)",
        default=None,
    )


class ReminderResponse(ModelSchema):
    class Meta:
        model = Reminder
        fields = ["id", "title", "remind_at", "event", "created_at", "is_sent"]
