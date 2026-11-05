from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wishlists", "0018_remove_wishreservation_is_anonymous"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wish",
            name="url",
            field=models.URLField(blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name="wish",
            name="preview_image_url",
            field=models.URLField(blank=True, default="", max_length=1000),
        ),
    ]
