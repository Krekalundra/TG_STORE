from django.core.validators import FileExtensionValidator, MaxValueValidator
from django.db import models
from tgshop.models.categories import Category
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from django.core.exceptions import ValidationError

def validate_telegram_length(value):
    """Валидатор для проверки длины описания"""
    MAX_TELEGRAM_LENGTH = 1024  # Максимальная длина подписи к фото в Telegram
    if len(value) > MAX_TELEGRAM_LENGTH:
        raise ValidationError(
            f'Описание слишком длинное. Максимальная длина - {MAX_TELEGRAM_LENGTH} символов. '
            f'Текущая длина - {len(value)} символов.'
        )

class Product(models.Model):
    PRICE_TYPE_CHOICES = [
        ('piece', 'За штуку'),
        ('gram', 'За грамм'),
    ]
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name="Категория"
    )
    is_active = models.BooleanField(
        "Активен", 
        default=True
    )
    name = models.CharField(
        "Название товара", 
        max_length=100
    )
    dis_product = models.TextField(
        blank=True, 
        verbose_name="Описание",
        validators=[validate_telegram_length],
        help_text="Максимальная длина - 1024 символа (ограничение Telegram)"
    )
    price = models.DecimalField(
        "Цена", 
        max_digits=6, 
        decimal_places=2
    )
    price_type = models.CharField(
        max_length=10,
        choices=PRICE_TYPE_CHOICES,
        default='piece',
        verbose_name="Тип цены"
    )


    class Meta:
        db_table = "tgshop_product"
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name