from http import HTTPStatus

import pytest
from django.test import override_settings

from invites.jwt_tokens import issue_token_pair
from invites.tests.helpers import (
    BOT_TOKEN_VERIFY,
    fresh_signed_init_data_user_id,
    delete_sub_in_token,
    overdue_exp_in_token,
)


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


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-at-least-32-bytes!!"
)
@pytest.mark.django_db
def test_refresh_session_happy_path(
        api_client,
        profile,
):
    refresh_payload = issue_token_pair(profile.telegram_user_id)
    refresh_token = refresh_payload.refresh_token
    response = api_client.post(
        '/api/telegram_webapp/refresh',
        payload={
            'refresh_token': refresh_token
        }
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body["access_token"] and body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]
    assert body["refresh_token"] != refresh_token
    assert body["token_type"] == "Bearer"


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-at-least-32-bytes!!"
)
@pytest.mark.django_db
def test_refresh_session_bad_token(
        api_client,
        profile,
):
    refresh_payload = "test-jwt-refresh"
    response = api_client.post(
        '/api/telegram_webapp/refresh',
        payload={
            'refresh_token': refresh_payload
        }
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'Ошибка JWT'
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-at-least-32-bytes!!"
)
@pytest.mark.django_db
def test_refresh_session_wrong_token(
        api_client,
        profile,
):
    refresh_payload = issue_token_pair(profile.telegram_user_id)
    access_token = refresh_payload.access_token
    response = api_client.post(
        '/api/telegram_webapp/refresh',
        payload={
            'refresh_token': access_token
        }
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'Неверный тип токена'
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-at-least-32-bytes!!"
)
@pytest.mark.django_db
def test_refresh_session_empty_sub(
        api_client,
        profile,
):
    refresh_payload = issue_token_pair(profile.telegram_user_id)
    refresh_token = refresh_payload.refresh_token
    bad_refresh_token = delete_sub_in_token(refresh_token)
    response = api_client.post(
        '/api/telegram_webapp/refresh',
        payload={
            'refresh_token': bad_refresh_token
        }
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'Отсутствуют данные пользователя'
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET=""
)
@pytest.mark.django_db
def test_refresh_session_jwt_secret_missing(
        api_client,
):
    response = api_client.post(
        '/api/telegram_webapp/refresh',
        payload={
            'refresh_token': ""
        }
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'JWT_SECRET не задан'
    assert response.status_code == 503


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-at-least-32-bytes!!"
)
@pytest.mark.django_db
def test_refresh_session_overdue_token(
        api_client,
        profile,
):
    refresh_payload = issue_token_pair(profile.telegram_user_id)
    refresh_token = refresh_payload.refresh_token
    overdue_refresh_token = overdue_exp_in_token(refresh_token)
    response = api_client.post(
        '/api/telegram_webapp/refresh',
        payload={
            'refresh_token': overdue_refresh_token
        }
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'Ошибка JWT'
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-at-least-32-bytes!!"
)
@pytest.mark.django_db
def test_refresh_session_wrong_profile(
        api_client,
        profile,
):
    refresh_payload = issue_token_pair(2)
    refresh_token = refresh_payload.refresh_token
    response = api_client.post(
        '/api/telegram_webapp/refresh',
        payload={
            'refresh_token': refresh_token
        }
    )
    assert 'detail' in response.json()
    assert response.status_code == HTTPStatus.NOT_FOUND

