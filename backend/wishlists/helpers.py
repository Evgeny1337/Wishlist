from http import HTTPStatus

from django.conf import settings
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

from invites.models import TelegramProfile
from invites.telegram_init_data import verify_init_data, InvalidInitData
from invites.telegram_webapp_user import telegram_user_init_data


def get_profile(init_data: str) -> TelegramProfile:
    if  not init_data:
        raise HttpError(HTTPStatus.UNPROCESSABLE_ENTITY,"пустой initData")
    try:
        pairs = verify_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)
        user = telegram_user_init_data(pairs)
    except InvalidInitData as exc:
        raise HttpError(HTTPStatus.UNPROCESSABLE_ENTITY, str(exc)) from exc
    return get_object_or_404(TelegramProfile, telegram_user_id=user.id)