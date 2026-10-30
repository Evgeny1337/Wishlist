"""Pydantic / Ninja DTO for wishlists app (split by domain)."""

from wishlists.schemas.access import (
    WishListAccessDeleteResponse,
    WishListAccessRequest,
    WishListAccessResponse,
)
from wishlists.schemas.common import DeletedResponse, DetailSchema, ValidationErrorSchema
from wishlists.schemas.event import (
    EventAccessRequest,
    EventAccessResponse,
    EventCreateRequest,
    EventResponse,
    EventUpdateRequest,
)
from wishlists.schemas.reminder import (
    ReminderCreateRequest,
    ReminderResponse,
    ReminderUpdateRequest,
)
from wishlists.schemas.reservation import WishReservationResponse, WishReserveDeleteResponse
from wishlists.schemas.wish import (
    WishCreateRequest,
    WishListQueryParams,
    WishPath,
    WishResponse,
    WishUpdateRequest,
)
from wishlists.schemas.wishlist import WishListCreateRequest, WishListResponse

__all__ = [
    "DeletedResponse",
    "DetailSchema",
    "EventAccessRequest",
    "EventAccessResponse",
    "EventCreateRequest",
    "EventResponse",
    "EventUpdateRequest",
    "ReminderCreateRequest",
    "ReminderResponse",
    "ReminderUpdateRequest",
    "ValidationErrorSchema",
    "WishCreateRequest",
    "WishListAccessDeleteResponse",
    "WishListAccessRequest",
    "WishListAccessResponse",
    "WishListCreateRequest",
    "WishListQueryParams",
    "WishListResponse",
    "WishPath",
    "WishReservationResponse",
    "WishReserveDeleteResponse",
    "WishResponse",
    "WishUpdateRequest",
]
