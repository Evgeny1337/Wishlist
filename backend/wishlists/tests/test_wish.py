from http import HTTPStatus

import pytest

from wishlists.models import Wish


@pytest.mark.django_db
def test_create_wish_empty_title(api_client, profile, wishlist_factory, auth_headers):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/wishes/",
        payload={
            "title": "",
            "note": "test",
            "url": "https://test-kek.ru",
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"][0]["type"] == "string_too_short"
    assert body["detail"][0]["loc"] == ["body", "data", "title"]
    assert body["detail"][0]["msg"] == "String should have at least 1 character"
    assert body["detail"][0]["ctx"] == {"min_length": 1}
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_create_wish_incorrect_url(api_client, profile, wishlist_factory, auth_headers):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/wishes/",
        payload={"title": "test", "note": "test", "url": "test"},
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"][0]["type"] == "url_parsing"
    assert body["detail"][0]["loc"] == ["body", "data", "url"]
    assert body["detail"][0]["msg"] == "Input should be a valid URL, relative URL without a base"
    assert body["detail"][0]["ctx"] == {"error": "relative URL without a base"}
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_create_wish_happy_path(api_client, profile, wishlist_factory, auth_headers):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/wishes/",
        payload={
            "url": "https://test-kek.ru",
            "title": "test",
            "note": "test",
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body["note"] == "test"
    assert body["url"] == "https://test-kek.ru/"
    assert body["title"] == "test"
    assert response.status_code == HTTPStatus.CREATED
    assert Wish.objects.filter(wishlist=wishlist, id=body["id"]).exists()


@pytest.mark.django_db
def test_get_wishes_someone_else_wishlist(
    api_client,
    profile_factory,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    profile_1 = profile_factory(telegram_user_id=1)
    profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=profile_1)
    wish_factory(wishlist=wishlist)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/",
        headers=auth_headers(2),
    )
    body = response.json()
    assert "detail" in body
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_get_wishes_empty_wish(api_client, profile, wishlist_factory, auth_headers):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body == []
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_get_wishes_happy_path(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert len(body) == 1
    item = body[0]
    assert item["id"] == wish.id
    assert item["title"] == wish.title
    assert item["url"] == wish.url
    assert item["note"] == wish.note
    assert item["wishlist_id"] == wishlist.id
    assert "created_at" in item
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_delete_wish_happy_path(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.delete(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert "deleted_count" in body
    assert body["deleted_count"] == 1
    assert response.status_code == HTTPStatus.OK
    assert not Wish.objects.filter(wishlist=wishlist, id=wish.id).exists()


@pytest.mark.django_db
def test_delete_wish_wrong_wish(
    api_client,
    profile_factory,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    my_profile = profile_factory(telegram_user_id=1)
    other_profile = profile_factory(telegram_user_id=2)
    my_wishlist = wishlist_factory(telegram_profile=my_profile)
    other_wishlist = wishlist_factory(telegram_profile=other_profile)
    wish = wish_factory(wishlist=other_wishlist)
    response = api_client.delete(
        f"/api/wishlists/{my_wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(1),
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"] == "Нет такого wish"
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_delete_wish_someone_else_wishlist(
    api_client,
    profile_factory,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    profile_factory(telegram_user_id=1)
    profile_2 = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=profile_2)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.delete(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(1),
    )
    body = response.json()
    assert "detail" in body
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_delete_wish_unauthorized(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.delete(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers={},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_get_wish_happy_path(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body["id"] == wish.id
    assert response.status_code == HTTPStatus.OK
    assert Wish.objects.filter(wishlist=wishlist, id=wish.id).exists()


@pytest.mark.django_db
def test_get_wish_someone_else_wishlist(
    api_client,
    profile_factory,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    profile_factory(telegram_user_id=1)
    profile_2 = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=profile_2)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(1),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_get_wish_wrong(api_client, profile, wishlist_factory, auth_headers):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/1/",
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_get_wish_unauthorized(api_client):
    response = api_client.get("/api/wishlists/1/wishes/1/", headers={})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_update_wish_happy_path(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist, note="keep-me")
    response = api_client.patch(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
        payload={"title": "test2", "url": "https://testurl.com"},
    )
    body = response.json()
    assert body["title"] == "test2"
    assert body["url"] == "https://testurl.com/"
    assert body["note"] == "keep-me"
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_update_wish_empty_body(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(
        wishlist=wishlist,
        title="original",
        url="https://original.ru/",
        note="original-note",
    )
    response = api_client.patch(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
        payload={},
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body["id"] == wish.id
    assert body["title"] == "original"
    assert body["url"] == "https://original.ru/"
    assert body["note"] == "original-note"


@pytest.mark.django_db
def test_update_wish_null_url(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist, url="https://to-clear.ru/")
    response = api_client.patch(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
        payload={"url": None},
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body["url"] == ""
    wish.refresh_from_db()
    assert wish.url == ""


@pytest.mark.django_db
def test_update_wish_someone_else_wishlist(
    api_client,
    profile_factory,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    profile_factory(telegram_user_id=1)
    profile_2 = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=profile_2)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.patch(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(1),
        payload={"title": "hacked"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_update_wish_wrong_wish(api_client, profile, wishlist_factory, auth_headers):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.patch(
        f"/api/wishlists/{wishlist.id}/wishes/99999/",
        headers=auth_headers(profile.telegram_user_id),
        payload={},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_update_wish_with_empty_title(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.patch(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
        payload={"title": ""},
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"][0]["type"] == "string_too_short"
    assert body["detail"][0]["loc"] == ["body", "body", "title"]
    assert body["detail"][0]["msg"] == "String should have at least 1 character"
    assert body["detail"][0]["ctx"] == {"min_length": 1}
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_update_wish_unauthorized(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.patch(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers={},
        payload={"title": "test3"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
