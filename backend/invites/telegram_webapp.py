from http import HTTPStatus

import jwt
from django.conf import settings
from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from invites.jwt_tokens import issue_token_pair, decode_token
from invites.models import TelegramProfile
from invites.pydantic_models import (
    ActivateViaWebAppIn,
    ActivateViaWebAppOut,
    VerifyInitDataIn,
    VerifyInitDataOut,
    TokenPair,
    RefreshIn,
)
from invites.services import (
    apply_invite_token_for_webapp_user,
    ensure_telegram_profile,
)
from invites.telegram_init_data import InvalidInitData, verify_init_data
from invites.telegram_webapp_user import telegram_user_init_data
from wishlists.schemas import DetailSchema

router = Router()


def _require_jwt_secret() -> None:
    if not (settings.JWT_SECRET or "").strip():
        raise HttpError(HTTPStatus.SERVICE_UNAVAILABLE, "JWT_SECRET не задан")


@router.post("/verify-init-data", response=VerifyInitDataOut)
def verify_init_data_view(request: HttpRequest, body: VerifyInitDataIn):
    token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    if not token:
        raise HttpError(503, "TELEGRAM_BOT_TOKEN не задан")
    try:
        pairs = verify_init_data(body.init_data, token)
        web_user = telegram_user_init_data(pairs)
        profile = ensure_telegram_profile(web_user)
    except InvalidInitData as exc:
        raise HttpError(422, str(exc)) from exc
    return VerifyInitDataOut(ok=True, telegram_user_id=profile.telegram_user_id)


@router.post("/activate-invite", response=ActivateViaWebAppOut)
def activate_invite_via_init_data_view(request: HttpRequest, body: ActivateViaWebAppIn):
    bot_token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    if not bot_token:
        raise HttpError(503, "TELEGRAM_BOT_TOKEN не задан")
    try:
        pairs = verify_init_data(body.init_data, bot_token)
        web_user = telegram_user_init_data(pairs)
    except InvalidInitData as exc:
        raise HttpError(422, str(exc)) from exc

    with transaction.atomic():
        used_count, profile = apply_invite_token_for_webapp_user(body.token, web_user)

    _require_jwt_secret()
    return ActivateViaWebAppOut(
        ok=True,
        used_count=used_count,
        token=body.token,
        telegram_user_id=profile.telegram_user_id,
        tokens=issue_token_pair(telegram_user_id=profile.telegram_user_id),
    )


@router.post('/session', response={
        HTTPStatus.OK: TokenPair,
})
def access_session_view(request: HttpRequest, body: VerifyInitDataIn):
    bot_token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    if not bot_token:
        raise HttpError(503, "TELEGRAM_BOT_TOKEN не задан")
    try:
        pairs = verify_init_data(body.init_data, bot_token)
        web_user = telegram_user_init_data(pairs)
    except InvalidInitData:
        raise HttpError(HTTPStatus.UNPROCESSABLE_ENTITY, "Ошибка валидации init_data")
    profile = get_object_or_404(TelegramProfile, telegram_user_id=web_user.id)
    _require_jwt_secret()
    return HTTPStatus.OK, issue_token_pair(telegram_user_id=profile.telegram_user_id)


@router.post('/refresh', response={
        HTTPStatus.OK: TokenPair,
        HTTPStatus.UNAUTHORIZED: DetailSchema,
        HTTPStatus.NOT_FOUND: DetailSchema,
})
def refresh_session_view(request: HttpRequest, body: RefreshIn):
    _require_jwt_secret()
    refresh_token = body.refresh_token
    try:
        payload = decode_token(refresh_token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HttpError(HTTPStatus.UNAUTHORIZED, "Ошибка JWT")
    if payload.get("type") != "refresh":
        raise HttpError(HTTPStatus.UNAUTHORIZED, "Не верный тип токена")
    if 'sub' not in payload:
        raise HttpError(HTTPStatus.UNAUTHORIZED, "Отсутсвуют данные пользователя")
    telegram_user_id = int(payload["sub"])
    get_object_or_404(TelegramProfile, telegram_user_id=telegram_user_id)
    return HTTPStatus.OK, issue_token_pair(telegram_user_id)





