from django.db.models import Q

from invites.models import TelegramProfile


def can_edit_wishlist(profile: TelegramProfile):
    return Q(owner=profile)


def can_view_wishlist(profile: TelegramProfile):
    return Q(wishlist_accesses__profile=profile) | Q(owner=profile)