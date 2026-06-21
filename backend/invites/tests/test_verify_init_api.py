import time
from urllib.parse import urlencode

import pytest
from django.test import override_settings

from invites.models import TelegramProfile

from .helpers import (
    BOT_TOKEN_VERIFY,
    fresh_signed_init_data,
    post_verify_init,
    signed_init_data,
)


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_verify_init_data_endpoint_success(client):
    assert not TelegramProfile.objects.filter(telegram_user_id=1).exists()
    raw = fresh_signed_init_data()
    resp = post_verify_init(client, raw)
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"ok": True, "telegram_user_id": 1}
    assert TelegramProfile.objects.filter(telegram_user_id=1).count() == 1


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_verify_init_data_endpoint_second_call_same_profile(client):
    raw = fresh_signed_init_data()
    first = post_verify_init(client, raw)
    assert first.status_code == 200
    second = post_verify_init(client, fresh_signed_init_data())
    assert second.status_code == 200
    assert first.json()["telegram_user_id"] == second.json()["telegram_user_id"] == 1
    assert TelegramProfile.objects.filter(telegram_user_id=1).count() == 1


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_verify_init_data_endpoint_invalid_user_payload_returns_422(client):
    now_ts = int(time.time())
    fields = {
        "user": "{}",
        "auth_date": str(now_ts - 3600),
        "query_id": "AA",
    }
    raw = signed_init_data(fields)
    resp = post_verify_init(client, raw)
    assert resp.status_code == 422


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=" ")
def test_verify_init_data_endpoint_blank_token_returns_503(client):
    raw = fresh_signed_init_data()
    resp = post_verify_init(client, raw)
    assert resp.status_code == 503


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_verify_init_data_endpoint_bad_signature_returns_422(client):
    now_ts = int(time.time())
    forged = urlencode(
        {"user": '{"id":1}', "auth_date": str(now_ts - 3600), "hash": "0" * 64}
    )
    resp = post_verify_init(client, forged)
    assert resp.status_code == 422


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_verify_init_data_endpoint_stale_auth_date_returns_422(client):
    stale_fields = {"user": '{"id":1}', "auth_date": "1000000000"}
    raw = signed_init_data(stale_fields)
    resp = post_verify_init(client, raw)
    assert resp.status_code == 422


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_verify_init_data_endpoint_missing_hash_returns_422(client):
    now_ts = int(time.time())
    raw = urlencode({"user": '{"id":1}', "auth_date": str(now_ts - 3600)})
    resp = post_verify_init(client, raw)
    assert resp.status_code == 422
