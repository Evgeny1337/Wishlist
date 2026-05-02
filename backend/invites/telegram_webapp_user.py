import json
from typing import Optional

from pydantic import BaseModel, ValidationError
from invites.telegram_init_data import InvalidInitData

class UserModel(BaseModel):
    id: int
    is_bot: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None
    added_to_attachment_menu: Optional[bool] = None
    allows_write_to_pm: Optional[bool] = None
    photo_url: Optional[str] = None


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


