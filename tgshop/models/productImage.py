# models.productImage.py
from django.db import models
from django.core.exceptions import ValidationError
from tgshop.models.product import Product  # правильный импорт
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill


def validate_single_cover(instance):
    """Проверяет, что у товара только одна обложка"""
    # Пропускаем валидацию если это новый товар
    if not instance.product_id:
        return
        
    existing_cover = ProductImage.objects.filter(
        product=instance.product,
        is_cover=True
    ).exclude(id=instance.id if instance.id else None).exists()
    
    if instance.is_cover and existing_cover:
        raise ValidationError('У товара может быть только одна обложка')

class ProductImage(models.Model):
    """Модель изображения товара"""
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Товар'
    )
    image = ProcessedImageField(
        upload_to='products/%Y/%m/%d/',
        processors=[ResizeToFill(800, 600)],
        format='JPEG',
        options={'quality': 85, 'optimize': True},
        verbose_name="Изображение"
    )
    is_cover = models.BooleanField(
        "Обложка", 
        default=False,
        help_text="Главное изображение товара"
    )
    order = models.PositiveIntegerField(
        "Порядок", 
        default=0,
        help_text="Чем меньше число, тем выше в списке"
    )

    class Meta:
        db_table = "tgshop_productimage"
        ordering = ['order']
        verbose_name = "Фотография товара"
        verbose_name_plural = "Фотографии товаров"

    def __str__(self):
        return f"Фото {self.order} для {self.product.name}"

    def clean(self):
        validate_single_cover(self)
        super().clean()