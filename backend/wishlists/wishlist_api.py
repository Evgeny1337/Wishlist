from http import HTTPStatus
from typing import List

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from pydantic import PositiveInt
from django.http import HttpRequest
from ninja import Router, Status, Path

from invites.auth import TelegramJWTAuth
from .models import WishList, Wish, WishReservation
from .schemas import (
    WishListResponseSchema,
    DetailSchema,
    ValidationErrorSchema,
    WishListCreateRequest,
    DeletedResponse,
    WishCreateRequest,
    WishResponse,
    PathWish, WishUpdateRequest, WishReservationResponse, WishDeleteReserveResponse,
)

wishlists_router = Router(auth=TelegramJWTAuth())


_UNPROCESSABLE = DetailSchema | ValidationErrorSchema


@wishlists_router.post(
    "/",
    response={
        HTTPStatus.CREATED: WishListResponseSchema,
        HTTPStatus.BAD_REQUEST: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
        HTTPStatus.NOT_FOUND: DetailSchema,
    },
)
def create_wishlist(request: HttpRequest, data: WishListCreateRequest):
    profile = request.auth
    wishlist = WishList.objects.create(
        owner=profile,
        title=data.title,
    )
    return Status(HTTPStatus.CREATED, wishlist)


@wishlists_router.get(
    "/",
    response={
        HTTPStatus.OK: List[WishListResponseSchema],
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
        HTTPStatus.NOT_FOUND: DetailSchema,
    },
)
def get_wishlists(request: HttpRequest):
    profile = request.auth
    wishlists = WishList.objects.filter(owner=profile)
    return Status(HTTPStatus.OK, wishlists)


