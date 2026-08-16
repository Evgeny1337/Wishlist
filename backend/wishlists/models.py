from django.db import models
from django.db.models import Q

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


class Event(models.Model):
    title = models.CharField(max_length=200)
    owner = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, related_name="events")
    wishlist = models.ForeignKey(WishList, on_delete=models.PROTECT, related_name="events")
    created_at = models.DateTimeField(auto_now_add=True)
    starts_at = models.DateTimeField()


class WishListAccess(models.Model):
    profile = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, related_name="wishlist_accesses")
    wishlist = models.ForeignKey(WishList, on_delete=models.CASCADE, related_name="wishlist_accesses")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "wishlist"],
                name="unique_wishlist_access",
            )
        ]


class EventAccess(models.Model):
    profile = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, related_name="event_accesses")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="event_accesses")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "event"],
                name="unique_event_access",
            )
        ]


class GiftPlan(models.Model):
    owner = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE, related_name="gift_plan")
    title = models.CharField(max_length=200)
    occurs_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class GiftPlanItem(models.Model):
    plan = models.ForeignKey(GiftPlan, on_delete=models.CASCADE, related_name="plan_items")
    wish = models.ForeignKey(Wish, on_delete=models.SET_NULL, related_name="plan_items", null=True)
    title = models.CharField(max_length=200)
    url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.wish:
            self.title = self.wish.title
            self.url = self.wish.url
        super().save(*args, **kwargs)
        return self

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(wish__isnull=False) | (Q(title__isnull=False) & Q(url__isnull=False)),
                name="xor_gift_plan_item",
            )
        ]
