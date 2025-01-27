#tgshop/tgshop/admin.py

from django.contrib import admin
from tgshop.models.settings import TelegramSettings
from tgshop.models.operators import Operator
from tgshop.models.categories import Category
from tgshop.models.product import Product
from tgshop.models.productImage import ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3  # Количество форм для новых фото


@admin.register(TelegramSettings)
class TelegramSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False  # Запрет на добавление новых записей

    def has_delete_permission(self, request, obj=None):
        return False  # Запрет на удалениеtgshop

@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_active')
    actions = None  # Скрыть действия массового редактирования

    def has_add_permission(self, request):
        # Разрешить добавление, но автоматически деактивировать предыдущего
        return True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
   list_display = ('name', 'parent', 'order')
   fields = ('name', 'parent', 'order')  # Добавьте все необходимые поля!



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]  # Добавляем вложенные изображения
    list_display = ('name', 'category', 'get_cover_image')  # Добавляем обложку в список
    
    # Ваш существующий код для управления ForeignKey (категории)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "category":
            field.widget.can_add_related = False  # Запретить создание новых категорий
            field.widget.can_change_related = True  # Разрешить редактирование
        return field
    
    # Метод для отображения обложки в списке товаров
    def get_cover_image(self, obj):
        cover = obj.images.filter(is_cover=True).first()
        return cover.image.url if cover else "—"
    get_cover_image.short_description = "Обложка"