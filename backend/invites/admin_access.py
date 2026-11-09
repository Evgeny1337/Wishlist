from django.conf import settings
from ninja.errors import HttpError

from invites.models import TelegramProfile


def is_admin_profile(profile: TelegramProfile) -> bool:
    admin_ids = getattr(settings, "ADMIN_TELEGRAM_USER_IDS", None) or []
    return profile.telegram_user_id in admin_ids


def require_admin(profile: TelegramProfile) -> TelegramProfile:
    if not is_admin_profile(profile):
        raise HttpError(403, "Недостаточно прав")
    return profile
