import pytest
import json
from invites.models import TelegramProfile
from wishlists.models import WishList


@pytest.fixture()
def wishlist_factory(db):
    def _create_wishlist(telegram_profile: TelegramProfile, title:str = 'test', **kwargs):
        return WishList.objects.create(
            owner=telegram_profile,
            title=title,
            **kwargs
        )
    return _create_wishlist

@pytest.fixture
def profile_factory(db):
    def _create(telegram_user_id:int = 1, **kwargs):
        return TelegramProfile.objects.create(
            telegram_user_id=telegram_user_id,
            **kwargs
        )
    return _create


@pytest.fixture()
def profile(profile_factory):
    return profile_factory()


@pytest.fixture
def api_client(client):
    class ApiClient:
        def post(self, url, payload, **kw):
            return client.post(
                url,
                data=json.dumps(payload),
                content_type="application/json",
                **kw,
            )
        def get(self, url, headers=None, **kw):
            return client.get(
                url,
                headers=headers or {},
                **kw
            )
        def delete(self, url, headers=None, **kw):
            return client.delete(
                url,
                headers=headers or {},
                **kw
            )
    return ApiClient()