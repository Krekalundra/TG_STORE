# models.productImage.py
from django.db import models
from django.core.exceptions import ValidationError
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from tgshop.models.product import Product  # правильный импорт


def validate_single_cover(image_instance):
    """Проверка, что только одно изображение — обложка."""
    if image_instance.is_cover:
        existing_cover = ProductImage.objects.filter(
            product=image_instance.product, 
            is_cover=True
        ).exclude(pk=image_instance.pk).exists()
        if existing_cover:
            raise ValidationError("Обложка уже выбрана для этого товара.")

class ProductImage(models.Model):
    
    product = models.ForeignKey(
        Product,  # прямая ссылка на модель
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name="Товар"
    )
    image = ProcessedImageField(
        upload_to='products/%Y/%m/%d/',
        processors=[ResizeToFill(800, 600)],
        format='JPEG',
        options={'quality': 80},
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