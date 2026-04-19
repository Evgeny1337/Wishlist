from typing import Optional

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel
from .models import Invite, TelegramProfile, InviteActivation
router = Router()

class TelegramUser(BaseModel):
    telegram_user_id:int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class ActivateIn(BaseModel):
    token: str
    telegram_user: TelegramUser




@router.post('/activate')
def activate_invite(request, activate_data: ActivateIn):
    with transaction.atomic():
        try:
            invite = Invite.objects.select_for_update().get(token=activate_data.token)
        except Invite.DoesNotExist:
            raise HttpError(404,'Такой ссылки-приглашения не существует')
        if not invite.is_active:
            raise HttpError(403,'Ссылка более не активна')
        if invite.expires_at and invite.expires_at < timezone.now():
            raise HttpError(403,'Срок действия ссылки истек')
        telegram_profile, _ = TelegramProfile.objects.get_or_create(
            telegram_user_id=activate_data.telegram_user.telegram_user_id,
            defaults={
                "username": activate_data.telegram_user.username or None,
                "first_name": activate_data.telegram_user.first_name or None,
                "last_name": activate_data.telegram_user.last_name or None,
            }
        )
        invite_activation, created = InviteActivation.objects.get_or_create(invite=invite, telegram_profile=telegram_profile)
        if not created:
            raise HttpError(409, 'Такая пара пользователь - ссылка уже зарегистрирована')
        if invite.used_count + 1 > invite.max_uses:
            raise  HttpError(403, 'Превышен лимит использования ссылки')
        invite.used_count += 1
        invite.save()
        return {"ok":True, "used_count":invite.used_count, "token":activate_data.token}



