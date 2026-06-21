import json

import pytest

from invites.telegram_init_data import InvalidInitData
from invites.telegram_webapp_user import UserModel, telegram_user_init_data

from .helpers import pairs_with_user


def test_telegram_user_init_data_success_minimal():
    user = telegram_user_init_data(pairs_with_user({"id": 991_001}))
    assert isinstance(user, UserModel)
    assert user.id == 991_001


def test_telegram_user_init_data_success_optional_fields():
    payload = {
        "id": 42,
        "first_name": "Ann",
        "last_name": "Test",
        "username": "ann_t",
        "language_code": "ru",
        "is_premium": True,
    }
    user = telegram_user_init_data(pairs_with_user(payload))
    assert user.id == 42
    assert user.first_name == "Ann"
    assert user.last_name == "Test"
    assert user.username == "ann_t"
    assert user.language_code == "ru"
    assert user.is_premium is True


def test_telegram_user_init_data_coerces_numeric_string_id():
    user = telegram_user_init_data(pairs_with_user({"id": "12345"}))
    assert user.id == 12345


def test_telegram_user_init_data_ignores_extra_keys():
    user = telegram_user_init_data(
        pairs_with_user({"id": 1, "unknown_future_field": True})
    )
    assert user.id == 1


def test_telegram_user_init_data_raises_without_user_field():
    with pytest.raises(InvalidInitData, match="Нет поля user"):
        telegram_user_init_data({"hash": "x"})


def test_telegram_user_init_data_raises_on_invalid_json():
    with pytest.raises(InvalidInitData, match="загрузки"):
        telegram_user_init_data({"user": "[}"})


def test_telegram_user_init_data_raises_when_user_not_object():
    with pytest.raises(InvalidInitData, match="не является dict"):
        telegram_user_init_data({"user": "[]"})
    with pytest.raises(InvalidInitData, match="не является dict"):
        telegram_user_init_data({"user": json.dumps("plain")})


def test_telegram_user_init_data_raises_on_missing_id():
    with pytest.raises(InvalidInitData, match="валид"):
        telegram_user_init_data(pairs_with_user({"first_name": "x"}))


def test_telegram_user_init_data_raises_on_unusable_id():
    with pytest.raises(InvalidInitData, match="валид"):
        telegram_user_init_data(pairs_with_user({"id": "nan"}))


def test_telegram_user_init_data_raises_on_id_zero_or_negative():
    with pytest.raises(InvalidInitData, match="Не корректный id"):
        telegram_user_init_data(pairs_with_user({"id": 0}))
    with pytest.raises(InvalidInitData, match="Не корректный id"):
        telegram_user_init_data(pairs_with_user({"id": -1}))
