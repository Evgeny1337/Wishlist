from django.db import models

from invites.models import TelegramProfile


class WishList(models.Model):
    owner = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, related_name="wishlists")
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class Wish(models.Model):
    wishlist = models.ForeignKey(WishList, on_delete=models.CASCADE, related_name="wishes")
    title = models.CharField(max_length=200)
    url = models.URLField(blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
