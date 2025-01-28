from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Главная клавиатура
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Каталог"), KeyboardButton(text="Корзина")],
        [KeyboardButton(text="Оплата и доставка"), KeyboardButton(text="Бонусная система")],
        [KeyboardButton(text="Связь с оператором"), KeyboardButton(text="О магазине")],
    ],
    resize_keyboard=True
)