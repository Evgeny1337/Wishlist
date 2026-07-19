from http import HTTPStatus
from typing import List

from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from pydantic import PositiveInt
from django.http import HttpRequest
from ninja import Router, Status, Path, Header

from .helpers import get_profile
from .models import WishList, Wish
from .schemas import (
    WishListResponseSchema,
    DetailSchema,
    ValidationErrorSchema,
    WishListCreateRequest,
    DeletedResponse,
    WishCreateRequest,
    WishCreateResponse,
    PathWish,
)

wishlists_router = Router()


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
    profile = get_profile(data.init_data)
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
def get_wishlists(request: HttpRequest, init_data: Header[str]):
    profile = get_profile(init_data)
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
    init_data: Header[str],
):
    profile = get_profile(init_data)
    wishlist = get_object_or_404(WishList, owner=profile, id=wishlist_id)
    return Status(HTTPStatus.OK, wishlist)


@wishlists_router.delete(
    "/{wishlist_id}/",
    response={
        HTTPStatus.OK: DeletedResponse,
        HTTPStatus.NOT_FOUND: DetailSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
    },
)
def delete_wishlist(
    request: HttpRequest,
    wishlist_id: PositiveInt,
    init_data: Header[str],
):
    profile = get_profile(init_data)
    deleted_count, details = WishList.objects.filter(owner=profile, id=wishlist_id).delete()
    if deleted_count == 0:
        raise HttpError(HTTPStatus.NOT_FOUND, "Такого вишлиста нету")
    return DeletedResponse(details=details, deleted_count=deleted_count)


@wishlists_router.post(
    "/{wishlist_id}/wishes/",
    response={
        HTTPStatus.CREATED: WishCreateResponse,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
        HTTPStatus.NOT_FOUND: DetailSchema,
    },
)
def create_wish(request: HttpRequest, wishlist_id: PositiveInt, data: WishCreateRequest):
    profile = get_profile(data.init_data)
    wishlist = get_object_or_404(WishList, owner=profile, id=wishlist_id)
    wish = Wish.objects.create(
        wishlist=wishlist,
        title=data.title,
        note=data.note,
        url=str(data.url) if data.url else "",
    )
    return Status(HTTPStatus.CREATED, wish)


@wishlists_router.get(
    "/{wishlist_id}/wishes/",
    response={
        HTTPStatus.OK: List[WishCreateResponse],
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
        HTTPStatus.NOT_FOUND: DetailSchema,
    },
)
def get_wishes(
    request: HttpRequest,
    wishlist_id: PositiveInt,
    init_data: Header[str],
):
    profile = get_profile(init_data)
    wishlist = get_object_or_404(WishList, owner=profile, id=wishlist_id)
    wishes = list(Wish.objects.filter(wishlist=wishlist))
    return Status(HTTPStatus.OK, wishes)


@wishlists_router.delete(
    "/{wishlist_id}/wishes/{wish_id}/",
    response={
        HTTPStatus.OK: DeletedResponse,
        HTTPStatus.UNPROCESSABLE_ENTITY: _UNPROCESSABLE,
        HTTPStatus.NOT_FOUND: DetailSchema,
    },
)
def delete_wish(request: HttpRequest, path: Path[PathWish], init_data: Header[str]):
    profile = get_profile(init_data)
    wishlist = get_object_or_404(WishList, owner=profile, id=path.wishlist_id)
    deleted_count, details = Wish.objects.filter(wishlist=wishlist, id=path.wish_id).delete()
    if deleted_count == 0:
        raise HttpError(HTTPStatus.NOT_FOUND, "Нет такого wish")
    return DeletedResponse(details=details, deleted_count=deleted_count)
