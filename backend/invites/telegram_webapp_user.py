import json

from invites.pydantic_models import UserModel
from invites.telegram_init_data import InvalidInitData
from pydantic import ValidationError


def telegram_user_init_data(pairs: dict[str, str]) -> UserModel:
    if "user" not in pairs:
        raise InvalidInitData("Нет поля user")
    try:
        user_dict = json.loads(pairs["user"])
    except json.JSONDecodeError:
        raise InvalidInitData("Ошибка загрузки user")
    if not isinstance(user_dict, dict):
        raise InvalidInitData("user не является dict")
    try:
        user: UserModel = UserModel(**user_dict)
    except (ValidationError, TypeError):
        raise InvalidInitData("поле user не валидно")
    if user.id <= 0:
        raise InvalidInitData("Не корректный id user")
    return user
