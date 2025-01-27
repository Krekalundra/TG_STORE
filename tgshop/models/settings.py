# tgshop/tgshop/models/settings.py
from django.db import models

class TelegramSettings(models.Model):
    token = models.CharField(
        "Telegram Token", 
        max_length=200,
        help_text="Получить у @BotFather",
        blank=True
    )
    chat_id = models.CharField(
        "ID чата для уведомлений", 
        max_length=100,
        blank=True,
        null=True
    )
    about = models.TextField(
        "О магазине", 
        max_length=500,
        blank=True,
        null=True
    )
    ship_pay = models.TextField(
        "Доставка и оплата", 
        max_length=500,
        blank=True,
        null=True
    )
    bonus = models.TextField(
        "Бонусная система", 
        max_length=500,
        blank=True,
        null=True
    )
    class Meta:
        db_table = "tgshop_telegramsettings"
        verbose_name = "Настройка Telegram"
        verbose_name_plural = "Настройки Telegram"

    def __str__(self):
        return "Токен бота" if self.token else "Пустые настройки"

    # Гарантируем только одну запись
    def save(self, *args, **kwargs):
        self.pk = 1  # Принудительно устанавливаем ID=1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj