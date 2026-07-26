import pytest
import json
from invites.models import TelegramProfile
from wishlists.models import WishList, Wish


@pytest.fixture
def wish_factory(db):
    def _create_wish(wishlist:WishList, url:str='https://test.ru', note:str='test', title:str='test',**kwargs):
        return Wish.objects.create(
            wishlist=wishlist,
            url=url,
            note=note,
            title=title,
            **kwargs
        )
    return _create_wish

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
                **kw,
            )
        def delete(self, url, headers=None, **kw):
            return client.delete(
                url,
                headers=headers or {},
                **kw,
            )
        def patch(self, url, payload, headers=None, **kw):
            return client.patch(
                url,
                data=json.dumps(payload),
                headers=headers or {},
                content_type="application/json",
                **kw,
            )
    return ApiClient()