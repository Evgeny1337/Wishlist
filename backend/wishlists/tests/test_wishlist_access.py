from http import HTTPStatus

import pytest

from wishlists.models import WishListAccess, WishReservation


@pytest.mark.django_db
def test_wishlist_access_grant_happy_path(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/grant/",
        headers=auth_headers(owner.telegram_user_id),
        payload={
            "profile": profile.telegram_user_id,
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert WishListAccess.objects.filter(wishlist=wishlist, profile=profile).exists()


@pytest.mark.django_db
def test_wishlist_access_grant_already_exists(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wishlist_access_factory,
):
    owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    wishlist_access_factory(wishlist=wishlist, profile=profile)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/grant/",
        headers=auth_headers(owner.telegram_user_id),
        payload={
            "profile": profile.telegram_user_id,
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT


@pytest.mark.django_db
def test_wishlist_access_grant_self(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    wishlist = wishlist_factory(telegram_profile=owner)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/grant/",
        headers=auth_headers(owner.telegram_user_id),
        payload={
            "profile": owner.telegram_user_id,
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_wishlist_access_grant_not_owner(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    profile_1 = profile_factory(telegram_user_id=2)
    profile_2 = profile_factory(telegram_user_id=3)
    wishlist = wishlist_factory(telegram_profile=owner)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/grant/",
        headers=auth_headers(profile_1.telegram_user_id),
        payload={
            "profile": profile_2.telegram_user_id,
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_wishlist_access_list_happy(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wishlist_access_factory,
):
    owner = profile_factory(telegram_user_id=1)
    profile_1 = profile_factory(telegram_user_id=2)
    profile_2 = profile_factory(telegram_user_id=3)
    wishlist = wishlist_factory(telegram_profile=owner)
    wishlist_access_factory(wishlist=wishlist, profile=profile_1)
    wishlist_access_factory(wishlist=wishlist, profile=profile_2)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/grant/",
        headers=auth_headers(owner.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert {item["profile"] for item in body} == {profile_1.id, profile_2.id}
    assert {item["wishlist"] for item in body} == {wishlist.id}


@pytest.mark.django_db
def test_viewer_get_wishes_ok(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wishlist_access_factory,
    wish_factory,
):
    owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    wish = wish_factory(wishlist=wishlist)
    wishlist_access_factory(wishlist=wishlist, profile=profile)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert len(body) == 1
    assert body[0]["id"] == wish.id


@pytest.mark.django_db
def test_viewer_without_access_get_wishes_404(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wish_factory,
):
    owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_viewer_patch_wish_forbidden(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wish_factory,
    wishlist_access_factory,
):
    owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    wish = wish_factory(wishlist=wishlist, title="original")
    wishlist_access_factory(wishlist=wishlist, profile=profile)
    response = api_client.patch(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/",
        headers=auth_headers(profile.telegram_user_id),
        payload={"title": "test2", "url": "https://testurl.com"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    wish.refresh_from_db()
    assert wish.title == "original"


@pytest.mark.django_db
def test_viewer_reserve_ok(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wish_factory,
    wishlist_access_factory,
):
    owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    wish = wish_factory(wishlist=wishlist)
    wishlist_access_factory(wishlist=wishlist, profile=profile)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers=auth_headers(profile.telegram_user_id),
        payload={},
    )
    assert response.status_code == HTTPStatus.CREATED
    assert WishReservation.objects.filter(wish=wish, profile=profile).exists()


@pytest.mark.django_db
def test_wishlist_access_revoke_then_404(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wishlist_access_factory,
):
    owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    wishlist_access_factory(wishlist=wishlist, profile=profile)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.OK
    response = api_client.delete(
        f"/api/wishlists/{wishlist.id}/grant/",
        headers=auth_headers(owner.telegram_user_id),
        payload={"profile": profile.telegram_user_id},
    )
    assert response.status_code == HTTPStatus.OK
    assert not WishListAccess.objects.filter(wishlist=wishlist, profile=profile).exists()
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
