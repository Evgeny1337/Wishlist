from datetime import datetime

from django.utils import timezone

import pytest

from invites.jwt_tokens import issue_token_pair
from invites.models import TelegramProfile
from wishlists.models import WishList, Wish, WishReservation, Event, WishListAccess, GiftPlan, GiftPlanItem


@pytest.fixture(autouse=True)
def _jwt_settings(settings):
    settings.JWT_SECRET = "test-jwt-secret-at-least-32-bytes!!"
    settings.JWT_ACCESS_TTL_SEC = 3600
    settings.JWT_REFRESH_TTL_SEC = 2592000


@pytest.fixture
def auth_headers():
    def _make(telegram_user_id: int = 1) -> dict[str, str]:
        access = issue_token_pair(telegram_user_id).access_token
        return {"Authorization": f"Bearer {access}"}

    return _make


@pytest.fixture
def wish_factory(db):
    def _create_wish(
        wishlist: WishList,
        url: str = "https://test.ru",
        note: str = "test",
        title: str = "test",
        **kwargs,
    ):
        return Wish.objects.create(
            wishlist=wishlist,
            url=url,
            note=note,
            title=title,
            **kwargs,
        )

    return _create_wish


@pytest.fixture()
def wishlist_factory(db):
    def _create_wishlist(
        telegram_profile: TelegramProfile,
        title: str = "test",
        **kwargs,
    ):
        return WishList.objects.create(
            owner=telegram_profile,
            title=title,
            **kwargs,
        )

    return _create_wishlist


@pytest.fixture()
def wish_reservation_factory(db):
    def _create_wish_reservation(wish: Wish, profile: TelegramProfile):
        return WishReservation.objects.create(
            profile=profile,
            wish=wish,
        )
    return _create_wish_reservation


@pytest.fixture()
def event_factory(db):
    def _create_event(
        wishlist: WishList,
        owner: TelegramProfile,
        title: str = "test",
        starts_at: datetime | None = None,
    ):
        return Event.objects.create(
            wishlist=wishlist,
            owner=owner,
            title=title,
            starts_at=starts_at or timezone.now(),
        )

    return _create_event


@pytest.fixture()
def wishlist_access_factory(db):
    def _create_access(wishlist: WishList, profile: TelegramProfile):
        access, _ = WishListAccess.objects.get_or_create(
            wishlist=wishlist,
            profile=profile,
        )
        return access

    return _create_access


@pytest.fixture()
def gift_plan_factory(db):
    def _create_gift_plan(profile: TelegramProfile, title: str = "test",):
        return GiftPlan.objects.create(
            title=title,
            owner=profile,
            occurs_at=timezone.now(),
        )
    return _create_gift_plan


@pytest.fixture()
def gift_plan_item_factory(db):
    def _create_gift_plan_item(
        plan: GiftPlan,
        title: str = "test",
        url: str = "",
        wish: Wish | None = None,
    ):
        return GiftPlanItem.objects.create(
            plan=plan,
            title=title,
            url=url,
            wish=wish,
        )
    return _create_gift_plan_item
