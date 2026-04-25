from django.contrib import admin
from invites.models import Invite, TelegramProfile, InviteActivation

@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    pass

@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    pass

@admin.register(InviteActivation)
class InviteActivationAdmin(admin.ModelAdmin):
    pass

