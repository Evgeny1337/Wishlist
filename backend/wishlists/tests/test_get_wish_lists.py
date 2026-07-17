import json
from http import HTTPStatus

from django.test import override_settings

from invites.models import TelegramProfile
from unittest.mock import patch
import pytest

from invites.tests.helpers import BOT_TOKEN_VERIFY, fresh_signed_init_data_user_id
from wishlists.models import WishList


@pytest.fixture()
def profile(db):
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
def test_wishlist_create_empty_init_data(api_client):
    response = api_client.post('/api/wishlists/', payload={'init_data':'', 'title':'test'})
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'пустой initData'
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_wishlist_create_invalid_init_data(api_client):
    response = api_client.post(
        "/api/wishlists/",
        payload={"init_data": "test", "title": "test"},
    )
    assert response.status_code == 422


@pytest.mark.django_db
def test_wishlist_create_empty_title(api_client, profile):
    with patch('wishlists.api.get_profile') as mock_get_profile:
        mock_get_profile.return_value = profile
        response = api_client.post('/api/wishlists/', payload={'init_data':'', 'title':''})
        body = response.json()
        assert 'detail' in body
        assert body['detail'][0]['type'] == 'string_too_short'
        assert body['detail'][0]['ctx'] == {'min_length': 1}
        assert body['detail'][0]['msg'] == 'String should have at least 1 character'
        assert body['detail'][0]['loc'] == ['body', 'data', 'title']
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_wishlist_create_unknown_user(api_client):
    init_data = fresh_signed_init_data_user_id(99999)
    response = api_client.post('/api/wishlists/', payload={'init_data':init_data, 'title':'test'})
    assert response.status_code == HTTPStatus.NOT_FOUND


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_wishlist_create_not_valid_data(client):
    response = client.post('/api/wishlists/', data='test', content_type='application/json')
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'Cannot parse request body'
    assert response.status_code == HTTPStatus.BAD_REQUEST


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_wishlist_create_happy_path(api_client, profile):
    init_data = fresh_signed_init_data_user_id(1)
    response = api_client.post('/api/wishlists/', payload={'init_data':init_data,'title':'test'})
    assert response.status_code == HTTPStatus.CREATED
    assert WishList.objects.filter(owner=profile, title="test").exists()

