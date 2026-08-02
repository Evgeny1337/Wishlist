from http import HTTPStatus

import pytest
from django.test import override_settings

from invites.jwt_tokens import issue_token_pair
from invites.tests.helpers import BOT_TOKEN_VERIFY, overdue_exp_in_token


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-for-activate-via-webapp",
    JWT_ACCESS_TTL_SEC=3600,
    JWT_REFRESH_TTL_SEC=2592000,
)
@pytest.mark.django_db
def test_get_me_happy_path(
        api_client,
        profile,
):
    payload_token = issue_token_pair(profile.telegram_user_id)
    response = api_client.get(
        '/api/telegram_webapp/me',
        headers={
            'Authorization': f'Bearer {payload_token.access_token}',
        }
    )
    assert response.json() == {"telegram_user_id": profile.telegram_user_id}
    assert response.status_code == HTTPStatus.OK


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-for-activate-via-webapp",
    JWT_ACCESS_TTL_SEC=3600,
    JWT_REFRESH_TTL_SEC=2592000,
)
@pytest.mark.django_db
def test_get_me_no_profile(
        api_client,
):
    payload_token = issue_token_pair(2)
    response = api_client.get(
        '/api/telegram_webapp/me',
        headers={
            'Authorization': f'Bearer {payload_token.access_token}',
        }
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-for-activate-via-webapp",
    JWT_ACCESS_TTL_SEC=3600,
    JWT_REFRESH_TTL_SEC=2592000,
)
@pytest.mark.django_db
def test_get_me_overdue_token(
        api_client,
        profile,
):
    payload_token = issue_token_pair(profile.telegram_user_id)
    access_token = payload_token.access_token
    overdue_access_token = overdue_exp_in_token(access_token)
    response = api_client.get(
        '/api/telegram_webapp/me',
        headers={
            'Authorization': f'Bearer {overdue_access_token}',
        }
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-for-activate-via-webapp",
    JWT_ACCESS_TTL_SEC=3600,
    JWT_REFRESH_TTL_SEC=2592000,
)
@pytest.mark.django_db
def test_get_me_unauthorized(
        api_client,
):
    response = api_client.get(
        '/api/telegram_webapp/me',
        headers={}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-for-activate-via-webapp",
    JWT_ACCESS_TTL_SEC=3600,
    JWT_REFRESH_TTL_SEC=2592000,
)
@pytest.mark.django_db
def test_get_me_bad_bearer(
        api_client,
):
    bad_bearer_token = 'test-wrong-bearer'
    response = api_client.get(
        '/api/telegram_webapp/me',
        headers={
            'Authorization': f'Bearer {bad_bearer_token}',
        }
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-for-activate-via-webapp",
    JWT_ACCESS_TTL_SEC=3600,
    JWT_REFRESH_TTL_SEC=2592000,
)
@pytest.mark.django_db
def test_get_me_different_token(
        api_client,
        profile,
):
    payload_token = issue_token_pair(profile.telegram_user_id)
    refresh_token = payload_token.refresh_token
    response = api_client.get(
        '/api/telegram_webapp/me',
        headers={
            'Authorization': f'Bearer {refresh_token}',
        }
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

