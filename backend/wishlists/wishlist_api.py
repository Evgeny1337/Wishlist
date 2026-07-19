from http import HTTPStatus
from typing import List

from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from pydantic import ValidationError, PositiveInt
from django.http import HttpRequest
from ninja import Router, Status, Path, Header

from .helpers import get_profile
from .models import WishList, Wish
from .schemas import WishListDeleteGet, WishListResponseSchema, ErrorSchema, WishListCreateRequest, \
    DeletedResponse, WishCreateRequest, WishCreateResponse, PathWish

wishlists_router = Router()


def validate_wishlist_request(request: HttpRequest) -> WishListDeleteGet:
    try:
        return WishListDeleteGet.model_validate({
            'init_data': request.headers.get('init_data') or '',
            'wishlist_id': request.headers.get('wishlist_id')
        })
    except ValidationError:
        raise HttpError(HTTPStatus.UNPROCESSABLE_ENTITY, 'Ошибка валидации параметров')


@wishlists_router.post(
    '/',
    response={
        HTTPStatus.CREATED: WishListResponseSchema,
        HTTPStatus.BAD_REQUEST: ErrorSchema,
        HTTPStatus.UNPROCESSABLE_ENTITY: ErrorSchema
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
    '/',
    response={
        HTTPStatus.OK: WishListResponseSchema,
        HTTPStatus.NOT_FOUND: str,
        HTTPStatus.UNPROCESSABLE_ENTITY: str
    },
)
def get_wishlist(request: HttpRequest):
    validate_data = validate_wishlist_request(request)
    profile = get_profile(validate_data.init_data)
    wishlist = get_object_or_404(WishList, owner=profile, id=validate_data.wishlist_id)
    return Status(HTTPStatus.OK, wishlist)


@wishlists_router.delete(
    '/',
    response={
        HTTPStatus.OK: DeletedResponse,
        HTTPStatus.NOT_FOUND: str,
    },
)
def delete_wishlist(request: HttpRequest):
    validate_data = validate_wishlist_request(request)
    profile = get_profile(validate_data.init_data)
    deleted_count, details = WishList.objects.filter(owner=profile, id=validate_data.wishlist_id).delete()
    if deleted_count == 0:
        raise HttpError(HTTPStatus.NOT_FOUND, "Такого вишлиста нету")
    return DeletedResponse(details=details, deleted_count=deleted_count)


@wishlists_router.post(
    '/{wishlist_id}/wishes/',
    response={
        HTTPStatus.UNPROCESSABLE_ENTITY: ErrorSchema,
        HTTPStatus.NOT_FOUND: str,
        HTTPStatus.CREATED: WishCreateResponse
    }
)
def create_wish(request: HttpRequest, wishlist_id:PositiveInt, data: WishCreateRequest):
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
    '/{wishlist_id}/wishes/',
    response={
        HTTPStatus.UNPROCESSABLE_ENTITY: ErrorSchema,
        HTTPStatus.NOT_FOUND: str,
        HTTPStatus.OK: List[WishCreateResponse]
    }
)
def get_wishes(request: HttpRequest, wishlist_id: PositiveInt):
    init_data = request.headers.get('init_data') or ""
    profile = get_profile(init_data)
    wishlist = get_object_or_404(WishList, owner=profile, id=wishlist_id)
    wishes = list(Wish.objects.filter(wishlist=wishlist))
    return Status(HTTPStatus.OK, wishes)


@wishlists_router.delete(
    '/{wishlist_id}/wishes/{wish_id}/',
    response={
        HTTPStatus.OK: DeletedResponse,
        HTTPStatus.UNPROCESSABLE_ENTITY: ErrorSchema,
        HTTPStatus.NOT_FOUND: str,
    }
)
def delete_wish(request: HttpRequest, path: Path[PathWish], init_data: Header[str]):
    profile = get_profile(init_data)
    wishlist = get_object_or_404(WishList, owner=profile, id=path.wishlist_id)
    deleted_count, details = Wish.objects.filter(wishlist=wishlist, id=path.wish_id).delete()
    if deleted_count == 0:
        raise HttpError(HTTPStatus.NOT_FOUND, "Нет такого wish")
    return DeletedResponse(details=details, deleted_count=deleted_count)

