from http import HTTPStatus

import pytest

from wishlists.models import WishList


@pytest.mark.django_db
def test_wishlists_get_invalid_id(api_client, profile, auth_headers):
    response = api_client.get(
        "/api/wishlists/test/",
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    body = response.json()
    assert "detail" in body
    assert body["detail"][0]["loc"] == ["path", "wishlist_id"]


@pytest.mark.django_db
def test_wishlists_get_unauthorized(api_client):
    response = api_client.get("/api/wishlists/1/", headers={})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_wishlists_get_unknown_wishlist(api_client, profile, auth_headers):
    response = api_client.get(
        "/api/wishlists/1/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert "detail" in body
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_wishlists_get_someone_else(
    api_client,
    profile_factory,
    wishlist_factory,
    auth_headers,
):
    profile_1 = profile_factory(telegram_user_id=1)
    profile_factory(telegram_user_id=2)
    wishlist_1 = wishlist_factory(telegram_profile=profile_1)
    response = api_client.get(
        f"/api/wishlists/{wishlist_1.id}/",
        headers=auth_headers(2),
    )
    body = response.json()
    assert "detail" in body
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_wishlists_get_happy(api_client, profile, wishlist_factory, auth_headers):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body["id"] == wishlist.id
    assert body["title"] == "test"
    assert body["events"] == []
    assert response.status_code == HTTPStatus.OK
    assert WishList.objects.filter(owner=profile).count() == 1


@pytest.mark.django_db
def test_wishlists_get_with_events(
    api_client,
    profile,
    wishlist_factory,
    event_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    event = event_factory(wishlist=wishlist, owner=profile, title="Birthday")
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert len(body["events"]) == 1
    assert body["events"][0]["id"] == event.id
    assert body["events"][0]["title"] == "Birthday"
    assert body["events"][0]["wishlist_id"] == wishlist.id


@pytest.mark.django_db
def test_wishlist_get_all_happy_path(
    api_client,
    profile,
    wishlist_factory,
    auth_headers,
):
    wishlist_factory(telegram_profile=profile)
    wishlist_factory(telegram_profile=profile)
    response = api_client.get(
        "/api/wishlists/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert len(body) == 2
    assert all("events" in item and item["events"] == [] for item in body)
    assert WishList.objects.filter(owner=profile).count() == 2


@pytest.mark.django_db
def test_wishlist_get_all_with_events(
    api_client,
    profile,
    wishlist_factory,
    event_factory,
    auth_headers,
):
    wl_with_event = wishlist_factory(telegram_profile=profile, title="with-event")
    wl_empty = wishlist_factory(telegram_profile=profile, title="empty")
    event = event_factory(wishlist=wl_with_event, owner=profile, title="Party")

    response = api_client.get(
        "/api/wishlists/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert len(body) == 2

    by_id = {item["id"]: item for item in body}
    assert by_id[wl_empty.id]["events"] == []
    assert len(by_id[wl_with_event.id]["events"]) == 1
    assert by_id[wl_with_event.id]["events"][0]["id"] == event.id
    assert by_id[wl_with_event.id]["events"][0]["title"] == "Party"
    assert by_id[wl_with_event.id]["events"][0]["wishlist_id"] == wl_with_event.id


@pytest.mark.django_db
def test_wishlist_get_all_empty_wishlists(api_client, profile, auth_headers):
    response = api_client.get(
        "/api/wishlists/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body == []
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_wishlist_get_all_unauthorized(api_client):
    response = api_client.get("/api/wishlists/", headers={})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
