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
    
    class Meta:
        verbose_name = "Настройка Telegram"
        verbose_name_plural = "Настройки Telegram"

    def __str__(self):
        return "Токен бота" if self.token else "Пустые настройки"