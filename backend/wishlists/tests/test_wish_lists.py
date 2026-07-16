import json
from http import HTTPStatus
from invites.models import TelegramProfile
from unittest.mock import patch
import pytest
import pdb

@pytest.fixture()
def profile():
    return TelegramProfile.objects.create(telegram_user_id=1,)


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
    return ApiClient()


@pytest.mark.django_db
def test_wishlist_create_not_valid_data(client):
    response = client.post('/api/wishlists/', payload='test')
    assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
def test_wishlist_create_empty_data(api_client):
    response = api_client.post('/api/wishlists/', payload={})
    body = response.json()
    assert 'detail' in body
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_wishlist_create_success(api_client, profile):
    with patch('wishlists.api.get_profile') as mock_get_profile:
        mock_get_profile.return_value = profile
        response = api_client.post('/api/wishlists/', payload={'init_data':'test','title':'test'})
    assert response.status_code == HTTPStatus.CREATED

