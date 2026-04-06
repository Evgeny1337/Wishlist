from django.db import models

class Wishlist(models.Model):
    title = models.CharField()
    url = models.URLField()
    price = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

