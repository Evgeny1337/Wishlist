from http import HTTPStatus

import pytest
from django.test import override_settings

from invites.tests.helpers import BOT_TOKEN_VERIFY, fresh_signed_init_data_user_id
from wishlists.models import WishList


@pytest.mark.django_db
def test_delete_wishlist_invalid_id(api_client):
    response = api_client.delete(
        "/api/wishlists/test/",
        headers={"init_data": "test"},
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"][0]["loc"] == ["path", "wishlist_id"]
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_delete_wishlist_missing_init_data(api_client):
    response = api_client.delete(
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
def test_delete_wishlist_wrong_id(
        api_client,
        profile,
):
    init_data = fresh_signed_init_data_user_id(1)
    response = api_client.delete(
        "/api/wishlists/2/",
        headers={"init_data": init_data},
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"] == "Такого вишлиста нету"
    assert response.status_code == HTTPStatus.NOT_FOUND


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_delete_wishlist_someone_else(
        api_client,
        profile_factory,
        wishlist_factory,
):
    profile_1 = profile_factory(telegram_user_id=1)
    profile_factory(telegram_user_id=2)
    wishlist_1 = wishlist_factory(telegram_profile=profile_1)
    init_data = fresh_signed_init_data_user_id(2)
    response = api_client.delete(
        f"/api/wishlists/{wishlist_1.id}/",
        headers={"init_data": init_data},
    )
    body = response.json()
    assert body["detail"] == "Такого вишлиста нету"
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert WishList.objects.filter(id=wishlist_1.id).exists()


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_delete_wishlist_happy_path(
        api_client,
        profile,
        wishlist_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    init_data = fresh_signed_init_data_user_id(1)
    response = api_client.delete(
        f"/api/wishlists/{wishlist.id}/",
        headers={"init_data": init_data},
    )
    body = response.json()
    assert "deleted_count" in body
    assert body["deleted_count"] == 1
    assert response.status_code == HTTPStatus.OK
    assert not WishList.objects.filter(owner=profile, id=wishlist.id).exists()
