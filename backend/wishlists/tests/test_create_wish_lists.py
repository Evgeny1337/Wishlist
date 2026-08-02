from http import HTTPStatus

import pytest

from wishlists.models import WishList


@pytest.mark.django_db
def test_wishlist_create_unauthorized(api_client):
    response = api_client.post("/api/wishlists/", payload={"title": "test"})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_wishlist_create_bad_bearer(api_client):
    response = api_client.post(
        "/api/wishlists/",
        payload={"title": "test"},
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_wishlist_create_empty_title(api_client, profile, auth_headers):
    response = api_client.post(
        "/api/wishlists/",
        payload={"title": ""},
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"][0]["type"] == "string_too_short"
    assert body["detail"][0]["ctx"] == {"min_length": 1}
    assert body["detail"][0]["msg"] == "String should have at least 1 character"
    assert body["detail"][0]["loc"] == ["body", "data", "title"]
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_wishlist_create_unknown_user(api_client, auth_headers):
    response = api_client.post(
        "/api/wishlists/",
        payload={"title": "test"},
        headers=auth_headers(99999),
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_wishlist_create_not_valid_data(api_client, profile, auth_headers, client):
    response = client.post(
        "/api/wishlists/",
        data="test",
        content_type="application/json",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"] == "Cannot parse request body"
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_wishlist_create_happy_path(api_client, profile, auth_headers):
    response = api_client.post(
        "/api/wishlists/",
        payload={"title": "test"},
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.CREATED
    assert WishList.objects.filter(owner=profile, title="test").exists()
