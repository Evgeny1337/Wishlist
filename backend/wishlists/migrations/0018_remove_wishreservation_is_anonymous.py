from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("wishlists", "0017_wishlist_is_anonymous"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="wishreservation",
            name="is_anonymous",
        ),
    ]
