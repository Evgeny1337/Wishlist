from datetime import datetime
from http import HTTPStatus

import pytest
from django.utils import timezone

from wishlists.models import Reminder


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@pytest.mark.django_db
def test_reminder_create_happy_path(
    api_client,
    profile,
    auth_headers,
    wishlist_factory,
    event_factory,
):
    wishlist = wishlist_factory(profile)
    event = event_factory(wishlist=wishlist, owner=profile)
    response = api_client.post(
        "/api/reminders/",
        payload={
            "event_id": event.id,
            "title": "test",
            "remind_at": timezone.now().isoformat(),
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.CREATED


@pytest.mark.django_db
def test_reminder_create_without_event(
    api_client,
    profile,
    auth_headers,
):
    response = api_client.post(
        "/api/reminders/",
        payload={
            "title": "free",
            "remind_at": timezone.now().isoformat(),
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()["event"] is None


@pytest.mark.django_db
def test_reminder_create_someone_else_event(
    api_client,
    profile_factory,
    auth_headers,
    wishlist_factory,
    event_factory,
):
    owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(owner)
    event = event_factory(wishlist=wishlist, owner=owner)
    response = api_client.post(
        "/api/reminders/",
        payload={
            "event_id": event.id,
            "title": "test",
            "remind_at": timezone.now().isoformat(),
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_reminder_create_bad_payload(
    api_client,
    profile,
    auth_headers,
):
    response = api_client.post(
        "/api/reminders/",
        payload={
            "event_id": "test",
            "title": "test",
            "remind_at": timezone.now().isoformat(),
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_reminder_get_happy_path(
    api_client,
    profile,
    auth_headers,
    wishlist_factory,
    event_factory,
    reminder_factory,
):
    wishlist = wishlist_factory(profile)
    event = event_factory(wishlist=wishlist, owner=profile)
    reminder = reminder_factory(event=event, owner=profile)
    response = api_client.get(
        f"/api/reminders/{reminder.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body["event"] == event.id
    assert body["title"] == reminder.title
    assert abs((parse_dt(body["remind_at"]) - reminder.remind_at).total_seconds()) < 0.001
    assert body["id"] == reminder.id
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_reminder_get_someone_else_reminder(
    api_client,
    profile_factory,
    auth_headers,
    wishlist_factory,
    event_factory,
    reminder_factory,
):
    owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(owner)
    event = event_factory(wishlist=wishlist, owner=owner)
    reminder = reminder_factory(event=event, owner=owner)
    response = api_client.get(
        f"/api/reminders/{reminder.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_reminder_list_happy_path(
    api_client,
    profile,
    auth_headers,
    wishlist_factory,
    event_factory,
    reminder_factory,
):
    wishlist_1 = wishlist_factory(profile)
    wishlist_2 = wishlist_factory(profile)
    event_1 = event_factory(wishlist=wishlist_1, owner=profile)
    event_2 = event_factory(wishlist=wishlist_2, owner=profile)
    reminder_factory(event=event_1, owner=profile)
    reminder_factory(event=event_2, owner=profile)
    response = api_client.get(
        "/api/reminders/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert len(body) == 2
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_reminder_list_empty(
    api_client,
    profile,
    auth_headers,
):
    response = api_client.get(
        "/api/reminders/",
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


@pytest.mark.django_db
def test_reminder_patch_happy_path(
    api_client,
    profile,
    auth_headers,
    wishlist_factory,
    event_factory,
    reminder_factory,
):
    wishlist = wishlist_factory(profile)
    event = event_factory(wishlist=wishlist, owner=profile)
    reminder = reminder_factory(event=event, owner=profile)
    response = api_client.patch(
        f"/api/reminders/{reminder.id}/",
        payload={"title": "kek"},
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body["title"] == "kek"
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_reminder_patch_empty_body(
    api_client,
    profile,
    auth_headers,
    wishlist_factory,
    event_factory,
    reminder_factory,
):
    wishlist = wishlist_factory(profile)
    event = event_factory(wishlist=wishlist, owner=profile)
    reminder = reminder_factory(event=event, owner=profile)
    response = api_client.patch(
        f"/api/reminders/{reminder.id}/",
        payload={},
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_reminder_patch_someone_else_reminder(
    api_client,
    profile_factory,
    auth_headers,
    wishlist_factory,
    event_factory,
    reminder_factory,
):
    owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(owner)
    event = event_factory(wishlist=wishlist, owner=owner)
    reminder = reminder_factory(event=event, owner=owner)
    response = api_client.patch(
        f"/api/reminders/{reminder.id}/",
        payload={"title": "kek"},
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_reminder_delete_happy_path(
    api_client,
    profile,
    auth_headers,
    wishlist_factory,
    event_factory,
    reminder_factory,
):
    wishlist = wishlist_factory(profile)
    event = event_factory(wishlist=wishlist, owner=profile)
    reminder = reminder_factory(event=event, owner=profile)
    response = api_client.delete(
        f"/api/reminders/{reminder.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    assert not Reminder.objects.filter(pk=reminder.id).exists()
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_reminder_delete_someone_else_reminder(
    api_client,
    profile_factory,
    auth_headers,
    wishlist_factory,
    event_factory,
    reminder_factory,
):
    owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(owner)
    event = event_factory(wishlist=wishlist, owner=owner)
    reminder = reminder_factory(event=event, owner=owner)
    response = api_client.delete(
        f"/api/reminders/{reminder.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_reminder_without_auth(api_client):
    response = api_client.get("/api/reminders/", headers={})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
