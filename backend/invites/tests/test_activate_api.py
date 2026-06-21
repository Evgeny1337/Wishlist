import datetime
import pytest
from django.utils import timezone

from invites.models import Invite, InviteActivation, TelegramProfile

from .helpers import post_activate


@pytest.mark.django_db
def test_activate_success_with_existing_profile(client):
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
    response = post_activate(
        client,
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
def test_activate_success_creates_telegram_profile(client):
    invite = Invite.objects.create(
        token="ok-new-profile",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    tg_id = 5002
    assert not TelegramProfile.objects.filter(telegram_user_id=tg_id).exists()

    response = post_activate(
        client, invite.token, tg_id, username="new", first_name="New", last_name="User"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["used_count"] == 1

    invite.refresh_from_db()
    assert invite.used_count == 1
    profile = TelegramProfile.objects.get(telegram_user_id=tg_id)
    assert InviteActivation.objects.filter(invite=invite, telegram_profile=profile).count() == 1


@pytest.mark.django_db
def test_activate_not_found_returns_404(client):
    tg_id = 5003
    assert TelegramProfile.objects.filter(telegram_user_id=tg_id).count() == 0
    response = post_activate(client, "missing-token-404", tg_id)
    assert response.status_code == 404
    assert TelegramProfile.objects.filter(telegram_user_id=tg_id).count() == 0


@pytest.mark.django_db
def test_activate_invite_limit_exceeded_returns_403(client):
    invite = Invite.objects.create(
        token="limit-403",
        max_uses=1,
        used_count=1,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    tg_id = 5004
    response = post_activate(client, invite.token, tg_id)
    assert response.status_code == 403
    invite.refresh_from_db()
    assert invite.used_count == 1
    assert not InviteActivation.objects.filter(
        invite=invite, telegram_profile__telegram_user_id=tg_id
    ).exists()


@pytest.mark.django_db
def test_activate_invite_expired_returns_403(client):
    invite = Invite.objects.create(
        token="expired-403",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() - datetime.timedelta(hours=1),
    )
    tg_id = 5005
    response = post_activate(client, invite.token, tg_id)
    assert response.status_code == 403
    invite.refresh_from_db()
    assert invite.used_count == 0
    assert not InviteActivation.objects.filter(
        invite=invite, telegram_profile__telegram_user_id=tg_id
    ).exists()


@pytest.mark.django_db
def test_activate_invite_inactive_returns_403(client):
    invite = Invite.objects.create(
        token="inactive-403",
        max_uses=1,
        used_count=0,
        is_active=False,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    tg_id = 5006
    response = post_activate(client, invite.token, tg_id)
    assert response.status_code == 403
    invite.refresh_from_db()
    assert invite.used_count == 0
    assert not InviteActivation.objects.filter(
        invite=invite, telegram_profile__telegram_user_id=tg_id
    ).exists()


@pytest.mark.django_db
def test_activate_same_user_second_time_idempotent_returns_200(client):
    """Постоянный вход по одной ссылке: повтор активации тот же 200 и тот же used_count."""
    invite = Invite.objects.create(
        token="dup-idempotent",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
    )
    tg_id = 5007
    first = post_activate(client, invite.token, tg_id)
    assert first.status_code == 200

    invite.refresh_from_db()
    assert invite.used_count == 1

    second = post_activate(client, invite.token, tg_id)
    assert second.status_code == 200
    body = second.json()
    assert body["ok"] is True
    assert body["used_count"] == 1

    invite.refresh_from_db()
    assert invite.used_count == 1
    profile = TelegramProfile.objects.get(telegram_user_id=tg_id)
    assert InviteActivation.objects.filter(invite=invite, telegram_profile=profile).count() == 1


@pytest.mark.django_db
def test_activate_personal_invite_wrong_telegram_user_returns_403(client):
    invite = Invite.objects.create(
        token="personal-wrong-user",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
        for_telegram_user_id=9999,
    )
    response = post_activate(client, invite.token, 5008)
    assert response.status_code == 403
    invite.refresh_from_db()
    assert invite.used_count == 0
    assert not InviteActivation.objects.filter(invite=invite).exists()


@pytest.mark.django_db
def test_activate_personal_invite_matching_user_ok(client):
    tg_id = 9999
    invite = Invite.objects.create(
        token="personal-ok",
        max_uses=1,
        used_count=0,
        is_active=True,
        expires_at=timezone.now() + datetime.timedelta(days=1),
        for_telegram_user_id=tg_id,
    )
    response = post_activate(client, invite.token, tg_id)
    assert response.status_code == 200
    invite.refresh_from_db()
    assert invite.used_count == 1
