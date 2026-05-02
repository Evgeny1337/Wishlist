from django.conf import settings
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from invites.services import ensure_telegram_profile
from invites.telegram_init_data import InvalidInitData, verify_init_data
from invites.telegram_webapp_user import telegram_user_init_data

router = Router()

class VerifyInitDataIn(BaseModel):
    init_data: str

class VerifyInitDataOut(BaseModel):
    ok: bool
    telegram_user_id: int

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