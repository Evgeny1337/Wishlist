import secrets
from http import HTTPStatus
from typing import List, Optional

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest
from ninja import Path, Router, Status
from ninja.errors import HttpError
from pydantic import PositiveInt

from invites.admin_access import require_admin
from invites.auth import TelegramJWTAuth
from invites.models import Invite, TelegramProfile
from invites.pydantic_models import (
    ActivateIn,
    InviteCreateIn,
    InviteOut,
    ProfileLookupOut,
    ProfileLookupTelegramOut,
)
from invites.services import activate_invite_from_activate_in
from invites.telegram_lookup import lookup_telegram_chat
from wishlists.schemas import DetailSchema

router = Router()


def _build_startapp_url(token: str) -> Optional[str]:
    bot = (getattr(settings, "TELEGRAM_BOT_USERNAME", None) or "").strip().lstrip("@")
    if not bot:
        return None
    return f"https://t.me/{bot}?startapp={token}"


def _invite_to_out(invite: Invite) -> InviteOut:
    return InviteOut(
        token=invite.token,
        max_uses=invite.max_uses,
        used_count=invite.used_count,
        is_active=invite.is_active,
        expires_at=invite.expires_at,
        for_telegram_user_id=invite.for_telegram_user_id,
        created_at=invite.created_at,
        startapp_url=_build_startapp_url(invite.token),
    )


def _generate_invite_token() -> str:
    # start_param в Telegram — до 64 символов
    return secrets.token_urlsafe(18)[:64]


@router.post("/activate")
def activate_invite(request, activate_data: ActivateIn):
    with transaction.atomic():
        used_count = activate_invite_from_activate_in(activate_data)
    return {
        "ok": True,
        "used_count": used_count,
        "token": activate_data.token,
    }


@router.post(
    "/admin/",
    auth=TelegramJWTAuth(),
    response={
        HTTPStatus.CREATED: InviteOut,
        HTTPStatus.BAD_REQUEST: DetailSchema,
        HTTPStatus.FORBIDDEN: DetailSchema,
        HTTPStatus.UNAUTHORIZED: DetailSchema,
    },
)
def create_invite_admin(request: HttpRequest, body: InviteCreateIn):
    require_admin(request.auth)

    raw_token = (body.token or "").strip() or _generate_invite_token()
    if len(raw_token) > 64:
        raise HttpError(HTTPStatus.BAD_REQUEST, "Токен длиннее 64 символов")
    if Invite.objects.filter(token=raw_token).exists():
        raise HttpError(HTTPStatus.BAD_REQUEST, "Такой токен уже существует")

    invite = Invite.objects.create(
        token=raw_token,
        max_uses=body.max_uses,
        expires_at=body.expires_at,
        for_telegram_user_id=body.for_telegram_user_id,
    )
    return Status(HTTPStatus.CREATED, _invite_to_out(invite))


@router.get(
    "/admin/",
    auth=TelegramJWTAuth(),
    response={
        HTTPStatus.OK: List[InviteOut],
        HTTPStatus.FORBIDDEN: DetailSchema,
        HTTPStatus.UNAUTHORIZED: DetailSchema,
    },
)
def list_invites_admin(request: HttpRequest):
    require_admin(request.auth)
    invites = Invite.objects.order_by("-created_at")[:50]
    return Status(HTTPStatus.OK, [_invite_to_out(item) for item in invites])


@router.get(
    "/admin/profiles/{telegram_user_id}/",
    auth=TelegramJWTAuth(),
    response={
        HTTPStatus.OK: ProfileLookupOut,
        HTTPStatus.FORBIDDEN: DetailSchema,
        HTTPStatus.UNAUTHORIZED: DetailSchema,
    },
)
def lookup_profile_admin(
    request: HttpRequest,
    telegram_user_id: PositiveInt = Path(...),
):
    require_admin(request.auth)

    profile = TelegramProfile.objects.filter(
        telegram_user_id=telegram_user_id,
    ).first()
    in_telegram, telegram_meta = lookup_telegram_chat(int(telegram_user_id))

    return Status(
        HTTPStatus.OK,
        ProfileLookupOut(
            telegram_user_id=int(telegram_user_id),
            in_app=profile is not None,
            username=profile.username if profile else None,
            first_name=profile.first_name if profile else None,
            last_name=profile.last_name if profile else None,
            in_telegram=in_telegram,
            telegram=(
                ProfileLookupTelegramOut(**telegram_meta)
                if telegram_meta
                else None
            ),
        ),
    )
