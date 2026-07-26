import datetime
import time
from urllib.parse import urlencode

import pytest
from django.test import override_settings
from django.utils import timezone

from invites.models import Invite, InviteActivation, TelegramProfile

from .helpers import (
    BOT_TOKEN_VERIFY,
    fresh_signed_init_data,
    fresh_signed_init_data_user_id,
    post_activate_invite_via_webapp,
    signed_init_data,
)


@pytest.mark.django_db
@override_settings(
    TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY,
    JWT_SECRET="test-jwt-secret-for-activate-via-webapp",
    JWT_ACCESS_TTL_SEC=3600,
    JWT_REFRESH_TTL_SEC=2592000,
)
def test_activate_via_webapp_success(client):
    """init_data задаёт telegram_user_id=1 — см. fresh_signed_init_data / helpers."""
    invite = Invite.objects.create(
        token="wa-activate-ok",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    assert not TelegramProfile.objects.filter(telegram_user_id=1).exists()

    raw = fresh_signed_init_data()
    resp = post_activate_invite_via_webapp(client, raw, invite.token)

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["used_count"] == 1
    assert data["token"] == invite.token
    assert data["telegram_user_id"] == 1
    tokens = data["tokens"]
    assert tokens["token_type"] == "Bearer"
    assert tokens["expires_in"] == 3600
    assert tokens["refresh_expires_in"] == 2592000
    assert isinstance(tokens["access_token"], str) and tokens["access_token"]
    assert isinstance(tokens["refresh_token"], str) and tokens["refresh_token"]
    assert tokens["access_token"] != tokens["refresh_token"]
    invite.refresh_from_db()
    assert invite.used_count == 1
    profile = TelegramProfile.objects.get(telegram_user_id=1)
    assert InviteActivation.objects.filter(invite=invite, telegram_profile=profile).count() == 1


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_activate_via_webapp_same_user_twice_idempotent_returns_200(client):
    invite = Invite.objects.create(
        token="wa-dup-idempotent",
        max_uses=2,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    raw = fresh_signed_init_data()
    assert post_activate_invite_via_webapp(client, raw, invite.token).status_code == 200
    second = post_activate_invite_via_webapp(client, fresh_signed_init_data(), invite.token)
    assert second.status_code == 200
    assert second.json()["used_count"] == 1
    invite.refresh_from_db()
    assert invite.used_count == 1


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_activate_via_webapp_personal_invite_wrong_user_returns_403(client):
    invite = Invite.objects.create(
        token="wa-personal-wrong",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
        for_telegram_user_id=999,
    )
    raw = fresh_signed_init_data()
    resp = post_activate_invite_via_webapp(client, raw, invite.token)
    assert resp.status_code == 403
    invite.refresh_from_db()
    assert invite.used_count == 0
    assert InviteActivation.objects.filter(invite=invite).count() == 0
    assert not TelegramProfile.objects.filter(telegram_user_id=1).exists()


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_activate_via_webapp_personal_invite_matching_user_ok(client):
    invite = Invite.objects.create(
        token="wa-personal-ok",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
        for_telegram_user_id=42,
    )
    raw = fresh_signed_init_data_user_id(42)
    resp = post_activate_invite_via_webapp(client, raw, invite.token)
    assert resp.status_code == 200
    assert resp.json()["telegram_user_id"] == 42
    invite.refresh_from_db()
    assert invite.used_count == 1


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_activate_via_webapp_two_users_under_max_uses(client):
    """Общий инвайт: два разных пользователя, max_uses=2."""
    invite = Invite.objects.create(
        token="wa-two-users",
        max_uses=2,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    r1 = post_activate_invite_via_webapp(
        client, fresh_signed_init_data_user_id(7001), invite.token
    )
    assert r1.status_code == 200
    assert r1.json()["used_count"] == 1

    r2 = post_activate_invite_via_webapp(
        client, fresh_signed_init_data_user_id(7002), invite.token
    )
    assert r2.status_code == 200
    assert r2.json()["used_count"] == 2

    r3 = post_activate_invite_via_webapp(
        client, fresh_signed_init_data_user_id(7003), invite.token
    )
    assert r3.status_code == 403
    invite.refresh_from_db()
    assert invite.used_count == 2


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_activate_via_webapp_invite_not_found_returns_404(client):
    raw = fresh_signed_init_data()
    resp = post_activate_invite_via_webapp(client, raw, "missing-invite-token")
    assert resp.status_code == 404
    assert not TelegramProfile.objects.filter(telegram_user_id=1).exists()


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_activate_via_webapp_limit_exceeded_returns_403(client):
    invite = Invite.objects.create(
        token="wa-limit-403",
        max_uses=1,
        used_count=1,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    raw = fresh_signed_init_data()
    resp = post_activate_invite_via_webapp(client, raw, invite.token)
    assert resp.status_code == 403
    invite.refresh_from_db()
    assert invite.used_count == 1
    assert not InviteActivation.objects.filter(invite=invite).exists()


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_activate_via_webapp_invite_expired_returns_403(client):
    invite = Invite.objects.create(
        token="wa-expired-403",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() - datetime.timedelta(hours=1),
    )
    resp = post_activate_invite_via_webapp(client, fresh_signed_init_data(), invite.token)
    assert resp.status_code == 403
    assert InviteActivation.objects.filter(invite=invite).count() == 0


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_activate_via_webapp_invite_inactive_returns_403(client):
    invite = Invite.objects.create(
        token="wa-inactive-403",
        max_uses=1,
        used_count=0,
        is_active=False,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    resp = post_activate_invite_via_webapp(client, fresh_signed_init_data(), invite.token)
    assert resp.status_code == 403


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_activate_via_webapp_invalid_signature_returns_422(client):
    invite = Invite.objects.create(
        token="wa-bad-hash",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    now_ts = int(time.time())
    forged = urlencode(
        {"user": '{"id":1}', "auth_date": str(now_ts - 3600), "hash": "0" * 64}
    )
    resp = post_activate_invite_via_webapp(client, forged, invite.token)
    assert resp.status_code == 422


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
def test_activate_via_webapp_stale_auth_returns_422(client):
    invite = Invite.objects.create(
        token="wa-stale-auth",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    raw = signed_init_data({"user": '{"id":1}', "auth_date": "1000000000"})
    resp = post_activate_invite_via_webapp(client, raw, invite.token)
    assert resp.status_code == 422


@pytest.mark.django_db
@override_settings(TELEGRAM_BOT_TOKEN=" ")
def test_activate_via_webapp_blank_bot_token_returns_503(client):
    invite = Invite.objects.create(
        token="wa-no-bot-token",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    resp = post_activate_invite_via_webapp(client, fresh_signed_init_data(), invite.token)
    assert resp.status_code == 503
