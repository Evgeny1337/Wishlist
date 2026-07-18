from http import HTTPStatus

import pytest

from django.test import override_settings

from invites.tests.helpers import fresh_signed_init_data_user_id, BOT_TOKEN_VERIFY
from wishlists.models import WishList


@pytest.mark.django_db
def test_wishlists_get_invalid_id(api_client):
    response = api_client.get(
        "/api/wishlists/",
        headers={"init_data": "test", "wishlist_id": "test"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["detail"] == "Ошибка валидации параметров"


@pytest.mark.django_db
def test_wishlists_get_empty_id(api_client):
    response = api_client.get(
        "/api/wishlists/",
        headers={"init_data": "test"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["detail"] == "Ошибка валидации параметров"


@pytest.mark.django_db
def test_wishlists_get_invalid_headers(api_client):
    response = api_client.get(
        "/api/wishlists/",
        headers={},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["detail"] == "Ошибка валидации параметров"


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_wishlists_get_unknown_wishlist(
        api_client,
        profile,
):
    init_data = fresh_signed_init_data_user_id(1)
    response = api_client.get(
        "/api/wishlists/",
        headers={"init_data": init_data, "wishlist_id": 1},
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'Not Found'
    assert response.status_code == HTTPStatus.NOT_FOUND



@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_wishlists_get_someone_else(
        api_client,
        profile_factory,
        wishlist_factory,
):
    profile_1 = profile_factory(telegram_user_id=1)
    profile_factory(telegram_user_id=2)
    wishlist_1 = wishlist_factory(telegram_profile=profile_1)
    init_data = fresh_signed_init_data_user_id(2)
    response = api_client.get(
        "/api/wishlists/",
        headers={"init_data": init_data, "wishlist_id": wishlist_1.id},
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'Not Found'
    assert response.status_code == HTTPStatus.NOT_FOUND


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_wishlists_get_happy(
        api_client,
        profile,
        wishlist_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    init_data = fresh_signed_init_data_user_id(1)
    response = api_client.get(
        "/api/wishlists/",
        headers={"init_data": init_data, "wishlist_id": wishlist.id},
    )
    body = response.json()
    assert body['title'] == 'test'
    assert response.status_code == HTTPStatus.OK
    assert WishList.objects.filter(owner=profile).count() == 1


