from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from tgshop.models.categories import Category
from tgshop.models.product import Product
from django.shortcuts import get_object_or_404
#Запрашиваем категории товаров


# Свежая клавиатура меня
categories_new = Category.objects.filter(parent__isnull=True).order_by('order')
updated_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"category_{cat.id}")] 
            for cat in categories_new
        ]
    )

# Главная клавиатура
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Каталог"), KeyboardButton(text="Корзина")],
        [KeyboardButton(text="Оплата и доставка"), KeyboardButton(text="Бонусная система")],
        [KeyboardButton(text="Связь с оператором"), KeyboardButton(text="О магазине")],
    ],
    resize_keyboard=True
)

 # Создаем inline-кнопки
categories = Category.objects.filter(parent__isnull=True).order_by('order')
catalog_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"category_{cat.id}")] for cat in categories
        ]
    )


def create_keyboard(category_id):
    # Создаём список кнопок
    buttons = []
    current_category = get_object_or_404(Category, id=category_id)
    categories = Category.objects.filter(parent_id=category_id).order_by('order')
    products = Product.objects.filter(category_id=category_id).order_by('id')


    for cat in categories:
        buttons.append([InlineKeyboardButton(text=f" {cat.name}", callback_data=f"category_{cat.id}")])

    # 🔹 Затем добавляем кнопки для товаров
    for product in products:
        buttons.append([InlineKeyboardButton(text=f"{product.name} - {product.price} ₽", callback_data=f"product_{product.id}")])
    
    if current_category.parent_id:
    # Если у текущей категории есть родитель — возвращаемся к нему
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"category_{current_category.parent_id}")])
    else:
    # Если у категории нет родителя — возвращаем в главное меню
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"catalog_menu")])   

    # Создаём клавиатуру
    temp_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return temp_keyboard
