from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("wishlists", "0014_alter_reminder_title"),
    ]

    operations = [
        migrations.DeleteModel(
            name="GiftPlanItem",
        ),
        migrations.DeleteModel(
            name="GiftPlan",
        ),
    ]
