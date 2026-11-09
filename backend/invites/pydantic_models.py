from datetime import datetime
from typing import Optional

from ninja import Schema
from pydantic import BaseModel, Field, PositiveInt


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str = Field(description="Access Token (короткий промежуток времени)")
    refresh_token: str = Field(description="Refresh Token (длинный промежуток времени)")
    token_type: str = Field(description="Тип токен", default="Bearer")
    expires_in: int = Field(description="Время жизни Access Token")
    refresh_expires_in: int = Field(description="Время жи Refresh Token")

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
    tokens: TokenPair


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


class ErrorUnauthorized(Schema):
    detail: dict[str, str]


class InviteCreateIn(BaseModel):
    max_uses: PositiveInt = Field(default=1, description="Лимит активаций")
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Срок действия (UTC); пусто — без срока",
    )
    for_telegram_user_id: Optional[PositiveInt] = Field(
        default=None,
        description="Личный инвайт только для этого tg id; пусто — общий",
    )
    token: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Свой токен startapp; пусто — сгенерировать",
    )


class InviteOut(BaseModel):
    token: str
    max_uses: int
    used_count: int
    is_active: bool
    expires_at: Optional[datetime] = None
    for_telegram_user_id: Optional[int] = None
    created_at: datetime
    startapp_url: Optional[str] = None


class ProfileLookupTelegramOut(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    type: Optional[str] = None


class ProfileLookupOut(BaseModel):
    telegram_user_id: int
    in_app: bool
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    in_telegram: Optional[bool] = Field(
        default=None,
        description="None — Bot API недоступен; True/False — ответ getChat",
    )
    telegram: Optional[ProfileLookupTelegramOut] = None
