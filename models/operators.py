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
        verbose_name = "Оператор"
        verbose_name_plural = "Операторы"

    def __str__(self):
        return f"@{self.username}"