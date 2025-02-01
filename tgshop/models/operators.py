# tgshop/models/operators.py
from django.db import models

class Operator(models.Model):
    username = models.CharField(
        "Telegram username оператора", 
        max_length=100,
        help_text="Без @ (например: johnsmith)"
    )
    telegram_id = models.BigIntegerField(  # Добавляем поле для Telegram ID
        "Telegram ID оператора",
        unique=True,
        help_text="ID пользователя в Telegram"
    )
    is_active = models.BooleanField(
        "Активен", 
        default=True
    )
    
    class Meta:
        db_table = "tgshop_operator"
        verbose_name = "Оператор"
        verbose_name_plural = "Операторы"

    def __str__(self):
        return f"@{self.username}"

    # Ограничение: только одна активная запись
    def save(self, *args, **kwargs):
        if self.is_active:
            Operator.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """ Загружает активного оператора или создает нового с фиксированным ID """
        obj, created = cls.objects.get_or_create(
            is_active=True,
            defaults={
                "username": "default_operator",
                "telegram_id": 7670256977  # Фиксированный ID оператора
            }
        )
        return obj