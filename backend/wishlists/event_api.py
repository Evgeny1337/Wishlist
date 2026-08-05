from http import HTTPStatus
from typing import List

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router, Status
from pydantic import PositiveInt

from invites.auth import TelegramJWTAuth
from wishlists.models import WishList, Event
from wishlists.schemas import (
    DetailSchema,
    EventDeleteResponse,
    EventRequest,
    EventResponse,
    EventUpdateRequest,
    ValidationErrorSchema,
)

events_router = Router(auth=TelegramJWTAuth())

_UNPROCESSABLE = DetailSchema | ValidationErrorSchema


@events_router.post(
    "/",
    response={
        HTTPStatus.CREATED: EventResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def create_event(request: HttpRequest, payload: EventRequest):
    owner = request.auth
    wishlist = get_object_or_404(WishList, pk=payload.wishlist, owner=owner)
    event = Event.objects.create(
        title=payload.title,
        owner=owner,
        wishlist=wishlist,
        starts_at=payload.starts_at,
    )
    return Status(HTTPStatus.CREATED, event)


@events_router.get(
    "/",
    response={
        HTTPStatus.OK: List[EventResponse],
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def list_events(request: HttpRequest):
    owner = request.auth
    events = Event.objects.filter(owner=owner).order_by("starts_at")
    return Status(HTTPStatus.OK, list(events))


@events_router.get(
    "/{event_id}/",
    response={
        HTTPStatus.OK: EventResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def get_event(request: HttpRequest, event_id: PositiveInt):
    owner = request.auth
    event = get_object_or_404(Event, pk=event_id, owner=owner)
    return Status(HTTPStatus.OK, event)


@events_router.patch(
    "/{event_id}/",
    response={
        HTTPStatus.OK: EventResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def update_event(request: HttpRequest, event_id: PositiveInt, payload: EventUpdateRequest):
    owner = request.auth
    event = get_object_or_404(Event, pk=event_id, owner=owner)
    updates = payload.model_dump(exclude_unset=True)
    if "wishlist" in updates:
        updates["wishlist"] = get_object_or_404(
            WishList,
            pk=updates["wishlist"],
            owner=owner,
        )
    if updates:
        for attr, value in updates.items():
            setattr(event, attr, value)
        event.save(update_fields=list(updates))
    return Status(HTTPStatus.OK, event)


@events_router.delete(
    "/{event_id}/",
    response={
        HTTPStatus.OK: EventDeleteResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def delete_event(request: HttpRequest, event_id: PositiveInt):
    owner = request.auth
    event = get_object_or_404(Event, pk=event_id, owner=owner)
    deleted_count, details = event.delete()
    return Status(
        HTTPStatus.OK,
        EventDeleteResponse(deleted_count=deleted_count, details=details),
    )
