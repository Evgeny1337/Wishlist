from invites.models import TelegramProfile
from invites.telegram_webapp_user import UserModel


def ensure_telegram_profile(user: UserModel) -> TelegramProfile:
    telegram_profile, _ = TelegramProfile.objects.get_or_create(
        telegram_user_id=user.id,
        defaults={
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    )
    return telegram_profile