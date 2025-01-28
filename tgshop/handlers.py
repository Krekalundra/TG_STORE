from asgiref.sync import sync_to_async
from aiogram import Dispatcher, types
from aiogram.filters.command import Command as AiogramCommand
from aiogram import F
from tgshop.models.settings import TelegramSettings
from tgshop.models.operators import Operator
from tgshop.keyboards import main_keyboard

async def start_command(message: types.Message):
    """ Обработчик команды /start, отправляем основное меню """
    await message.answer(f"Привет, {message.from_user.first_name}! 👋", reply_markup=main_keyboard)

async def handle_catalog(message: types.Message):
    """ Обработчик кнопки 'Каталог """
    operator = await sync_to_async(Operator.load)()
    await message.answer("Здесь каталог магазина. Ты его не видишь, а он есть")

async def handle_cart(message: types.Message):
    """ Обработчик кнопки 'Корзина' """
    operator = await sync_to_async(Operator.load)()
    await message.answer("Здесь твоя корзина, с тебя 5000 уже списали")

async def handle_shippay(message: types.Message):
    """ Обработчик кнопки 'Оплата и доставка' """
    settings = await sync_to_async(TelegramSettings.load)()
    await message.answer(f"📦 {settings.ship_pay}")

async def handle_bonus(message: types.Message):
    """ Обработчик кнопки 'Бонусная система' """
    settings = await sync_to_async(TelegramSettings.load)()
    await message.answer(f"📦 {settings.bonus}")    

async def handle_operator(message: types.Message):
    """ Обработчик кнопки 'Связь с оператором' """
    operator = await sync_to_async(Operator.load)()
    await message.answer(f"Наш чайный эксперт Вам поможет:\n @{operator.username}")

async def handle_about(message: types.Message):
    """ Обработчик кнопки 'О магазине' """
    settings = await sync_to_async(TelegramSettings.load)()
    await message.answer(f"📦 {settings.about}")

async def handle_any_message(message: types.Message):
    """ Обработчик всех остальных сообщений, отправляем основное меню """
    await message.answer("Воспользуйтесь меню ниже:", reply_markup=main_keyboard)



def register_handlers(dp: Dispatcher):
    """ Функция для регистрации обработчиков """
    dp.message.register(start_command, AiogramCommand(commands=["start"]))
    dp.message.register(handle_catalog, F.text == "Каталог")
    dp.message.register(handle_cart, F.text == "Корзина")
    dp.message.register(handle_shippay, F.text == "Оплата и доставка")
    dp.message.register(handle_bonus, F.text == "Бонусная система")
    dp.message.register(handle_operator, F.text == "Связь с оператором")
    dp.message.register(handle_about, F.text == "О магазине")
    dp.message.register(handle_any_message)