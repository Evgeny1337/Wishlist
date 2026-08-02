from http import HTTPStatus

import pytest

from wishlists.models import WishList


@pytest.mark.django_db
def test_delete_wishlist_invalid_id(api_client, profile, auth_headers):
    response = api_client.delete(
        "/api/wishlists/test/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"][0]["loc"] == ["path", "wishlist_id"]
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_delete_wishlist_unauthorized(api_client):
    response = api_client.delete("/api/wishlists/1/", headers={})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_delete_wishlist_wrong_id(api_client, profile, auth_headers):
    response = api_client.delete(
        "/api/wishlists/2/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"] == "Такого вишлиста нету"
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_delete_wishlist_someone_else(
    api_client,
    profile_factory,
    wishlist_factory,
    auth_headers,
):
    profile_1 = profile_factory(telegram_user_id=1)
    profile_factory(telegram_user_id=2)
    wishlist_1 = wishlist_factory(telegram_profile=profile_1)
    response = api_client.delete(
        f"/api/wishlists/{wishlist_1.id}/",
        headers=auth_headers(2),
    )
    body = response.json()
    assert body["detail"] == "Такого вишлиста нету"
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert WishList.objects.filter(id=wishlist_1.id).exists()


@pytest.mark.django_db
def test_delete_wishlist_happy_path(
    api_client,
    profile,
    wishlist_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.delete(
        f"/api/wishlists/{wishlist.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert "deleted_count" in body
    assert body["deleted_count"] == 1
    assert response.status_code == HTTPStatus.OK
    assert not WishList.objects.filter(owner=profile, id=wishlist.id).exists()
