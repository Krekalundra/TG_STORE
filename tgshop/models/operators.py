# tgshop/models/operators.py
from django.db import models

class Operator(models.Model):
    username = models.CharField(
        "Telegram username оператора", 
        max_length=100,
        unique=True,
        help_text="Без @ (например: johnsmith)"
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