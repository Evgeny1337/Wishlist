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