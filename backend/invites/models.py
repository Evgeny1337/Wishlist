from django.db import models


class Invite(models.Model):
    token = models.CharField(unique=True, max_length=1000, verbose_name='Токен')
    max_uses = models.IntegerField(default=1, verbose_name='Разрешенное кол-во активаций')
    used_count = models.IntegerField(default=0, verbose_name='Кол-во активаций')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Срок действия")
    is_active = models.BooleanField(default=True, verbose_name='Активная ссылка')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    def __str__(self):
        return self.created_at.strftime('%Y/%m/%d') + ' - ' + ('Активный' if self.is_active else 'Не активный')

class TelegramProfile(models.Model):
    telegram_user_id = models.BigIntegerField(unique=True, verbose_name='Id Telegram')
    username = models.CharField(null=True, blank=True, max_length=200, verbose_name='Никнейм')
    first_name = models.CharField(null=True, blank=True, max_length=100, verbose_name='Имя')
    last_name = models.CharField(null=True, blank=True, max_length=100, verbose_name='Фамилия')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    def __str__(self):
        return str(self.telegram_user_id) + ' - ' +  (self.username or '')

class InviteActivation(models.Model):
    invite = models.ForeignKey(Invite, on_delete=models.CASCADE)
    telegram_profile = models.ForeignKey(TelegramProfile, on_delete=models.CASCADE)
    activated_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('invite', 'telegram_profile')
    def __str__(self):
        return str(self.invite) + ' - ' + str(self.telegram_profile)

