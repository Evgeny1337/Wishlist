from django.db import models

from invites.models import TelegramProfile


class WishList(models.Model):
    owner = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, related_name="wishlists")
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class Wish(models.Model):
    class WishPriority(models.IntegerChoices):
        LOW = 1
        MEDIUM = 2
        HIGH = 3
    wishlist = models.ForeignKey(WishList, on_delete=models.CASCADE, related_name="wishes")
    title = models.CharField(max_length=200)
    url = models.URLField(blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.IntegerField(choices=WishPriority, default=WishPriority.LOW)


class WishReservation(models.Model):
    wish = models.ForeignKey(Wish, on_delete=models.CASCADE, related_name="reservation")
    profile = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, related_name="reservations")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["wish"],
                name="unique_reservation",
            )
        ]
