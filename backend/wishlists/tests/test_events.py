from datetime import datetime, timedelta
from http import HTTPStatus

import pytest
from django.utils import timezone

from wishlists.models import Event


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@pytest.mark.django_db
def test_create_event_happy_path(
    api_client,
    profile,
    auth_headers,
    wishlist_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    date = timezone.now().isoformat()
    response = api_client.post(
        "/api/events/",
        headers=auth_headers(profile.telegram_user_id),
        payload={
            "title": "test",
            "wishlist": wishlist.id,
            "starts_at": date,
        },
    )
    body = response.json()
    assert body["title"] == "test"
    assert body["wishlist_id"] == wishlist.id
    assert abs((parse_dt(body["starts_at"]) - parse_dt(date)).total_seconds()) < 0.001
    assert response.status_code == HTTPStatus.CREATED


@pytest.mark.django_db
def test_create_event_wrong_wishlist(
    api_client,
    profile_factory,
    auth_headers,
    wishlist_factory,
):
    profile_1 = profile_factory(telegram_user_id=1)
    profile_2 = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=profile_2)
    response = api_client.post(
        "/api/events/",
        headers=auth_headers(profile_1.telegram_user_id),
        payload={
            "title": "test",
            "wishlist": wishlist.id,
            "starts_at": timezone.now().isoformat(),
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_create_event_wrong_bearer(
    api_client,
    profile,
    wishlist_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.post(
        "/api/events/",
        headers={"Authorization": f"Bearer {profile.telegram_user_id}"},
        payload={
            "title": "test",
            "wishlist": wishlist.id,
            "starts_at": timezone.now().isoformat(),
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_create_event_empty_title(
    api_client,
    profile,
    wishlist_factory,
    auth_headers,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.post(
        "/api/events/",
        headers=auth_headers(profile.telegram_user_id),
        payload={
            "title": "",
            "wishlist": wishlist.id,
            "starts_at": timezone.now().isoformat(),
        },
    )
    body = response.json()
    assert "detail" in body
    assert body["detail"][0]["type"] == "string_too_short"
    assert body["detail"][0]["loc"] == ["body", "payload", "title"]
    assert body["detail"][0]["msg"] == "String should have at least 1 character"
    assert body["detail"][0]["ctx"] == {"min_length": 1}
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_get_event_happy_path(
    api_client,
    profile,
    auth_headers,
    wishlist_factory,
    event_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    event = event_factory(wishlist=wishlist, owner=profile)
    response = api_client.get(
        f"/api/events/{event.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body["id"] == event.id
    assert body["title"] == event.title
    assert body["wishlist_id"] == wishlist.id
    assert abs((parse_dt(body["starts_at"]) - event.starts_at).total_seconds()) < 0.001
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_get_event_someone_else(
    api_client,
    profile_factory,
    wishlist_factory,
    event_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    event = event_factory(wishlist=wishlist, owner=owner)
    response = api_client.get(
        f"/api/events/{event.id}/",
        headers=auth_headers(2),
    )
    body = response.json()
    assert "detail" in body
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_get_event_wrong_id(api_client, profile, auth_headers):
    response = api_client.get(
        "/api/events/99999/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert "detail" in body
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_get_event_unauthorized(api_client, profile, wishlist_factory, event_factory):
    wishlist = wishlist_factory(telegram_profile=profile)
    event = event_factory(wishlist=wishlist, owner=profile)
    response = api_client.get(f"/api/events/{event.id}/", headers={})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_list_events_happy_path(
    api_client,
    profile,
    auth_headers,
    wishlist_factory,
    event_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    earlier = timezone.now()
    later = earlier + timedelta(days=1)
    event_factory(
        wishlist=wishlist,
        owner=profile,
        title="later",
        starts_at=later,
    )
    event_factory(
        wishlist=wishlist,
        owner=profile,
        title="earlier",
        starts_at=earlier,
    )
    response = api_client.get(
        "/api/events/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert len(body) == 2
    assert [item["title"] for item in body] == ["earlier", "later"]


@pytest.mark.django_db
def test_list_events_excludes_someone_else(
    api_client,
    profile_factory,
    wishlist_factory,
    event_factory,
    auth_headers,
):
    me = profile_factory(telegram_user_id=1)
    other = profile_factory(telegram_user_id=2)
    my_wishlist = wishlist_factory(telegram_profile=me)
    other_wishlist = wishlist_factory(telegram_profile=other)
    mine = event_factory(wishlist=my_wishlist, owner=me, title="mine")
    event_factory(wishlist=other_wishlist, owner=other, title="theirs")
    response = api_client.get(
        "/api/events/",
        headers=auth_headers(me.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert len(body) == 1
    assert body[0]["id"] == mine.id
    assert body[0]["title"] == "mine"


@pytest.mark.django_db
def test_list_events_empty(api_client, profile, auth_headers):
    response = api_client.get(
        "/api/events/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body == []
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_list_events_unauthorized(api_client):
    response = api_client.get("/api/events/", headers={})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_update_event_happy_path(
    api_client,
    profile,
    auth_headers,
    wishlist_factory,
    event_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    event = event_factory(wishlist=wishlist, owner=profile, title="old")
    new_starts_at = (timezone.now() + timedelta(days=2)).isoformat()
    response = api_client.patch(
        f"/api/events/{event.id}/",
        headers=auth_headers(profile.telegram_user_id),
        payload={"title": "new", "starts_at": new_starts_at},
    )
    body = response.json()
    assert body["title"] == "new"
    assert abs((parse_dt(body["starts_at"]) - parse_dt(new_starts_at)).total_seconds()) < 0.001
    assert response.status_code == HTTPStatus.OK
    event.refresh_from_db()
    assert event.title == "new"


@pytest.mark.django_db
def test_update_event_wrong_wishlist(
    api_client,
    profile_factory,
    wishlist_factory,
    event_factory,
    auth_headers,
):
    me = profile_factory(telegram_user_id=1)
    other = profile_factory(telegram_user_id=2)
    my_wishlist = wishlist_factory(telegram_profile=me)
    other_wishlist = wishlist_factory(telegram_profile=other)
    event = event_factory(wishlist=my_wishlist, owner=me)
    response = api_client.patch(
        f"/api/events/{event.id}/",
        headers=auth_headers(me.telegram_user_id),
        payload={"wishlist": other_wishlist.id},
    )
    body = response.json()
    assert "detail" in body
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_update_event_someone_else(
    api_client,
    profile_factory,
    wishlist_factory,
    event_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    event = event_factory(wishlist=wishlist, owner=owner, title="keep")
    response = api_client.patch(
        f"/api/events/{event.id}/",
        headers=auth_headers(2),
        payload={"title": "hacked"},
    )
    body = response.json()
    assert "detail" in body
    assert response.status_code == HTTPStatus.NOT_FOUND
    event.refresh_from_db()
    assert event.title == "keep"


@pytest.mark.django_db
def test_update_event_wrong_id(api_client, profile, auth_headers):
    response = api_client.patch(
        "/api/events/99999/",
        headers=auth_headers(profile.telegram_user_id),
        payload={"title": "nope"},
    )
    body = response.json()
    assert "detail" in body
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_update_event_unauthorized(
    api_client,
    profile,
    wishlist_factory,
    event_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    event = event_factory(wishlist=wishlist, owner=profile)
    response = api_client.patch(
        f"/api/events/{event.id}/",
        headers={},
        payload={"title": "nope"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
def test_delete_event_happy_path(
    api_client,
    profile,
    auth_headers,
    wishlist_factory,
    event_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    event = event_factory(wishlist=wishlist, owner=profile)
    event_id = event.id
    response = api_client.delete(
        f"/api/events/{event.id}/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert body["deleted_count"] == 1
    assert response.status_code == HTTPStatus.OK
    assert not Event.objects.filter(id=event_id).exists()


@pytest.mark.django_db
def test_delete_event_someone_else(
    api_client,
    profile_factory,
    wishlist_factory,
    event_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    event = event_factory(wishlist=wishlist, owner=owner)
    response = api_client.delete(
        f"/api/events/{event.id}/",
        headers=auth_headers(2),
    )
    body = response.json()
    assert "detail" in body
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Event.objects.filter(id=event.id).exists()


@pytest.mark.django_db
def test_delete_event_wrong_id(api_client, profile, auth_headers):
    response = api_client.delete(
        "/api/events/99999/",
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert "detail" in body
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_delete_event_unauthorized(
    api_client,
    profile,
    wishlist_factory,
    event_factory,
):
    wishlist = wishlist_factory(telegram_profile=profile)
    event = event_factory(wishlist=wishlist, owner=profile)
    response = api_client.delete(f"/api/events/{event.id}/", headers={})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert Event.objects.filter(id=event.id).exists()


@pytest.mark.django_db
def test_viewer_get_event_ok(
    api_client,
    profile_factory,
    wishlist_factory,
    event_factory,
    wishlist_access_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    viewer = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    event = event_factory(wishlist=wishlist, owner=owner, title="party")
    wishlist_access_factory(wishlist=wishlist, profile=viewer)
    response = api_client.get(
        f"/api/events/{event.id}/",
        headers=auth_headers(viewer.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body["id"] == event.id
    assert body["title"] == "party"
    assert body["wishlist_id"] == wishlist.id


@pytest.mark.django_db
def test_viewer_get_event_without_access_404(
    api_client,
    profile_factory,
    wishlist_factory,
    event_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    viewer = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    event = event_factory(wishlist=wishlist, owner=owner)
    response = api_client.get(
        f"/api/events/{event.id}/",
        headers=auth_headers(viewer.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "detail" in response.json()


@pytest.mark.django_db
def test_viewer_list_events_includes_shared(
    api_client,
    profile_factory,
    wishlist_factory,
    event_factory,
    wishlist_access_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    viewer = profile_factory(telegram_user_id=2)
    stranger = profile_factory(telegram_user_id=3)
    shared_wishlist = wishlist_factory(telegram_profile=owner, title="shared")
    private_wishlist = wishlist_factory(telegram_profile=stranger, title="private")
    shared_event = event_factory(
        wishlist=shared_wishlist,
        owner=owner,
        title="shared-event",
    )
    event_factory(
        wishlist=private_wishlist,
        owner=stranger,
        title="private-event",
    )
    own_wishlist = wishlist_factory(telegram_profile=viewer, title="mine")
    own_event = event_factory(
        wishlist=own_wishlist,
        owner=viewer,
        title="own-event",
    )
    wishlist_access_factory(wishlist=shared_wishlist, profile=viewer)
    response = api_client.get(
        "/api/events/",
        headers=auth_headers(viewer.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    ids = {item["id"] for item in body}
    assert ids == {shared_event.id, own_event.id}


@pytest.mark.django_db
def test_viewer_patch_event_404(
    api_client,
    profile_factory,
    wishlist_factory,
    event_factory,
    wishlist_access_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    viewer = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    event = event_factory(wishlist=wishlist, owner=owner, title="keep")
    wishlist_access_factory(wishlist=wishlist, profile=viewer)
    response = api_client.patch(
        f"/api/events/{event.id}/",
        headers=auth_headers(viewer.telegram_user_id),
        payload={"title": "hacked"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    event.refresh_from_db()
    assert event.title == "keep"


@pytest.mark.django_db
def test_viewer_delete_event_404(
    api_client,
    profile_factory,
    wishlist_factory,
    event_factory,
    wishlist_access_factory,
    auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    viewer = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=owner)
    event = event_factory(wishlist=wishlist, owner=owner)
    wishlist_access_factory(wishlist=wishlist, profile=viewer)
    response = api_client.delete(
        f"/api/events/{event.id}/",
        headers=auth_headers(viewer.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Event.objects.filter(id=event.id).exists()
