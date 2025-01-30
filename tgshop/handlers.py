from asgiref.sync import sync_to_async
from aiogram import Dispatcher, types
from aiogram.types import CallbackQuery
from aiogram.filters.command import Command as AiogramCommand
from aiogram import F
from tgshop.models.settings import TelegramSettings
from tgshop.models.operators import Operator
from tgshop.models.product import Product
from tgshop.keyboards import main_keyboard, catalog_keyboard, create_keyboard
from tgshop.models.category import Category

async def start_command(message: types.Message):
    """ Обработчик команды /start, отправляем основное меню """
    await message.answer(f"Привет, {message.from_user.first_name}! 👋", reply_markup=main_keyboard)

async def handle_catalog(message: types.Message):
    await message.answer(f"Воспользуйтесь кнопками ниже для навигации по каталогу",reply_markup=catalog_keyboard)

async def handle_cart(message: types.Message):
    """ Обработчик кнопки 'Корзина' """
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

async def handle_catalog_menu(message: types.Message):
    """ Обработчик кнопки 'Возврат к началу' """
    print(catalog_keyboard)
    await message.answer(f"Воспользуйтесь кнопками ниже для навигации по каталогу",reply_markup=catalog_keyboard)

async def product_callback_handler(callback: CallbackQuery):
    """ Обработчик нажатия на кнопку товара """
    product_id = int(callback.data.split("_")[1])  # Получаем ID товара

    product = await sync_to_async(Product.objects.get)(id=product_id)

    await callback.message.answer(f"Вы выбрали товар: {product.name}\nЦена: {product.price} ₽")

async def catalog_callback_handler(callback: CallbackQuery):
    """Обработчик инлайн-кнопок каталога"""
    
    # Обработка возврата в главное меню
    if callback.data == "category_main":
        await callback.message.edit_text(
            "Воспользуйтесь кнопками ниже для навигации по каталогу",
            reply_markup=catalog_keyboard
        )
        return

    category_id = int(callback.data.split("_")[1])  # Преобразуем в int
    
    # Получаем текущую категорию для отображения её названия
    current_category = await sync_to_async(Category.objects.get)(id=category_id)
    
    temp_keyboard = await sync_to_async(create_keyboard)(category_id)
    
    await callback.message.edit_text(
        f"Категория: {current_category.name}", 
        reply_markup=temp_keyboard
    )

def register_handlers(dp: Dispatcher):
    """ Функция для регистрации обработчиков """
    dp.message.register(start_command, AiogramCommand(commands=["start"]))
    dp.message.register(handle_catalog, F.text == "Каталог")
    dp.message.register(handle_cart, F.text == "Корзина")
    dp.message.register(handle_shippay, F.text == "Оплата и доставка")
    dp.message.register(handle_bonus, F.text == "Бонусная система")
    dp.message.register(handle_operator, F.text == "Связь с оператором")
    dp.message.register(handle_about, F.text == "О магазине")
    dp.callback_query.register(catalog_callback_handler, F.data.startswith("category_"))
    dp.callback_query.register(product_callback_handler, F.data.startswith("product_"))
    dp.callback_query.register(handle_catalog_menu, F.data == "catalog_menu")
    dp.message.register(handle_any_message)