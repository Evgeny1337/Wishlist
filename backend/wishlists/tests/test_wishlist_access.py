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


@pytest.mark.django_db
def test_someoneelse_list_happy_path(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wishlist_access_factory,
):
    owner = profile_factory(telegram_user_id=1)
    viewer = profile_factory(telegram_user_id=2)
    shared = wishlist_factory(telegram_profile=owner, title="shared")
    wishlist_factory(telegram_profile=owner, title="not-shared")
    wishlist_factory(telegram_profile=viewer, title="viewer-own")
    wishlist_access_factory(wishlist=shared, profile=viewer)

    response = api_client.get(
        "/api/wishlists/someoneelse",
        headers=auth_headers(viewer.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert len(body) == 1
    assert body[0]["id"] == shared.id
    assert body[0]["title"] == "shared"
    assert body[0]["owner"] == owner.id


@pytest.mark.django_db
def test_someoneelse_list_empty(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    viewer = profile_factory(telegram_user_id=2)
    wishlist_factory(telegram_profile=owner, title="foreign")
    wishlist_factory(telegram_profile=viewer, title="own")

    response = api_client.get(
        "/api/wishlists/someoneelse",
        headers=auth_headers(viewer.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


@pytest.mark.django_db
def test_someoneelse_excludes_own_wishlists(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wishlist_access_factory,
):
    """Даже при access на чужой список свои wishlists в someoneelse не попадают."""
    owner = profile_factory(telegram_user_id=1)
    viewer = profile_factory(telegram_user_id=2)
    shared = wishlist_factory(telegram_profile=owner, title="shared")
    own = wishlist_factory(telegram_profile=viewer, title="own")
    wishlist_access_factory(wishlist=shared, profile=viewer)

    response = api_client.get(
        "/api/wishlists/someoneelse",
        headers=auth_headers(viewer.telegram_user_id),
    )
    ids = {item["id"] for item in response.json()}
    assert response.status_code == HTTPStatus.OK
    assert shared.id in ids
    assert own.id not in ids


@pytest.mark.django_db
def test_someoneelse_multiple_shared(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wishlist_access_factory,
):
    owner_a = profile_factory(telegram_user_id=1)
    owner_b = profile_factory(telegram_user_id=2)
    viewer = profile_factory(telegram_user_id=3)
    wl_a = wishlist_factory(telegram_profile=owner_a, title="a")
    wl_b = wishlist_factory(telegram_profile=owner_b, title="b")
    wishlist_access_factory(wishlist=wl_a, profile=viewer)
    wishlist_access_factory(wishlist=wl_b, profile=viewer)

    response = api_client.get(
        "/api/wishlists/someoneelse",
        headers=auth_headers(viewer.telegram_user_id),
    )
    ids = {item["id"] for item in response.json()}
    assert response.status_code == HTTPStatus.OK
    assert ids == {wl_a.id, wl_b.id}


@pytest.mark.django_db
def test_someoneelse_without_auth(api_client):
    response = api_client.get("/api/wishlists/someoneelse", headers={})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_access_users_happy_path(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wishlist_access_factory,
):
    owner = profile_factory(telegram_user_id=1, username="owner")
    viewer_a = profile_factory(telegram_user_id=2, username="alice")
    viewer_b = profile_factory(telegram_user_id=3, username="bob")
    wishlist = wishlist_factory(telegram_profile=owner)
    wishlist_access_factory(wishlist=wishlist, profile=viewer_a)
    wishlist_access_factory(wishlist=wishlist, profile=viewer_b)

    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/access_users/",
        headers=auth_headers(owner.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert {item["telegram_user_id"] for item in body} == {
        viewer_a.telegram_user_id,
        viewer_b.telegram_user_id,
    }
    assert {item["username"] for item in body} == {"alice", "bob"}
    assert all(set(item) == {"telegram_user_id", "username"} for item in body)


@pytest.mark.django_db
def test_access_users_empty(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    wishlist = wishlist_factory(telegram_profile=owner)

    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/access_users/",
        headers=auth_headers(owner.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


@pytest.mark.django_db
def test_access_users_not_owner(
    api_client,
    wishlist_factory,
    profile_factory,
    auth_headers,
    wishlist_access_factory,
):
    owner = profile_factory(telegram_user_id=1)
    viewer = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    wishlist_access_factory(wishlist=wishlist, profile=viewer)

    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/access_users/",
        headers=auth_headers(viewer.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_access_users_without_auth(
    api_client,
    wishlist_factory,
    profile_factory,
):
    owner = profile_factory(telegram_user_id=1)
    wishlist = wishlist_factory(telegram_profile=owner)

    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/access_users/",
        headers={},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
