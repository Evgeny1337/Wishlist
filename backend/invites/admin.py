from django.contrib import admin
from invites.models import Invite, TelegramProfile, InviteActivation

@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ("token", "for_telegram_user_id", "used_count", "max_uses", "is_active", "expires_at")
    list_filter = ("is_active",)
    search_fields = ("token",)

@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    pass

@admin.register(InviteActivation)
class InviteActivationAdmin(admin.ModelAdmin):
    pass

