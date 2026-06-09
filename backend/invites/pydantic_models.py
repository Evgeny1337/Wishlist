from typing import Optional

from pydantic import BaseModel


class TelegramUser(BaseModel):
    telegram_user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ActivateIn(BaseModel):
    token: str
    telegram_user: TelegramUser


class VerifyInitDataIn(BaseModel):
    init_data: str


class VerifyInitDataOut(BaseModel):
    ok: bool
    telegram_user_id: int


class ActivateViaWebAppIn(BaseModel):
    init_data: str
    token: str


class ActivateViaWebAppOut(BaseModel):
    ok: bool
    used_count: int
    token: str
    telegram_user_id: int


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
