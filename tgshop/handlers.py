from asgiref.sync import sync_to_async
from aiogram import Dispatcher, types
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, MenuButtonCommands, BotCommand, MenuButtonDefault
from aiogram.filters.command import Command as AiogramCommand
from aiogram import F
from tgshop.models.settings import TelegramSettings
from tgshop.models.operators import Operator
from tgshop.models.product import Product
from tgshop.keyboards import main_keyboard, catalog_keyboard, create_keyboard, create_product_keyboard
from tgshop.models.categories import Category
import os
from django.conf import settings
import logging

async def start_command(message: types.Message):
    """ Обработчик команды /start """
    # Устанавливаем пустое меню (скрываем)
    await message.bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=MenuButtonDefault()
    )
    
    # Очищаем список команд в меню
    await message.bot.delete_my_commands()
    
    # Возвращаем reply-клавиатуру
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        f"Используйте кнопки ниже для навигации:", 
        reply_markup=main_keyboard
    )

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
    """Обработчик нажатия на кнопку товара"""
    # Удаляем сообщение с каталогом
    await callback.message.delete()
    
    product_id = int(callback.data.split("_")[1])
    
    # Получаем товар и его изображения
    product = await sync_to_async(Product.objects.select_related('category').get)(id=product_id)
    images = await sync_to_async(list)(product.images.all())
    
    # Формируем текст описания
    product_text = (
        f"📦 *{product.name}*\n\n"
        f"💰 Цена: {product.price} ₽"
        f"{' за грамм' if product.price_type == 'gram' else ''}\n\n"
        f"📝 Описание:\n{product.dis_product}\n\n"
    )
    
    # Создаём клавиатуру для товара
    product_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_to_cart_{product_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_category_{product.category.id}")]
    ])
    
    if images:
        try:
            # Находим обложку
            cover_image = next((img for img in images if img.is_cover), images[0])
            cover_path = os.path.join(settings.MEDIA_ROOT, str(cover_image.image))
            
            # Получаем остальные фотографии (исключая обложку)
            other_images = [img for img in images if img != cover_image]
            
            
            # Если есть дополнительные фотографии, отправляем их альбомом
            if other_images:
                media_group = []
                for image in other_images:
                    image_path = os.path.join(settings.MEDIA_ROOT, str(image.image))
                    media_group.append(InputMediaPhoto(media=FSInputFile(image_path)))
                await callback.message.answer_media_group(media=media_group)
            
            # Отправляем сообщение с обложкой, описанием и кнопками
            await callback.message.answer_photo(
                photo=FSInputFile(cover_path),
                caption=product_text,
                reply_markup=product_keyboard,
                parse_mode="Markdown"
            )
            
        except FileNotFoundError as e:
            logging.error(f"Файл не найден: {e}")
            await callback.message.answer(
                text=f"{product_text}\n\n❌ Изображения недоступны",
                reply_markup=product_keyboard,
                parse_mode="Markdown"
            )
    else:
        await callback.message.answer(
            text=product_text,
            reply_markup=product_keyboard,
            parse_mode="Markdown"
        )

async def back_to_category_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' в карточке товара"""
    category_id = int(callback.data.split("_")[3])
    
    # Удаляем кнопки у карточки товара
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Получаем текущую категорию
    current_category = await sync_to_async(Category.objects.get)(id=category_id)
    
    # Создаем клавиатуру для категории
    category_keyboard = await sync_to_async(create_keyboard)(category_id)
    
    # Отправляем новое сообщение с категорией
    await callback.message.answer(
        f"Категория: {current_category.name}",
        reply_markup=category_keyboard
    )

async def catalog_callback_handler(callback: CallbackQuery):
    """Обработчик инлайн-кнопок каталога"""
    
    # Удаляем сообщение, под которым была нажата кнопка
    await callback.message.delete()
    
    # Обработка возврата в главное меню
    if callback.data == "category_main":
        await callback.message.answer(
            "Воспользуйтесь кнопками ниже для навигации по каталогу",
            reply_markup=catalog_keyboard
        )
        return

    category_id = int(callback.data.split("_")[1])
    
    # Получаем текущую категорию для отображения её названия
    current_category = await sync_to_async(Category.objects.get)(id=category_id)
    
    # Создаем клавиатуру для текущей категории
    temp_keyboard = await sync_to_async(create_keyboard)(category_id)
    
    # Отправляем новое сообщение с актуальной категорией
    await callback.message.answer(
        f"Категория: {current_category.name}", 
        reply_markup=temp_keyboard
    )

# Добавляем обработчики цифровых команд
async def command_1(message: types.Message):
    await handle_catalog(message)

async def command_2(message: types.Message):
    await handle_cart(message)

async def command_3(message: types.Message):
    await handle_shippay(message)

async def command_4(message: types.Message):
    await handle_bonus(message)

async def command_5(message: types.Message):
    await handle_operator(message)

async def command_6(message: types.Message):
    await handle_about(message)

def register_handlers(dp: Dispatcher):
    """ Функция для регистрации обработчиков """
    dp.message.register(start_command, AiogramCommand(commands=["start"]))
    
    # Регистрируем цифровые команды
    dp.message.register(command_1, AiogramCommand(commands=["1"]))
    dp.message.register(command_2, AiogramCommand(commands=["2"]))
    dp.message.register(command_3, AiogramCommand(commands=["3"]))
    dp.message.register(command_4, AiogramCommand(commands=["4"]))
    dp.message.register(command_5, AiogramCommand(commands=["5"]))
    dp.message.register(command_6, AiogramCommand(commands=["6"]))
    
    # Оставляем существующие обработчики текстовых команд
    dp.message.register(handle_catalog, F.text == "Каталог")
    dp.message.register(handle_cart, F.text == "Корзина")
    dp.message.register(handle_shippay, F.text == "Оплата и доставка")
    dp.message.register(handle_bonus, F.text == "Бонусная система")
    dp.message.register(handle_operator, F.text == "Связь с оператором")
    dp.message.register(handle_about, F.text == "О магазине")
    
    # Оставляем обработчики для callback-запросов
    dp.callback_query.register(catalog_callback_handler, F.data.startswith("category_"))
    dp.callback_query.register(product_callback_handler, F.data.startswith("product_"))
    dp.callback_query.register(handle_catalog_menu, F.data == "catalog_menu")
    dp.callback_query.register(back_to_category_handler, F.data.startswith("back_to_category_"))
    dp.message.register(handle_any_message)