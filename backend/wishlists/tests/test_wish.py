from http import HTTPStatus

import pytest

from wishlists.models import Wish, WishReservation


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
    assert body["is_reserved"] is False
    assert body["reserved_by_me"] is False
    assert body["priority"] == Wish.WishPriority.LOW
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
    assert item["is_reserved"] is False
    assert item["reserved_by_me"] is False
    assert "created_at" in item
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_get_wishes_with_reservation_flags(
    api_client,
    profile,
    profile_factory,
    wishlist_factory,
    wish_factory,
    wish_reservation_factory,
    auth_headers,
):
    other = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=profile)
    mine = wish_factory(wishlist=wishlist, title="mine")
    others = wish_factory(wishlist=wishlist, title="others")
    wish_reservation_factory(wish=mine, profile=profile)
    wish_reservation_factory(wish=others, profile=other)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = {item["id"]: item for item in response.json()}
    assert response.status_code == HTTPStatus.OK
    assert body[mine.id]["is_reserved"] is True
    assert body[mine.id]["reserved_by_me"] is True
    assert body[others.id]["is_reserved"] is True
    assert body[others.id]["reserved_by_me"] is False


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
    assert body["is_reserved"] is False
    assert body["reserved_by_me"] is False
    assert response.status_code == HTTPStatus.OK
    assert Wish.objects.filter(wishlist=wishlist, id=wish.id).exists()


@pytest.mark.django_db
def test_get_wish_reserved_by_me(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    wish_reservation_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    wish_reservation_factory(wish=wish, profile=profile)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body["is_reserved"] is True
    assert body["reserved_by_me"] is True


@pytest.mark.django_db
def test_get_wish_reserved_by_someone_else(
    api_client,
    profile,
    profile_factory,
    wishlist_factory,
    wish_factory,
    wish_reservation_factory,
    auth_headers,
):
    other = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    wish_reservation_factory(wish=wish, profile=other)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body["is_reserved"] is True
    assert body["reserved_by_me"] is False


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
    assert body["is_reserved"] is False
    assert body["reserved_by_me"] is False
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_update_wish_clears_reservation(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    wish_reservation_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    wish_reservation_factory(wish=wish, profile=profile)
    assert WishReservation.objects.filter(wish=wish).exists()
    response = api_client.patch(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
        payload={"title": "changed"},
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body["title"] == "changed"
    assert body["is_reserved"] is False
    assert body["reserved_by_me"] is False
    assert not WishReservation.objects.filter(wish=wish).exists()


@pytest.mark.django_db
def test_update_wish_empty_body_keeps_reservation(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    wish_reservation_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(
        wishlist=wishlist,
        title="original",
        url="https://original.ru/",
        note="original-note",
    )
    wish_reservation_factory(wish=wish, profile=profile)
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
    assert body["is_reserved"] is True
    assert body["reserved_by_me"] is True
    assert WishReservation.objects.filter(wish=wish, profile=profile).exists()


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


@pytest.mark.django_db
def test_create_wish_with_high_priority(
    api_client,
    profile,
    wishlist_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/wishes/",
        payload={
            "title": "urgent",
            "note": "test",
            "url": "https://test-kek.ru",
            "priority": Wish.WishPriority.HIGH,
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.CREATED
    assert body["priority"] == Wish.WishPriority.HIGH
    wish = Wish.objects.get(id=body["id"])
    assert wish.priority == Wish.WishPriority.HIGH


@pytest.mark.django_db
@pytest.mark.parametrize("bad_priority", [0, 4, -1])
def test_create_wish_invalid_priority(
    api_client,
    profile,
    wishlist_factory,
    auth_headers,
    bad_priority,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/wishes/",
        payload={
            "title": "test",
            "note": "test",
            "url": "https://test-kek.ru",
            "priority": bad_priority,
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "detail" in response.json()


@pytest.mark.django_db
def test_update_wish_priority(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist, priority=Wish.WishPriority.LOW)
    response = api_client.patch(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
        payload={"priority": Wish.WishPriority.HIGH},
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body["priority"] == Wish.WishPriority.HIGH
    wish.refresh_from_db()
    assert wish.priority == Wish.WishPriority.HIGH


@pytest.mark.django_db
@pytest.mark.parametrize("bad_priority", [0, 4])
def test_update_wish_invalid_priority(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
    bad_priority,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.patch(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
        payload={"priority": bad_priority},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_get_wishes_ordered_by_priority(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    low = wish_factory(wishlist=wishlist, title="low", priority=Wish.WishPriority.LOW)
    high = wish_factory(wishlist=wishlist, title="high", priority=Wish.WishPriority.HIGH)
    medium = wish_factory(
        wishlist=wishlist,
        title="medium",
        priority=Wish.WishPriority.MEDIUM,
    )
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert [item["id"] for item in body] == [high.id, medium.id, low.id]
    assert [item["priority"] for item in body] == [
        Wish.WishPriority.HIGH,
        Wish.WishPriority.MEDIUM,
        Wish.WishPriority.LOW,
    ]
