# Generated manually for personal invites

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("invites", "0007_alter_inviteactivation_activated_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="invite",
            name="for_telegram_user_id",
            field=models.BigIntegerField(
                blank=True,
                help_text="Если задано, активировать ссылку может только этот telegram user id; "
                "NULL — общий инвайт в пределах max_uses.",
                null=True,
                verbose_name="Только для Telegram user id",
            ),
        ),
    ]
