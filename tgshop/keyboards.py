from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from tgshop.models.categories import Category
from tgshop.models.product import Product
from django.shortcuts import get_object_or_404
#Запрашиваем категории товаров
#Для коммита

__all__ = [
    'main_keyboard',
    'catalog_keyboard',
    'create_keyboard',
    'create_product_keyboard',
    'cancel_keyboard',
    'create_cart_keyboard',
    'create_cart_item_keyboard',
    'create_delivery_keyboard'  # Добавляем новую функцию
]

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
        [KeyboardButton(text="Оплата и доставка"), KeyboardButton(text="Личный кабинет")],
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
    # Создаем пустой список для кнопок
    buttons = []
    
    # Получаем подкатегории
    subcategories = Category.objects.filter(parent_id=category_id)
    products = Product.objects.filter(category_id=category_id)
    
    # Добавляем кнопки подкатегорий
    for subcategory in subcategories:
        buttons.append([
            InlineKeyboardButton(
                text=subcategory.name,
                callback_data=f"category_{subcategory.id}"
            )
        ])
    
    # Добавляем кнопки товаров
    for product in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"{product.name} - {product.price}₽",
                callback_data=f"product_{product.id}"
            )
        ])
    
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
        
        buttons.append([
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"category_{back_id}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для карточки товара"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_to_cart_{product_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_category_{product_id}")]
    ])
    return keyboard

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отмена")]],
    resize_keyboard=True
)

def create_cart_keyboard(cart_items):
    """Создание клавиатуры для корзины"""
    keyboard = []
    
    # Добавляем кнопки для каждого товара
    for item in cart_items:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{item.product.name} ({item.quantity} шт.)", 
                callback_data=f"edit_cart_{item.id}"
            )
        ])
    
    # Добавляем кнопки управления корзиной
    if cart_items:  # Добавляем кнопки только если есть товары
        keyboard.extend([
            [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")]
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_cart_item_keyboard(item_id: int, quantity: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для редактирования товара в корзине"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data=f"cart_decrease_{item_id}"),
            InlineKeyboardButton(text=f"{quantity}", callback_data="ignore"),
            InlineKeyboardButton(text="➕", callback_data=f"cart_increase_{item_id}")
        ],
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"cart_remove_{item_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к корзине", callback_data="back_to_cart")]
    ])
    return keyboard

def create_delivery_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора способа доставки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚚 Курьером", callback_data="delivery_courier")],
        [InlineKeyboardButton(text="🏪 Самовывоз", callback_data="delivery_pickup")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
    ])
    return keyboard
