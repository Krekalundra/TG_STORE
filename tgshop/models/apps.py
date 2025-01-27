from django.apps import AppConfig

class ModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tgshop.models'  # совпадает с Python-путём до этой папки
    verbose_name = "Магазин" # то, как приложение будет называться в админке

def ready(self):
        # Импортируем модели после инициализации
    from .models import (
        Category,
        Operator,
        Product,
        ProductImage,
        TelegramSettings
    )