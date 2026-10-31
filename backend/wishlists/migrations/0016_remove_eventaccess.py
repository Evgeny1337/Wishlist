from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("wishlists", "0015_remove_giftplan"),
    ]

    operations = [
        migrations.DeleteModel(
            name="EventAccess",
        ),
    ]
