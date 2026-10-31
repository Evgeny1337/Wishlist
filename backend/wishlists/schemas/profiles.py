from ninja import ModelSchema

from invites.models import TelegramProfile


class ProfileResponse(ModelSchema):
    class Meta:
        model = TelegramProfile
        fields = ["telegram_user_id", "username"]
