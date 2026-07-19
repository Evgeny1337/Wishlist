from http import HTTPStatus

import pytest
from django.test import override_settings

from invites.tests.helpers import fresh_signed_init_data_user_id, BOT_TOKEN_VERIFY
from wishlists.models import  Wish


@pytest.mark.django_db
def test_create_wish_empty_title(
        api_client,
):
    response = api_client.post(
        '/api/wishlists/1/wishes/',
        payload={'title': '', 'note':'test', 'url':'https://test-kek.ru','init_data':'test'}
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'][0]['type'] == 'string_too_short'
    assert body['detail'][0]['loc'] == ['body', 'data', 'title']
    assert body['detail'][0]['msg'] == 'String should have at least 1 character'
    assert body['detail'][0]['ctx'] == {'min_length': 1}
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
def test_create_wish_incorrect_url(
        api_client,
):
    response = api_client.post(
        '/api/wishlists/1/wishes/',
        payload={'title': 'test', 'note':'test', 'url':'test','init_data':'test'}
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'][0]['type'] == 'url_parsing'
    assert body['detail'][0]['loc'] == ['body', 'data', 'url']
    assert body['detail'][0]['msg'] == 'Input should be a valid URL, relative URL without a base'
    assert body['detail'][0]['ctx'] == {'error': 'relative URL without a base'}
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_create_wish_happy_path(
        api_client,
        profile,
        wishlist_factory,
):
    init_data = fresh_signed_init_data_user_id(1)
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.post(
        f'/api/wishlists/{wishlist.id}/wishes/',
        payload={'url':'https://test-kek.ru','init_data':init_data,'title':'test', 'note':'test'},
    )
    body = response.json()
    assert body['note'] == 'test'
    assert body['url'] == 'https://test-kek.ru/'
    assert body['title'] == 'test'
    assert response.status_code == HTTPStatus.CREATED
    assert Wish.objects.filter(wishlist=wishlist, id=body['id']).exists()


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_get_wishes_someone_else_wishlist(
        api_client,
        profile_factory,
        wishlist_factory,
        wish_factory
):
    profile_1 = profile_factory(telegram_user_id=1)
    profile_factory(telegram_user_id=2)
    init_data = fresh_signed_init_data_user_id(2)
    wishlist = wishlist_factory(telegram_profile=profile_1)
    wish_factory(wishlist=wishlist)
    response = api_client.get(
        f'/api/wishlists/{wishlist.id}/wishes/',
        headers={'init_data':init_data},
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'Not Found'
    assert response.status_code == HTTPStatus.NOT_FOUND


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_get_wishes_empty_wish(
        api_client,
        profile,
        wishlist_factory
):
    init_data = fresh_signed_init_data_user_id(1)
    wishlist = wishlist_factory(telegram_profile=profile)
    response = api_client.get(
        f'/api/wishlists/{wishlist.id}/wishes/',
        headers={'init_data':init_data},
    )
    body = response.json()
    assert body == []
    assert response.status_code == HTTPStatus.OK


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_get_wishes_happy_path(
        api_client,
        profile,
        wishlist_factory,
        wish_factory
):
    init_data = fresh_signed_init_data_user_id(1)
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.get(
        f'/api/wishlists/{wishlist.id}/wishes/',
        headers={'init_data':init_data},
    )
    body = response.json()
    assert len(body) == 1
    item = body[0]
    assert item["id"] == wish.id
    assert item["title"] == wish.title
    assert item["url"] == wish.url
    assert item["note"] == wish.note
    assert item["wishlist_id"] == wishlist.id
    assert "created_at" in item
    assert response.status_code == HTTPStatus.OK


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_delete_wish_happy_path(
        api_client,
        profile,
        wishlist_factory,
        wish_factory
):
    init_data = fresh_signed_init_data_user_id(1)
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.delete(
        f'/api/wishlists/{wishlist.id}/wishes/{wish.id}/',
        headers={'init_data':init_data},
    )
    body = response.json()
    assert 'deleted_count' in body
    assert body['deleted_count'] == 1
    assert response.status_code == HTTPStatus.OK
    assert not Wish.objects.filter(wishlist=wishlist, id=wish.id).exists()


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_delete_wish_wrong_wish(
        api_client,
        profile_factory,
        wishlist_factory,
        wish_factory
):
    init_data = fresh_signed_init_data_user_id(1)
    my_profile = profile_factory(telegram_user_id=1)
    other_profile = profile_factory(telegram_user_id=2)
    my_wishlist = wishlist_factory(telegram_profile=my_profile)
    other_wishlist = wishlist_factory(telegram_profile=other_profile)
    wish = wish_factory(wishlist=other_wishlist)
    response = api_client.delete(
        f'/api/wishlists/{my_wishlist.id}/wishes/{wish.id}/',
        headers={'init_data':init_data},
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'Нет такого wish'
    assert response.status_code == HTTPStatus.NOT_FOUND


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_delete_wish_someone_else_wishlist(
        api_client,
        profile_factory,
        wishlist_factory,
        wish_factory
):
    init_data = fresh_signed_init_data_user_id(1)
    profile_factory(telegram_user_id=1)
    profile_2 = profile_factory(telegram_user_id=2)
    wishlist = wishlist_factory(telegram_profile=profile_2)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.delete(
        f'/api/wishlists/{wishlist.id}/wishes/{wish.id}/',
        headers={'init_data':init_data},
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'] == 'Not Found'
    assert response.status_code == HTTPStatus.NOT_FOUND


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN_VERIFY)
@pytest.mark.django_db
def test_delete_wish_empty_init_data(
        api_client,
        profile,
        wishlist_factory,
        wish_factory
):
    wishlist = wishlist_factory(telegram_profile=profile)
    wish = wish_factory(wishlist=wishlist)
    response = api_client.delete(
        f'/api/wishlists/{wishlist.id}/wishes/{wish.id}/',
        headers={},
    )
    body = response.json()
    assert 'detail' in body
    assert body['detail'][0]['type'] == 'missing'
    assert body['detail'][0]['loc'] == ['header', 'init_data']
    assert body['detail'][0]['msg'] == 'Field required'
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

