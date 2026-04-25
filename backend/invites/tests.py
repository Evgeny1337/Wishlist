import datetime
import hashlib
import hmac
import json

import pytest
from django.test import Client
from django.utils import timezone

from invites.models import Invite, InviteActivation, TelegramProfile
from invites.telegram_init_data import (
    build_data_check_string,
    init_data_secret_key,
    is_auth_date_fresh,
    is_valid_init_data_hash,
    parse_init_data_pairs,
)

client = Client()


def _tg(telegram_user_id: int, **kwargs) -> dict:
    return {
        "telegram_user_id": telegram_user_id,
        "username": kwargs.get("username", "user"),
        "first_name": kwargs.get("first_name", "User"),
        "last_name": kwargs.get("last_name", "Test"),
    }


def _post_activate(token: str, telegram_user_id: int, **kwargs):
    payload = {"token": token, "telegram_user": _tg(telegram_user_id, **kwargs)}
    return client.post(
        "/api/invites/activate",
        data=json.dumps(payload),
        content_type="application/json",
    )


@pytest.mark.django_db
def test_activate_success_with_existing_profile():
    invite = Invite.objects.create(
        token="ok-existing-profile",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    profile = TelegramProfile.objects.create(
        telegram_user_id=5001,
        username="u5001",
        first_name="U",
        last_name="One",
    )
    response = _post_activate(
        invite.token,
        profile.telegram_user_id,
        username=profile.username,
        first_name=profile.first_name,
        last_name=profile.last_name,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["used_count"] == 1
    assert data["token"] == invite.token

    invite.refresh_from_db()
    assert invite.used_count == 1
    assert InviteActivation.objects.filter(invite=invite, telegram_profile=profile).count() == 1


@pytest.mark.django_db
def test_activate_success_creates_telegram_profile():
    invite = Invite.objects.create(
        token="ok-new-profile",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    tg_id = 5002
    assert not TelegramProfile.objects.filter(telegram_user_id=tg_id).exists()

    response = _post_activate(invite.token, tg_id, username="new", first_name="New", last_name="User")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["used_count"] == 1

    invite.refresh_from_db()
    assert invite.used_count == 1
    profile = TelegramProfile.objects.get(telegram_user_id=tg_id)
    assert InviteActivation.objects.filter(invite=invite, telegram_profile=profile).count() == 1


@pytest.mark.django_db
def test_activate_not_found_returns_404():
    tg_id = 5003
    assert TelegramProfile.objects.filter(telegram_user_id=tg_id).count() == 0
    response = _post_activate("missing-token-404", tg_id)
    assert response.status_code == 404
    assert TelegramProfile.objects.filter(telegram_user_id=tg_id).count() == 0


@pytest.mark.django_db
def test_activate_invite_limit_exceeded_returns_403():
    invite = Invite.objects.create(
        token="limit-403",
        max_uses=1,
        used_count=1,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    tg_id = 5004
    response = _post_activate(invite.token, tg_id)
    assert response.status_code == 403
    invite.refresh_from_db()
    assert invite.used_count == 1
    assert not InviteActivation.objects.filter(invite=invite, telegram_profile__telegram_user_id=tg_id).exists()


@pytest.mark.django_db
def test_activate_invite_expired_returns_403():
    invite = Invite.objects.create(
        token="expired-403",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() - datetime.timedelta(hours=1),
    )
    tg_id = 5005
    response = _post_activate(invite.token, tg_id)
    assert response.status_code == 403
    invite.refresh_from_db()
    assert invite.used_count == 0
    assert not InviteActivation.objects.filter(invite=invite, telegram_profile__telegram_user_id=tg_id).exists()


@pytest.mark.django_db
def test_activate_invite_inactive_returns_403():
    invite = Invite.objects.create(
        token="inactive-403",
        max_uses=1,
        used_count=0,
        is_active=False,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    tg_id = 5006
    response = _post_activate(invite.token, tg_id)
    assert response.status_code == 403
    invite.refresh_from_db()
    assert invite.used_count == 0
    assert not InviteActivation.objects.filter(invite=invite, telegram_profile__telegram_user_id=tg_id).exists()


@pytest.mark.django_db
def test_activate_duplicate_user_returns_409():
    invite = Invite.objects.create(
        token="dup-409",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    tg_id = 5007
    first = _post_activate(invite.token, tg_id)
    assert first.status_code == 200

    invite.refresh_from_db()
    assert invite.used_count == 1

    second = _post_activate(invite.token, tg_id)
    assert second.status_code == 409

    invite.refresh_from_db()
    assert invite.used_count == 1
    profile = TelegramProfile.objects.get(telegram_user_id=tg_id)
    assert InviteActivation.objects.filter(invite=invite, telegram_profile=profile).count() == 1


def test_parse_init_data_pairs_decodes_percent_encoding():
    test_str = "user=%7B%22id%22%3A1%7D&a=1&b=2&hash=abc"
    assert parse_init_data_pairs(test_str) == {
        "user": '{"id":1}',
        "a": "1",
        "b": "2",
        "hash": "abc",
    }


def test_build_data_check_string_matches_telegram_rules():
    # Ключи не в алфавитном порядке в dict; hash исключается; эталон — как в доке (\\n между парами).
    pairs = {
        "user": '{"id":1}',
        "auth_date": "1672531200",
        "query_id": "AA",
        "hash": "ignored",
    }
    expected = 'auth_date=1672531200\nquery_id=AA\nuser={"id":1}'
    assert build_data_check_string(pairs) == expected

def test_init_data_secret_key_matches_telegram_formula():
    bot_token = "123456:ABCDEF"
    expected_hex = "b85c5dcb6eee1e844daed3e80fb928a3e86d719ccd96a3f410a29360ba5ba60b"

    assert init_data_secret_key(bot_token).hex() == expected_hex

def test_valid_init_data_hash():
    test_str = "user=%7B%22id%22%3A1%7D&a=1&b=2&hash='abc'"
    pairs = parse_init_data_pairs(test_str)
    secret_key = init_data_secret_key(bot_token="123456:ABCDEF")
    data_check_string = build_data_check_string(pairs)
    received_hash = hmac.new(secret_key,data_check_string.encode('utf-8'),hashlib.sha256).hexdigest()
    assert is_valid_init_data_hash(data_check_string, received_hash, secret_key)


def test_invalid_init_data_hash():
    test_str = "user=%7B%22id%22%3A1%7D&a=1&b=2&hash='abc'"
    pairs = parse_init_data_pairs(test_str)
    secret_key = init_data_secret_key(bot_token="123456:ABCDEF")
    secret_bad_key = init_data_secret_key(bot_token='123457:ABCDEF')
    data_check_string = build_data_check_string(pairs)
    bad_hash = hmac.new(secret_bad_key,data_check_string.encode('utf-8'),hashlib.sha256).hexdigest()
    assert not is_valid_init_data_hash(data_check_string, bad_hash, secret_key)


def test_is_auth_date_fresh_within_window():
    now_ts = 1_700_000_000
    auth_ts = now_ts - 3600
    assert is_auth_date_fresh(str(auth_ts), max_age_seconds=86400, now_ts=now_ts)


def test_is_auth_date_fresh_too_old():
    now_ts = 1_700_000_000
    auth_ts = now_ts - 100_000
    assert not is_auth_date_fresh(str(auth_ts), max_age_seconds=86400, now_ts=now_ts)


def test_is_auth_date_fresh_in_future_rejected():
    now_ts = 1_700_000_000
    auth_ts = now_ts + 10
    assert not is_auth_date_fresh(str(auth_ts), max_age_seconds=86400, now_ts=now_ts)


def test_is_auth_date_fresh_invalid_string():
    assert not is_auth_date_fresh("not-a-number", max_age_seconds=86400, now_ts=1_700_000_000)

