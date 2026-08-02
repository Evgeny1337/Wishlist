import pytest

from invites.jwt_tokens import issue_token_pair
from invites.models import TelegramProfile
from wishlists.models import WishList, Wish


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
