from http import HTTPStatus

import pytest

from wishlists.models import WishReservation


@pytest.mark.django_db
def test_wish_reserve_happy_path(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers=auth_headers(profile.telegram_user_id),
        payload={},
    )
    body = response.json()
    assert body["wish"] == wish.id
    assert body["is_reserved"] is True
    assert response.status_code == HTTPStatus.CREATED
    assert WishReservation.objects.filter(wish=wish, profile=profile).exists()


@pytest.mark.django_db
def test_wish_reserve_already_exists(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    api_client.post(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers=auth_headers(profile.telegram_user_id),
        payload={},
    )
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers=auth_headers(profile.telegram_user_id),
        payload={},
    )
    body = response.json()
    assert body["detail"] == "Желание уже забронировано"
    assert response.status_code == HTTPStatus.CONFLICT


@pytest.mark.django_db
def test_wish_reserve_conflict_other_user(
    api_client,
    profile_factory,
    wishlist_factory,
    wish_factory,
    auth_headers,
    wish_reservation_factory,
):
    owner = profile_factory(telegram_user_id=1)
    other = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    wish = wish_factory(wishlist=wishlist)
    wish_reservation_factory(wish=wish, profile=owner)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers=auth_headers(other.telegram_user_id),
        payload={},
    )
    body = response.json()
    assert body["detail"] == "Желание уже забронировано"
    assert response.status_code == HTTPStatus.CONFLICT


@pytest.mark.django_db
def test_wish_reserve_unauthorized(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.post(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers={},
        payload={},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_wish_reserve_wrong_wishlist(
    api_client,
    profile,
    profile_factory,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    other = profile_factory(telegram_user_id=2)
    my_wishlist = wishlist_factory(telegram_profile=profile)
    other_wishlist = wishlist_factory(telegram_profile=other)
    wish = wish_factory(wishlist=other_wishlist)
    response = api_client.post(
        f"/api/wishlists/{my_wishlist.id}/wishes/{wish.id}/reserve/",
        headers=auth_headers(profile.telegram_user_id),
        payload={},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_get_wish_reserve_not_reserved(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body["wish"] == wish.id
    assert body["is_reserved"] is False
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_get_wish_reserve_happy_path(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
    wish_reservation_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    wish_reservation_factory(wish=wish, profile=profile)
    response = api_client.get(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body["wish"] == wish.id
    assert body["is_reserved"] is True
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_delete_wish_reserve_happy_path(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
    wish_reservation_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    wish_reservation_factory(wish=wish, profile=profile)
    response = api_client.delete(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body["wish"] == wish.id
    assert response.status_code == HTTPStatus.OK
    assert not WishReservation.objects.filter(wish=wish).exists()


@pytest.mark.django_db
def test_delete_wish_reserve_someone_else(
    api_client,
    wishlist_factory,
    wish_factory,
    auth_headers,
    wish_reservation_factory,
    profile_factory,
):
    profile_1 = profile_factory(telegram_user_id=1)
    profile_2 = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=profile_2)
    wish = wish_factory(wishlist=wishlist)
    wish_reservation_factory(wish=wish, profile=profile_2)
    response = api_client.delete(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers=auth_headers(profile_1.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert WishReservation.objects.filter(wish=wish, profile=profile_2).exists()


@pytest.mark.django_db
def test_delete_wish_reserve_not_exists(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.delete(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_delete_wish_reserve_wrong_wish(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
    wish_reservation_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    wish_reservation_factory(wish=wish, profile=profile)
    response = api_client.delete(
        f"/api/wishlists/{wishlist.id}/wishes/99999/reserve/",
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_delete_wish_reserve_wrong_bearer(
    api_client,
    profile,
    wishlist_factory,
    wish_factory,
    auth_headers,
    wish_reservation_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    wish_reservation_factory(wish=wish, profile=profile)
    response = api_client.delete(
        f"/api/wishlists/{wishlist.id}/wishes/{wish.id}/reserve/",
        headers={"Authorization": "Bearer test-wrong-token"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
