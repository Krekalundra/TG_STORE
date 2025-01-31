from django.db import models

class Customer(models.Model):
    telegram_id = models.BigIntegerField(
        unique=True,
        verbose_name="Telegram ID"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата регистрации"
    )
    first_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Имя"
    )
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Отчество"
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Фамилия"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Телефон"
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name="Адрес доставки"
    )
    delivery_method = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Способ доставки",
        help_text="Например: Самовывоз, Курьер, Почта России и т.д."
    )
    discount = models.PositiveIntegerField(
        default=0,
        verbose_name="Скидка (%)"
    )

    class Meta:
        db_table = "tgshop_customer"
        verbose_name = "Покупатель"
        verbose_name_plural = "Покупатели"
        ordering = ['-created_at']

    def __str__(self):
        name = self.first_name or f"User {self.telegram_id}"
        return f"{name} ({self.telegram_id})" 