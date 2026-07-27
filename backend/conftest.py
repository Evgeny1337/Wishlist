import json

import pytest

from invites.models import TelegramProfile


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