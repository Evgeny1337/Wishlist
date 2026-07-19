from http import HTTPStatus

import pytest

from django.test import override_settings

from invites.tests.helpers import fresh_signed_init_data_user_id, BOT_TOKEN_VERIFY
from wishlists.models import WishList


@pytest.mark.django_db
def test_wishlists_get_invalid_id(api_client):
    response = api_client.get(
        "/api/wishlists/test/",
        headers={"init_data": "test"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    body = response.json()
    assert "detail" in body
    assert body["detail"][0]["loc"] == ["path", "wishlist_id"]


@pytest.mark.django_db
def test_wishlists_get_missing_init_data(api_client):
    response = api_client.get(
        "/api/wishlists/1/",
        headers={},
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"][0]["type"] == "missing"
    assert body["detail"][0]["loc"] == ["header", "init_data"]
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_wishlists_get_unknown_wishlist(
        api_client,
        profile,
):
    init_data = fresh_signed_init_data_user_id(1)
    response = api_client.get(
        "/api/wishlists/1/",
        headers={"init_data": init_data},
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"] == "Not Found"
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
        f"/api/wishlists/{wishlist_1.id}/",
        headers={"init_data": init_data},
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"] == "Not Found"
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
        f"/api/wishlists/{wishlist.id}/",
        headers={"init_data": init_data},
    )
    body = response.json()
    assert body["id"] == wishlist.id
    assert body["title"] == "test"
    assert response.status_code == HTTPStatus.OK
    assert WishList.objects.filter(owner=profile).count() == 1
