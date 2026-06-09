from typing import Optional

from django.utils import timezone
from ninja.errors import HttpError

from invites.models import Invite, TelegramProfile, InviteActivation
from invites.pydantic_models import ActivateIn, TelegramUser, UserModel


def telegram_profile_get_or_create(
    telegram_user_id: int,
    *,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> TelegramProfile:
    telegram_profile, _ = TelegramProfile.objects.get_or_create(
        telegram_user_id=telegram_user_id,
        defaults={
            "username": username or None,
            "first_name": first_name or None,
            "last_name": last_name or None,
        },
    )
    return telegram_profile


def ensure_telegram_profile(user: UserModel) -> TelegramProfile:
    return telegram_profile_get_or_create(
        user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )


def profile_from_activate_telegram_user(telegram_user: TelegramUser) -> TelegramProfile:
    return telegram_profile_get_or_create(
        telegram_user.telegram_user_id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
    )


def _lock_invite_or_404(invite_token: str) -> Invite:
    try:
        return Invite.objects.select_for_update().get(token=invite_token)
    except Invite.DoesNotExist:
        raise HttpError(404, "Такой ссылки-приглашения не существует")


def _assert_invite_valid(invite: Invite) -> None:
    if not invite.is_active:
        raise HttpError(403, "Ссылка более не активна")
    if invite.expires_at and invite.expires_at < timezone.now():
        raise HttpError(403, "Срок действия ссылки истек")


def _assert_personal_invite(invite: Invite, telegram_user_id: int) -> None:
    if invite.for_telegram_user_id is None:
        return
    if telegram_user_id != invite.for_telegram_user_id:
        raise HttpError(
            403,
            "Это приглашение выдано другому пользователю Telegram",
        )


def _activate_locked_invite_for_profile(
    invite: Invite, telegram_profile: TelegramProfile
) -> int:
    """Инвайт уже заблокирован и проверен."""
    exists = InviteActivation.objects.filter(
        invite=invite,
        telegram_profile=telegram_profile,
    ).exists()
    if exists:
        return invite.used_count

    if invite.used_count + 1 > invite.max_uses:
        raise HttpError(403, "Превышен лимит использования ссылки")

    InviteActivation.objects.create(invite=invite, telegram_profile=telegram_profile)
    invite.used_count += 1
    invite.save(update_fields=["used_count"])
    return invite.used_count


def apply_invite_token_to_profile(
    invite_token: str, telegram_profile: TelegramProfile
) -> int:
    """Активация по уже известному профилю (например `POST /api/invites/activate`).

    Повтор тем же профилем — идемпотентно (used_count без повторного роста).
    Только внутри atomic().
    """
    invite = _lock_invite_or_404(invite_token)
    _assert_invite_valid(invite)
    _assert_personal_invite(invite, telegram_profile.telegram_user_id)
    return _activate_locked_invite_for_profile(invite, telegram_profile)


def apply_invite_token_for_webapp_user(
    invite_token: str, web_user: UserModel
) -> tuple[int, TelegramProfile]:
    """WebApp: сначала проверяем инвайт и личность по user.id из initData, затем профиль.

    Чтобы при личном приглашении для «чужого» initData не создавалась запись TelegramProfile.
    Только внутри atomic().
    """
    invite = _lock_invite_or_404(invite_token)
    _assert_invite_valid(invite)
    _assert_personal_invite(invite, web_user.id)

    telegram_profile = ensure_telegram_profile(web_user)
    used_count = _activate_locked_invite_for_profile(invite, telegram_profile)
    return used_count, telegram_profile


def activate_invite_from_activate_in(activate_data: ActivateIn) -> int:
    profile = profile_from_activate_telegram_user(activate_data.telegram_user)
    return apply_invite_token_to_profile(activate_data.token, profile)
