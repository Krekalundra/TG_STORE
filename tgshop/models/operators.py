# tgshop/models/operators.py
from django.db import models

class Operator(models.Model):
    username = models.CharField(
        "Имя пользователя",
        max_length=100,
        help_text="Имя пользователя оператора в Telegram (без @)"
    )
    
    class Meta:
        db_table = "tgshop_operator"
        verbose_name = "Оператор"
        verbose_name_plural = "Операторы"

    def __str__(self):
        return f"@{self.username}"

    @classmethod
    def load(cls):
        """Получение или создание оператора"""
        obj, created = cls.objects.get_or_create(
            defaults={"username": "chaika_tea"}
        )
        return obj