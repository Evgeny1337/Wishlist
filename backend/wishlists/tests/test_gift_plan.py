from datetime import datetime
from http import HTTPStatus

import pytest
from django.utils import timezone

from wishlists.models import GiftPlan, GiftPlanItem


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@pytest.mark.django_db
def test_gift_plan_create_happy_path(
        api_client,
        profile,
        auth_headers,
):
    occurs_at = timezone.now().isoformat()
    response = api_client.post(
        '/api/gifts/plan/',
        payload={
            'title': 'test',
            'occurs_at': occurs_at,
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.CREATED
    assert body['title'] == 'test'
    assert 'id' in body
    assert abs((parse_dt(body['occurs_at']) - parse_dt(occurs_at)).total_seconds()) < 0.001
    assert GiftPlan.objects.filter(id=body['id'], owner=profile).exists()


@pytest.mark.django_db
def test_create_gift_plan_item_happy_path_with_wish(
        api_client,
        profile_factory,
        auth_headers,
        gift_plan_factory,
        wishlist_factory,
        wishlist_access_factory,
        wish_factory,
):
    wishlist_owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)

    gift_plan = gift_plan_factory(profile)

    wishlist = wishlist_factory(wishlist_owner)
    wishlist_access_factory(wishlist, profile)

    wish = wish_factory(wishlist)

    response = api_client.post(
        f'/api/gifts/plan/{gift_plan.id}/item/',
        payload={
            'wish': wish.id,
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.CREATED
    assert body['title'] == wish.title
    assert body['url'] == wish.url
    assert body['wish'] == wish.id
    assert GiftPlanItem.objects.filter(
        id=body['id'],
        plan=gift_plan,
        wish=wish,
    ).exists()


@pytest.mark.django_db
def test_create_gift_plan_item_own_wish(
        api_client,
        profile,
        auth_headers,
        gift_plan_factory,
        wishlist_factory,
        wish_factory,
):
    gift_plan = gift_plan_factory(profile)
    wishlist = wishlist_factory(profile)
    wish = wish_factory(wishlist, title="own-wish", url="https://own.ru")

    response = api_client.post(
        f'/api/gifts/plan/{gift_plan.id}/item/',
        payload={'wish': wish.id},
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.CREATED
    assert body['title'] == 'own-wish'
    assert body['url'] == 'https://own.ru'
    assert body['wish'] == wish.id


@pytest.mark.django_db
def test_create_gift_plan_item_happy_path_with_title(
        api_client,
        profile,
        auth_headers,
        gift_plan_factory,
):
    gift_plan = gift_plan_factory(profile)
    response = api_client.post(
        f'/api/gifts/plan/{gift_plan.id}/item/',
        payload={
            'title': 'test',
            'url': 'https://test.ru',
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.CREATED
    assert body['title'] == 'test'
    assert body['url'] == 'https://test.ru/'
    assert body['wish'] is None


@pytest.mark.django_db
def test_create_gift_plan_item_title_only(
        api_client,
        profile,
        auth_headers,
        gift_plan_factory,
):
    gift_plan = gift_plan_factory(profile)
    response = api_client.post(
        f'/api/gifts/plan/{gift_plan.id}/item/',
        payload={'title': 'manual'},
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.CREATED
    assert body['title'] == 'manual'
    assert body['url'] == ''
    assert body['wish'] is None


@pytest.mark.django_db
def test_create_gift_plan_item_someone_else_wishlist(
        api_client,
        profile_factory,
        auth_headers,
        gift_plan_factory,
        wishlist_factory,
        wish_factory
):
    wishlist_owner = profile_factory(telegram_user_id=1)
    profile = profile_factory(telegram_user_id=2)

    gift_plan = gift_plan_factory(profile)

    wishlist = wishlist_factory(wishlist_owner)
    wish = wish_factory(wishlist)

    response = api_client.post(
        f'/api/gifts/plan/{gift_plan.id}/item/',
        payload={
            'wish': wish.id,
        },
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert not GiftPlanItem.objects.filter(plan=gift_plan, wish=wish).exists()


@pytest.mark.django_db
def test_list_gift_plans_empty(api_client, profile, auth_headers):
    response = api_client.get(
        '/api/gifts/plan/',
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


@pytest.mark.django_db
def test_list_gift_plans_excludes_someone_else(
        api_client,
        profile_factory,
        gift_plan_factory,
        auth_headers,
):
    me = profile_factory(telegram_user_id=1)
    other = profile_factory(telegram_user_id=2)
    mine = gift_plan_factory(me, title='mine')
    gift_plan_factory(other, title='theirs')

    response = api_client.get(
        '/api/gifts/plan/',
        headers=auth_headers(me.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert len(body) == 1
    assert body[0]['id'] == mine.id
    assert body[0]['title'] == 'mine'


@pytest.mark.django_db
def test_get_gift_plan_happy_path(
        api_client,
        profile,
        auth_headers,
        gift_plan_factory,
):
    plan = gift_plan_factory(profile, title='one')
    response = api_client.get(
        f'/api/gifts/plan/{plan.id}',
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body['id'] == plan.id
    assert body['title'] == 'one'


@pytest.mark.django_db
def test_get_gift_plan_someone_else(
        api_client,
        profile_factory,
        gift_plan_factory,
        auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    profile_factory(telegram_user_id=2)
    plan = gift_plan_factory(owner)

    response = api_client.get(
        f'/api/gifts/plan/{plan.id}',
        headers=auth_headers(2),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
def test_list_gift_plan_items_empty(
        api_client,
        profile,
        auth_headers,
        gift_plan_factory,
):
    plan = gift_plan_factory(profile)
    response = api_client.get(
        f'/api/gifts/plan/{plan.id}/item/',
        headers=auth_headers(profile.telegram_user_id),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


@pytest.mark.django_db
def test_list_gift_plan_items_happy_path(
        api_client,
        profile,
        auth_headers,
        gift_plan_factory,
        gift_plan_item_factory,
):
    plan = gift_plan_factory(profile)
    item = gift_plan_item_factory(plan, title='socks')

    response = api_client.get(
        f'/api/gifts/plan/{plan.id}/item/',
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert len(body) == 1
    assert body[0]['id'] == item.id
    assert body[0]['title'] == 'socks'


@pytest.mark.django_db
def test_get_gift_plan_item_happy_path(
        api_client,
        profile,
        auth_headers,
        gift_plan_factory,
        gift_plan_item_factory,
):
    plan = gift_plan_factory(profile)
    item = gift_plan_item_factory(plan, title='book', url='https://book.ru')

    response = api_client.get(
        f'/api/gifts/plan/{plan.id}/item/{item.id}',
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body['id'] == item.id
    assert body['title'] == 'book'
    assert body['url'] == 'https://book.ru'


@pytest.mark.django_db
def test_update_gift_plan_item_title(
        api_client,
        profile,
        auth_headers,
        gift_plan_factory,
        gift_plan_item_factory,
):
    plan = gift_plan_factory(profile)
    item = gift_plan_item_factory(plan, title='old')

    response = api_client.patch(
        f'/api/gifts/plan/{plan.id}/item/{item.id}',
        payload={'title': 'new'},
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body['title'] == 'new'
    item.refresh_from_db()
    assert item.title == 'new'


@pytest.mark.django_db
def test_update_gift_plan_item_with_wish(
        api_client,
        profile,
        auth_headers,
        gift_plan_factory,
        gift_plan_item_factory,
        wishlist_factory,
        wish_factory,
):
    plan = gift_plan_factory(profile)
    item = gift_plan_item_factory(plan, title='manual')
    wishlist = wishlist_factory(profile)
    wish = wish_factory(wishlist, title='from-wish', url='https://from-wish.ru')

    response = api_client.patch(
        f'/api/gifts/plan/{plan.id}/item/{item.id}',
        payload={'wish': wish.id},
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body['title'] == 'from-wish'
    assert body['url'] == 'https://from-wish.ru'
    assert body['wish'] == wish.id
    item.refresh_from_db()
    assert item.wish_id == wish.id
    assert item.title == 'from-wish'


@pytest.mark.django_db
def test_delete_gift_plan_item_happy_path(
        api_client,
        profile,
        auth_headers,
        gift_plan_factory,
        gift_plan_item_factory,
):
    plan = gift_plan_factory(profile)
    item = gift_plan_item_factory(plan)
    item_id = item.id

    response = api_client.delete(
        f'/api/gifts/plan/{plan.id}/item/{item.id}',
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body['item_id'] == item_id
    assert not GiftPlanItem.objects.filter(id=item_id).exists()


@pytest.mark.django_db
def test_delete_gift_plan_happy_path(
        api_client,
        profile,
        auth_headers,
        gift_plan_factory,
        gift_plan_item_factory,
):
    plan = gift_plan_factory(profile)
    gift_plan_item_factory(plan)
    plan_id = plan.id

    response = api_client.delete(
        f'/api/gifts/plan/{plan.id}',
        headers=auth_headers(profile.telegram_user_id),
    )
    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert body['plan_id'] == plan_id
    assert not GiftPlan.objects.filter(id=plan_id).exists()
    assert not GiftPlanItem.objects.filter(plan_id=plan_id).exists()


@pytest.mark.django_db
def test_delete_gift_plan_someone_else(
        api_client,
        profile_factory,
        gift_plan_factory,
        auth_headers,
):
    owner = profile_factory(telegram_user_id=1)
    profile_factory(telegram_user_id=2)
    plan = gift_plan_factory(owner)

    response = api_client.delete(
        f'/api/gifts/plan/{plan.id}',
        headers=auth_headers(2),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert GiftPlan.objects.filter(id=plan.id).exists()


@pytest.mark.django_db
def test_without_bearer(api_client):
    response_plan = api_client.post(
        '/api/gifts/plan/',
        payload={
            'title': 'test',
            'occurs_at': timezone.now().isoformat(),
        },
        headers={},
    )
    assert response_plan.status_code == HTTPStatus.UNAUTHORIZED
    response_item = api_client.post(
        '/api/gifts/plan/1/item/',
        payload={
            'title': 'test',
            'url': 'https://test.ru',
        },
        headers={},
    )
    assert response_item.status_code == HTTPStatus.UNAUTHORIZED
    response_list = api_client.get('/api/gifts/plan/', headers={})
    assert response_list.status_code == HTTPStatus.UNAUTHORIZED