@wishlists_router.get(
    "/{wishlist_id}/",
    response={
        HTTPStatus.OK: WishListResponseSchema,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def get_wishlist(
    request: HttpRequest,
    wishlist_id: PositiveInt,
):
    profile = request.auth
    wishlist = get_object_or_404(WishList, owner=profile, id=wishlist_id)
    return Status(HTTPStatus.OK, wishlist)


@wishlists_router.delete(
    "/{wishlist_id}/",
    response={
        HTTPStatus.OK: DeletedResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.CONFLICT: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def delete_wishlist(
    request: HttpRequest,
    wishlist_id: PositiveInt,
):
    profile = request.auth
    wishlist = WishList.objects.filter(owner=profile, id=wishlist_id).first()
    if wishlist is None:
        raise HttpError(HTTPStatus.NOT_FOUND, "Такого вишлиста нету")
    try:
        deleted_count, details = wishlist.delete()
    except ProtectedError:
        raise HttpError(
            HTTPStatus.CONFLICT,
            "Нельзя удалить вишлист, пока к нему привязаны события",
        )
    return DeletedResponse(details=details, deleted_count=deleted_count)


@wishlists_router.post(
    "/{wishlist_id}/wishes/",
    response={
        HTTPStatus.CREATED: WishResponse,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
        HTTPStatus.NOT_FOUND: DetailSchema,
    },
)
def create_wish(request: HttpRequest, wishlist_id: PositiveInt, data: WishCreateRequest):
    profile = request.auth
    wishlist = get_object_or_404(WishList, owner=profile, id=wishlist_id)
    wish = Wish.objects.create(
        wishlist=wishlist,
        title=data.title,
        note=data.note,
        url=str(data.url) if data.url else "",
        priority=data.priority,
    )
    return Status(HTTPStatus.CREATED, wish)


@wishlists_router.get(
    "/{wishlist_id}/wishes/{wish_id}/",
    response={
        HTTPStatus.OK: WishResponse,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
        HTTPStatus.NOT_FOUND: DetailSchema,
    }
)
def get_wish(
        request: HttpRequest,
        path: Path[PathWish],
):
    profile = request.auth
    wishlist = get_object_or_404(WishList, owner=profile, id=path.wishlist_id)
    wish = get_object_or_404(Wish.objects.prefetch_related('reservation'), wishlist=wishlist, id=path.wish_id)
    return Status(HTTPStatus.OK, wish)


@wishlists_router.get(
    "/{wishlist_id}/wishes/",
    response={
        HTTPStatus.OK: List[WishResponse],
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
        HTTPStatus.NOT_FOUND: DetailSchema,
    },
)
def get_wishes(
    request: HttpRequest,
    wishlist_id: PositiveInt,
):
    profile = request.auth
    wishlist = get_object_or_404(WishList, owner=profile, id=wishlist_id)
    wishes = list(Wish.objects.prefetch_related('reservation').filter(wishlist=wishlist).order_by("-priority", "-created_at"))
    return Status(HTTPStatus.OK, wishes)


@wishlists_router.delete(
    "/{wishlist_id}/wishes/{wish_id}/",
    response={
        HTTPStatus.OK: DeletedResponse,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
        HTTPStatus.NOT_FOUND: DetailSchema,
    },
)
def delete_wish(
        request: HttpRequest,
        path: Path[PathWish],
):
    profile = request.auth
    wishlist = get_object_or_404(WishList, owner=profile, id=path.wishlist_id)
    deleted_count, details = Wish.objects.filter(wishlist=wishlist, id=path.wish_id).delete()
    if deleted_count == 0:
        raise HttpError(HTTPStatus.NOT_FOUND, "Нет такого wish")
    return DeletedResponse(details=details, deleted_count=deleted_count)


@wishlists_router.patch(
    "/{wishlist_id}/wishes/{wish_id}/",
    response={
        HTTPStatus.OK: WishResponse,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
        HTTPStatus.NOT_FOUND: DetailSchema,
    }
)
def update_wish(
        request: HttpRequest,
        path: Path[PathWish],
        body: WishUpdateRequest,
):
    profile = request.auth
    wishlist = get_object_or_404(WishList, owner=profile, id=path.wishlist_id)
    wish = get_object_or_404(Wish.objects.prefetch_related('reservation'), id=path.wish_id, wishlist=wishlist)
    with transaction.atomic():
        updates = body.model_dump(exclude_unset=True)
        if "url" in updates:
            updates["url"] = str(updates["url"]) if updates["url"] else ""
        if updates:
            wish.reservation.all().delete()
            for attr, value in updates.items():
                setattr(wish, attr, value)
            wish.save(update_fields=list(updates))
    return Status(HTTPStatus.OK, wish)


@wishlists_router.post(
    "/{wishlist_id}/wishes/{wish_id}/reserve/",
    response={
        HTTPStatus.CREATED: WishReservationResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.CONFLICT: DetailSchema,
    }
)
def reserve_wish(
        request: HttpRequest,
        path: Path[PathWish],
):
    profile = request.auth
    wish = get_object_or_404(Wish, pk=path.wish_id, wishlist_id=path.wishlist_id)
    try:
        WishReservation.objects.create(
            wish=wish,
            profile=profile,
        )
    except IntegrityError as exc:
        raise HttpError(
            HTTPStatus.CONFLICT,
            "Желание уже забронировано",
        ) from exc
    return Status(HTTPStatus.CREATED, WishReservationResponse(
        wish=wish.id,
        is_reserved=True,
    ))


@wishlists_router.get(
    "/{wishlist_id}/wishes/{wish_id}/reserve/",
    response={
        HTTPStatus.OK: WishReservationResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
    }
)
def get_reserve_wish(
        request: HttpRequest,
        path: Path[PathWish],
):
    profile = request.auth
    wish = get_object_or_404(Wish, pk=path.wish_id, wishlist_id=path.wishlist_id)
    try:
        WishReservation.objects.get(wish=wish, profile=profile)
    except WishReservation.DoesNotExist:
        return Status(HTTPStatus.OK, WishReservationResponse(
            wish=wish.id,
            is_reserved=False,
        ))
    return Status(HTTPStatus.OK, WishReservationResponse(
        wish=wish.id,
        is_reserved=True
    ))


@wishlists_router.delete(
    "/{wishlist_id}/wishes/{wish_id}/reserve/",
    response={
        HTTPStatus.OK: WishDeleteReserveResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
    }
)
def delete_reserve_wish(
        request: HttpRequest,
        path: Path[PathWish],
):
    profile = request.auth
    wish = get_object_or_404(Wish, pk=path.wish_id, wishlist_id=path.wishlist_id)
    wish_reservation = get_object_or_404(WishReservation, wish=wish, profile=profile)
    wish_reservation.delete()
    return Status(HTTPStatus.OK, WishDeleteReserveResponse(
        wish=wish.id))
