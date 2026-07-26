from http import HTTPStatus

from django.conf import settings
from django.db import transaction
from ninja import Router
from ninja.errors import HttpError, ValidationError

from invites.jwt_tokens import issue_token_pair
from invites.pydantic_models import (
    ActivateViaWebAppIn,
    ActivateViaWebAppOut,
    VerifyInitDataIn,
    VerifyInitDataOut,
)
from invites.services import (
    apply_invite_token_for_webapp_user,
    ensure_telegram_profile,
)
from invites.telegram_init_data import InvalidInitData, verify_init_data
from invites.telegram_webapp_user import telegram_user_init_data

router = Router()


@router.post("/verify-init-data", response=VerifyInitDataOut)
def verify_init_data_view(request, body: VerifyInitDataIn):
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
def activate_invite_via_init_data_view(request, body: ActivateViaWebAppIn):
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

    try:
        jwt_pairs = issue_token_pair(telegram_user_id=profile.telegram_user_id)
        return ActivateViaWebAppOut(
            ok=True,
            used_count=used_count,
            token=body.token,
            telegram_user_id=profile.telegram_user_id,
            tokens=jwt_pairs,
        )
    except ValidationError:
        raise HttpError(HTTPStatus.UNPROCESSABLE_ENTITY, "Ошибка создания JWT")


