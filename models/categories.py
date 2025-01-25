from django.db import models

class Category(models.Model):
    name = models.CharField(
        "Название категории", 
        max_length=100
    )
    order = models.PositiveIntegerField(
        "Порядок отображения", 
        default=0
    )
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order']

    def __str__(self):
        return self.name