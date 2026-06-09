from django.db import transaction
from ninja import Router

from .pydantic_models import ActivateIn, TelegramUser
from .services import activate_invite_from_activate_in

router = Router()


@router.post("/activate")
def activate_invite(request, activate_data: ActivateIn):
    with transaction.atomic():
        used_count = activate_invite_from_activate_in(activate_data)
    return {
        "ok": True,
        "used_count": used_count,
        "token": activate_data.token,
    }


