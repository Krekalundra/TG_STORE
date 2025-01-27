# models/categories.py
from django.db import models

class Category(models.Model):
    name = models.CharField("Название", max_length=100)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Родительская категория"
    )
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        db_table = "tgshop_category"
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order']

    def __str__(self):
        return self.name