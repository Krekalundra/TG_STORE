from django.db import models
from .categories import Category

class Product(models.Model):
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE,
        verbose_name="Категория"
    )
    name = models.CharField(
        "Название товара", 
        max_length=200
    )
    price = models.DecimalField(
        "Цена", 
        max_digits=10, 
        decimal_places=2
    )
    is_active = models.BooleanField(
        "Активен", 
        default=True
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name