#tgshop/tgshop/admin.py

from django.contrib import admin
from tgshop.models.settings import TelegramSettings
from tgshop.models.operators import Operator
from tgshop.models.categories import Category
from tgshop.models.product import Product
from tgshop.models.productImage import ProductImage
from tgshop.models.customer import Customer
from tgshop.models.order import Order, OrderItem
from tgshop.models.cart import Cart, CartItem

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3  # Количество форм для новых фото

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('price',)

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ('created_at',)

@admin.register(TelegramSettings)
class TelegramSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False  # Запрет на добавление новых записей

    def has_delete_permission(self, request, obj=None):
        return False  # Запрет на удалениеtgshop

@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ['username']  # Убираем is_active из списка отображаемых полей
    search_fields = ['username']

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

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'first_name', 'last_name', 'phone', 'delivery_method', 'discount')
    list_filter = ('delivery_method', 'created_at')
    search_fields = ('telegram_id', 'first_name', 'last_name', 'phone')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('telegram_id', 'created_at')
        }),
        ('Личные данные', {
            'fields': ('first_name', 'middle_name', 'last_name', 'phone')
        }),
        ('Доставка', {
            'fields': ('address', 'delivery_method')
        }),
        ('Дополнительно', {
            'fields': ('discount',)
        }),
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__telegram_id', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('created_at',)
    inlines = [OrderItemInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('customer', 'status', 'total_amount', 'created_at')
        }),
        ('Доставка', {
            'fields': ('delivery_address',)
        }),
        ('Дополнительно', {
            'fields': ('comment',)
        }),
    )

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('customer', 'get_total_amount', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('customer__telegram_id', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]
    
    def get_total_amount(self, obj):
        return obj.get_total_amount()
    get_total_amount.short_description = "Сумма"