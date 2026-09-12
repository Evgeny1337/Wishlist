from http import HTTPStatus
from typing import List

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router, Status
from ninja.errors import HttpError
from pydantic import PositiveInt

from invites.auth import TelegramJWTAuth
from wishlists.models import Event, Reminder
from wishlists.schemas import (
    DetailSchema,
    ReminderRequest,
    ReminderResponse,
    ReminderUpdateRequest,
    ValidationErrorSchema,
)

reminder_router = Router(auth=TelegramJWTAuth())

_UNPROCESSABLE = DetailSchema | ValidationErrorSchema


def _owned_event_or_404(event_id: int, owner) -> Event:
    return get_object_or_404(Event, pk=event_id, owner=owner)


@reminder_router.post(
    "/",
    response={
        HTTPStatus.CREATED: ReminderResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def create_reminder(request: HttpRequest, payload: ReminderRequest):
    owner = request.auth
    event = None
    if payload.event_id is not None:
        event = _owned_event_or_404(payload.event_id, owner)
    reminder = Reminder.objects.create(
        owner=owner,
        event=event,
        title=payload.title,
        remind_at=payload.remind_at,
    )
    return Status(HTTPStatus.CREATED, reminder)


@reminder_router.get(
    "/",
    response={
        HTTPStatus.OK: List[ReminderResponse],
    },
)
def list_reminders(request: HttpRequest):
    reminders = Reminder.objects.filter(owner=request.auth).order_by("remind_at")
    return Status(HTTPStatus.OK, list(reminders))


@reminder_router.get(
    "/{int:pk}/",
    response={
        HTTPStatus.OK: ReminderResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def get_reminder(request: HttpRequest, pk: PositiveInt):
    reminder = get_object_or_404(Reminder, pk=pk, owner=request.auth)
    return Status(HTTPStatus.OK, reminder)


@reminder_router.patch(
    "/{int:pk}/",
    response={
        HTTPStatus.OK: ReminderResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def update_reminder(request: HttpRequest, pk: PositiveInt, payload: ReminderUpdateRequest):
    owner = request.auth
    reminder = get_object_or_404(Reminder, pk=pk, owner=owner)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HttpError(HTTPStatus.UNPROCESSABLE_ENTITY, "Пустое тело запроса")
    if "event_id" in updates:
        event_id = updates.pop("event_id")
        updates["event"] = (
            None if event_id is None else _owned_event_or_404(event_id, owner)
        )
    for attr, value in updates.items():
        setattr(reminder, attr, value)
    reminder.save(update_fields=list(updates))
    return Status(HTTPStatus.OK, reminder)


@reminder_router.delete(
    "/{int:pk}/",
    response={
        HTTPStatus.OK: ReminderResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def delete_reminder(request: HttpRequest, pk: PositiveInt):
    reminder = get_object_or_404(Reminder, pk=pk, owner=request.auth)
    reminder.delete()
    return Status(HTTPStatus.OK, reminder)
