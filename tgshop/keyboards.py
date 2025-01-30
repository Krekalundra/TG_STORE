from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from tgshop.models.categories import Category
from tgshop.models.product import Product
from django.shortcuts import get_object_or_404
#Запрашиваем категории товаров
#Для коммита


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


def create_keyboard(category_id=None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Получаем подкатегории
    subcategories = Category.objects.filter(parent_id=category_id)
    products = Product.objects.filter(category_id=category_id)
    
    # Добавляем кнопки подкатегорий
    for subcategory in subcategories:
        keyboard.add(InlineKeyboardButton(
            text=subcategory.name,
            callback_data=f"category_{subcategory.id}"
        ))
    
    # Добавляем кнопки товаров
    for product in products:
        keyboard.add(InlineKeyboardButton(
            text=f"{product.name} - {product.price}₽",
            callback_data=f"product_{product.id}"
        ))
    
    # Добавляем кнопку "Назад"
    if category_id is not None:
        # Получаем текущую категорию
        current_category = Category.objects.get(id=category_id)
        # Если есть родительская категория, возвращаемся к ней
        if current_category.parent_id:
            back_id = current_category.parent_id
        else:
            # Если родительской категории нет, возвращаемся в корневое меню
            back_id = "main"
        
        keyboard.add(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"category_{back_id}"
        ))
    
    return keyboard
