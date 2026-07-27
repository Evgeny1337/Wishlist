from http import HTTPStatus

import pytest
from django.test import override_settings

from invites.tests.helpers import BOT_TOKEN_VERIFY, fresh_signed_init_data_user_id


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-at-least-32-bytes!!",
    JWT_ACCESS_TTL_SEC=3600,
    JWT_REFRESH_TTL_SEC=2592000,
)
@pytest.mark.django_db
def test_access_session_happy_path(
    api_client,
    profile,
):
    init_data = fresh_signed_init_data_user_id(1)
    response = api_client.post(
        '/api/telegram_webapp/session',
        payload={
            'init_data': init_data
        }
    )
    body = response.json()
    assert 'access_token' in body and body['access_token']
    assert 'refresh_token' in body and body['refresh_token']
    assert 'expires_in' in body and body['expires_in']
    assert 'refresh_expires_in' in body and body['refresh_expires_in']
    assert 'token_type' in body and body['token_type']
    assert response.status_code == HTTPStatus.OK


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_access_session_undefined_profile(
        api_client,
):
    init_data = fresh_signed_init_data_user_id(1)
    response = api_client.post(
        '/api/telegram_webapp/session',
        payload={
            'init_data': init_data
        }
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_access_session_invalid_init_data(
        api_client,
):
    response = api_client.post(
        '/api/telegram_webapp/session',
        payload={
            'init_data': 'test'
        }
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'Ошибка валидации init_data'
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@override_settings(TELEGRAM_BOT_TOKEN='')
@pytest.mark.django_db
def test_access_session_bot_token_not_found(
        api_client,
        profile,
):
    init_data = fresh_signed_init_data_user_id(1)
    response = api_client.post(
        '/api/telegram_webapp/session',
        payload={
            'init_data': init_data
        }
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'TELEGRAM_BOT_TOKEN не задан'
    assert response.status_code == 503


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="",
)
@pytest.mark.django_db
def test_access_session_jwt_secret_missing(
        api_client,
        profile,
):
    init_data = fresh_signed_init_data_user_id(1)
    response = api_client.post(
        '/api/telegram_webapp/session',
        payload={
            'init_data': init_data
        }
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == "JWT_SECRET не задан"
    assert response.status_code == 503
