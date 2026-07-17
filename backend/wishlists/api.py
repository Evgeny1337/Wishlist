from http import HTTPStatus

from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from pydantic import PositiveInt, ValidationError
from django.http import HttpRequest
from ninja import Router, Schema, ModelSchema, Field, Status

from django.conf import settings
from invites.models import TelegramProfile
from invites.telegram_init_data import verify_init_data, InvalidInitData
from invites.telegram_webapp_user import telegram_user_init_data
from .models import WishList

wishlists_router = Router()


class ErrorSchema(Schema):
    detail: dict[str,str] = Field(description='Ошибка валидации')


class WishListDeletedResponse(Schema):
    deleted_count: PositiveInt = Field(description='Количиство удаленных')
    details: dict[str, int] = Field(description='Количество удаленных объектов')


class WishListCreateRequest(Schema):
    init_data: str = Field(description='Авторизационные данные ')
    title: str = Field(description='Заголовок', min_length=1)

class WishListDeleteGet(Schema):
    init_data: str = Field(description='Авторизационные данные ')
    wishlist_id: PositiveInt = Field(description="ID Вишлиста")


class WishListResponseSchema(ModelSchema):
    class Meta:
        model = WishList
        fields = ['id', 'owner', 'title', 'created_at']

def get_profile(init_data: str) -> TelegramProfile:
    if  not init_data:
        raise HttpError(HTTPStatus.UNPROCESSABLE_ENTITY,"пустой initData")
    try:
        pairs = verify_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)
        user = telegram_user_init_data(pairs)
    except InvalidInitData as exc:
        raise HttpError(HTTPStatus.UNPROCESSABLE_ENTITY, str(exc)) from exc
    return get_object_or_404(TelegramProfile, telegram_user_id=user.id)

def validate_wishlist_request(request: HttpRequest) -> WishListDeleteGet:
    try:
        return WishListDeleteGet.model_validate({
            'init_data': request.headers.get('initData') or '',
            'wishlist_id': request.headers.get('wishListId')
        })
    except ValidationError as e:
        raise HttpError(422, e.errors()) from e


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
        HTTPStatus.NOT_IMPLEMENTED: str
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
        HTTPStatus.OK: WishListDeletedResponse,
        HTTPStatus.NOT_FOUND: str,
    },
)
def delete_wishlist(request: HttpRequest):
    validate_data = validate_wishlist_request(request)
    profile = get_profile(validate_data.init_data)
    deleted_count, details = WishList.objects.filter(owner=profile, id=validate_data.wishlist_id).delete()
    if deleted_count == 0:
        raise HttpError(HTTPStatus.NOT_FOUND, "Такого вишлиста нету")
    return WishListDeletedResponse(details=details, deleted_count=deleted_count)