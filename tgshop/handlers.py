from asgiref.sync import sync_to_async
from aiogram import Dispatcher, types
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, MenuButtonCommands, BotCommand, MenuButtonDefault
from aiogram.filters.command import Command as AiogramCommand
from aiogram import F
from tgshop.models.settings import TelegramSettings
from tgshop.models.operators import Operator
from tgshop.models.product import Product
from tgshop.models.cart import CartItem
from tgshop.keyboards import (
    main_keyboard, 
    catalog_keyboard, 
    create_keyboard, 
    create_product_keyboard,
    cancel_keyboard,
    create_cart_keyboard,
    create_cart_item_keyboard
)
from tgshop.models.categories import Category
import os
from django.conf import settings
import logging
from tgshop.services.customer import CustomerService
from aiogram.fsm.context import FSMContext
from tgshop.states import AddToCartStates
from tgshop.services.cart import CartService

# Глобальная переменная для отслеживания состояния каталога
catalog_states = {}  # user_id: last_catalog_message_id

async def start_command(message: types.Message):
    """ Обработчик команды /start """
    # Создаем или получаем покупателя
    customer_service = CustomerService()
    customer, created = await sync_to_async(customer_service.get_or_create_customer)(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Устанавливаем пустое меню (скрываем)
    await message.bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=MenuButtonDefault()
    )
    
    # Очищаем список команд в меню
    await message.bot.delete_my_commands()
    
    # Формируем приветственное сообщение
    greeting = "С возвращением" if not created else "Добро пожаловать"
    
    # Возвращаем reply-клавиатуру
    await message.answer(
        f"{greeting}, {message.from_user.first_name}! 👋\n"
        f"Используйте кнопки ниже для навигации:", 
        reply_markup=main_keyboard
    )

async def handle_catalog(message: types.Message):
    """Обработчик кнопки 'Каталог'"""
    await delete_catalog_if_exists(message)
    try:
        # Отправляем сообщение с каталогом
        catalog_message = await message.answer(
            "Воспользуйтесь кнопками ниже для навигации по каталогу",
            reply_markup=catalog_keyboard
        )
        # Сохраняем id сообщения каталога для этого пользователя
        catalog_states[message.from_user.id] = catalog_message.message_id
        
    except Exception as e:
        logging.error(f"Ошибка при показе каталога: {e}")
        await message.answer("Произошла ошибка", reply_markup=main_keyboard)

async def delete_catalog_if_exists(message: types.Message):
    """Вспомогательная функция для удаления сообщения каталога"""
    if message.from_user.id in catalog_states:
        try:
            await message.bot.delete_message(
                message.chat.id,
                catalog_states[message.from_user.id]
            )
        except Exception as e:
            logging.error(f"Ошибка при удалении сообщения каталога: {e}")
        del catalog_states[message.from_user.id]

async def handle_cart(message: types.Message):
    """Обработчик кнопки 'Корзина'"""
    await delete_catalog_if_exists(message)
    try:
        # Получаем покупателя
        customer_service = CustomerService()
        customer = await sync_to_async(customer_service.get_customer)(message.from_user.id)
        
        if not customer:
            await message.answer("❌ Для доступа к корзине необходимо начать диалог с ботом командой /start")
            return
            
        # Получаем корзину покупателя
        cart_service = CartService()
        cart = await sync_to_async(cart_service.get_cart)(customer)
        
        if not cart or not await sync_to_async(lambda: cart.items.exists())():
            await message.answer("🛒 Ваша корзина пуста", reply_markup=main_keyboard)
            return
            
        # Формируем сообщение с товарами
        cart_items = await sync_to_async(list)(cart.items.select_related('product').all())
        
        cart_text = "🛒 Ваша корзина:\n\n"
        total = 0
        
        for item in cart_items:
            product = item.product
            item_cost = item.quantity * product.price
            total += item_cost
            
            cart_text += (
                f"• {product.name}\n"
                f"  {item.quantity} x {product.price}₽ = {item_cost}₽\n"
            )
        
        cart_text += f"\n💰 Итого: {total}₽\n\n"
        cart_text += "Нажмите на товар для изменения количества"
        
        # Создаем клавиатуру для корзины
        cart_keyboard = create_cart_keyboard(cart_items)
        
        # Отправляем сообщение с содержимым корзины и кнопками
        await message.answer(
            cart_text, 
            reply_markup=cart_keyboard
        )
        
    except Exception as e:
        logging.error(f"Ошибка при просмотре корзины: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке корзины",
            reply_markup=main_keyboard
        )

async def handle_shippay(message: types.Message):
    """Обработчик кнопки 'Оплата и доставка'"""
    await delete_catalog_if_exists(message)
    settings = await sync_to_async(TelegramSettings.load)()
    await message.answer(f"📦 {settings.ship_pay}")

async def handle_bonus(message: types.Message):
    """Обработчик кнопки 'Бонусная система'"""
    await delete_catalog_if_exists(message)
    settings = await sync_to_async(TelegramSettings.load)()
    await message.answer(f"�� {settings.bonus}")    

async def handle_operator(message: types.Message):
    """Обработчик кнопки 'Связь с оператором'"""
    await delete_catalog_if_exists(message)
    operator = await sync_to_async(Operator.load)()
    await message.answer(f"Наш чайный эксперт Вам поможет:\n @{operator.username}")

async def handle_about(message: types.Message):
    """Обработчик кнопки 'О магазине'"""
    await delete_catalog_if_exists(message)
    settings = await sync_to_async(TelegramSettings.load)()
    await message.answer(f"📦 {settings.about}")

async def handle_any_message(message: types.Message, state: FSMContext):
    """ Обработчик всех остальных сообщений """
    # Проверяем, не находимся ли мы в состоянии ожидания ввода
    current_state = await state.get_state()
    if current_state is not None:
        return  # Если в состоянии ожидания, не показываем сообщение о меню
        
    # Проверяем существование покупателя
    customer_service = CustomerService()
    customer = await sync_to_async(customer_service.get_customer)(message.from_user.id)
    
    if not customer:
        # Если покупателя нет, создаем его
        customer, _ = await sync_to_async(customer_service.get_or_create_customer)(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
    
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
    product_keyboard = create_product_keyboard(product_id)
    
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

async def handle_quantity_input(message: types.Message, state: FSMContext):
    """Обработчик ввода количества товара"""
    if message.text == "Отмена":
        # Получаем данные из состояния
        data = await state.get_data()
        quantity_message_id = data.get('quantity_message_id')
        category_id = data.get('category_id')
        
        # Удаляем сообщение с запросом количества
        if quantity_message_id:
            try:
                await message.bot.delete_message(message.chat.id, quantity_message_id)
            except Exception as e:
                logging.error(f"Ошибка при удалении сообщения: {e}")
        
        # Возвращаем основную клавиатуру и показываем категорию
        if category_id:
            current_category = await sync_to_async(Category.objects.get)(id=category_id)
            category_keyboard = await sync_to_async(create_keyboard)(category_id)
            await message.answer(
                f"Категория: {current_category.name}",
                reply_markup=main_keyboard  # Возвращаем основную reply клавиатуру
            )
            # Отдельно отправляем inline клавиатуру категории и сохраняем ID сообщения
            catalog_message = await message.answer(
                "Выберите товар:",
                reply_markup=category_keyboard
            )
            # Сохраняем id сообщения каталога
            catalog_states[message.from_user.id] = catalog_message.message_id
        
        await state.clear()
        return

    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным")
            
        data = await state.get_data()
        product_id = data.get('product_id')
        category_id = data.get('category_id')
        quantity_message_id = data.get('quantity_message_id')
        
        if not product_id:
            raise ValueError("Не найден ID товара")
            
        # Получаем товар и покупателя
        product = await sync_to_async(Product.objects.get)(id=product_id)
        customer = await sync_to_async(CustomerService.get_customer)(message.from_user.id)
        
        if not customer:
            raise ValueError("Покупатель не найден")
            
        # Добавляем в корзину
        cart_service = CartService()
        await sync_to_async(cart_service.add_product)(
            customer=customer,
            product=product,
            quantity=quantity
        )
        
        # Получаем обновленную корзину
        cart = await sync_to_async(cart_service.get_cart)(customer)
        cart_items = await sync_to_async(list)(cart.items.select_related('product').all())
        
        # Формируем сообщение о добавлении и составе корзины
        message_text = (
            f"✅ Добавлено в корзину:\n"
            f"• {product.name} - {quantity} шт. × {product.price}₽ = {quantity * product.price}₽\n\n"
            f"🛒 Текущий состав корзины:\n"
        )
        
        total = 0
        for item in cart_items:
            item_cost = item.quantity * item.product.price
            total += item_cost
            message_text += f"• {item.product.name} - {item.quantity} шт. × {item.product.price}₽ = {item_cost}₽\n"
        
        message_text += f"\n💰 Итого: {total}₽"
        
        # Удаляем сообщение с запросом количества
        if quantity_message_id:
            try:
                await message.bot.delete_message(message.chat.id, quantity_message_id)
            except Exception as e:
                logging.error(f"Ошибка при удалении сообщения: {e}")
        
        await state.clear()
        
        # Отправляем сообщение с информацией о корзине
        await message.answer(
            message_text,
            reply_markup=main_keyboard
        )
        
        # Показываем категорию с inline клавиатурой
        if category_id:
            current_category = await sync_to_async(Category.objects.get)(id=category_id)
            category_keyboard = await sync_to_async(create_keyboard)(category_id)
            catalog_message = await message.answer(
                f"Категория: {current_category.name}",
                reply_markup=category_keyboard
            )
            # Сохраняем id сообщения каталога
            catalog_states[message.from_user.id] = catalog_message.message_id
        
    except ValueError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=cancel_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при добавлении в корзину: {e}")
        await message.answer(
            "❌ Произошла ошибка при добавлении товара в корзину",
            reply_markup=cancel_keyboard
        )
        await state.clear()

async def add_to_cart_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия кнопки 'Добавить в корзину'"""
    try:
        # Получаем и сохраняем данные
        parts = callback.data.split("_")
        product_id = int(parts[-1])
        
        product = await sync_to_async(Product.objects.get)(id=product_id)
        category_id = await sync_to_async(lambda: product.category.id)()
        
        await state.update_data(product_id=product_id)
        await state.update_data(category_id=category_id)
        
        # Убираем кнопки под сообщением с товаром
        await callback.message.edit_reply_markup(reply_markup=None)
        
        # Отправляем сообщение с запросом количества, меняем reply клавиатуру на cancel_keyboard
        msg = await callback.message.answer(
            "Введите количество товара:",
            reply_markup=cancel_keyboard  # Заменяем основную клавиатуру на cancel_keyboard
        )
        
        await state.update_data(quantity_message_id=msg.message_id)
        await state.set_state(AddToCartStates.waiting_for_quantity)
        await callback.answer()
        
    except Exception as e:
        logging.error(f"Ошибка при обработке callback_data: {e}")
        await callback.answer("Произошла ошибка при добавлении в корзину", show_alert=True)

async def edit_cart_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия на товар в корзине"""
    try:
        item_id = int(callback.data.split("_")[2])
        cart_item = await sync_to_async(CartItem.objects.select_related('product').get)(id=item_id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬇️", callback_data=f"cart_decrease_{item_id}"),
                InlineKeyboardButton(text=str(cart_item.quantity), callback_data="ignore"),
                InlineKeyboardButton(text="⬆️", callback_data=f"cart_increase_{item_id}")
            ],
            [InlineKeyboardButton(text="❌ Удалить", callback_data=f"cart_remove_{item_id}")],
            [InlineKeyboardButton(text="⬅️ Назад к корзине", callback_data="back_to_cart")]
        ])
        
        await callback.message.edit_text(
            f"🛒 {cart_item.product.name}\n"
            f"Количество: {cart_item.quantity} шт\n"
            f"Цена за шт: {cart_item.product.price}₽\n"
            f"Итого: {cart_item.quantity * cart_item.product.price}₽\n\n"
            f"Выберите действие:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logging.error(f"Ошибка при редактировании товара в корзине: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

async def cart_increase_callback(callback: CallbackQuery):
    """Увеличить количество товара"""
    try:
        item_id = int(callback.data.split("_")[2])
        cart_item = await sync_to_async(CartItem.objects.select_related('product').get)(id=item_id)
        
        # Увеличиваем количество
        cart_item.quantity += 1
        await sync_to_async(cart_item.save)()
        
        # Получаем обновленные данные
        cart_item = await sync_to_async(CartItem.objects.select_related('product').get)(id=item_id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬇️", callback_data=f"cart_decrease_{item_id}"),
                InlineKeyboardButton(text=str(cart_item.quantity), callback_data="ignore"),
                InlineKeyboardButton(text="⬆️", callback_data=f"cart_increase_{item_id}")
            ],
            [InlineKeyboardButton(text="❌ Удалить", callback_data=f"cart_remove_{item_id}")],
            [InlineKeyboardButton(text="⬅️ Назад к корзине", callback_data="back_to_cart")]
        ])
        
        await callback.message.edit_text(
            f"🛒 {cart_item.product.name}\n"
            f"Количество: {cart_item.quantity} шт\n"
            f"Цена за шт: {cart_item.product.price}₽\n"
            f"Итого: {cart_item.quantity * cart_item.product.price}₽\n\n"
            f"Выберите действие:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logging.error(f"Ошибка при увеличении количества: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

async def cart_decrease_callback(callback: CallbackQuery):
    """Уменьшить количество товара"""
    try:
        item_id = int(callback.data.split("_")[2])
        cart_item = await sync_to_async(CartItem.objects.select_related('product').get)(id=item_id)
        
        if cart_item.quantity > 1:
            # Уменьшаем количество
            cart_item.quantity -= 1
            await sync_to_async(cart_item.save)()
            
            # Получаем обновленные данные
            cart_item = await sync_to_async(CartItem.objects.select_related('product').get)(id=item_id)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="⬇️", callback_data=f"cart_decrease_{item_id}"),
                    InlineKeyboardButton(text=str(cart_item.quantity), callback_data="ignore"),
                    InlineKeyboardButton(text="⬆️", callback_data=f"cart_increase_{item_id}")
                ],
                [InlineKeyboardButton(text="❌ Удалить", callback_data=f"cart_remove_{item_id}")],
                [InlineKeyboardButton(text="⬅️ Назад к корзине", callback_data="back_to_cart")]
            ])
            
            await callback.message.edit_text(
                f"🛒 {cart_item.product.name}\n"
                f"Количество: {cart_item.quantity} шт\n"
                f"Цена за шт: {cart_item.product.price}₽\n"
                f"Итого: {cart_item.quantity * cart_item.product.price}₽\n\n"
                f"Выберите действие:",
                reply_markup=keyboard
            )
        else:
            await callback.answer("Для удаления товара используйте кнопку ❌", show_alert=True)
            
    except Exception as e:
        logging.error(f"Ошибка при уменьшении количества: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

async def cart_remove_callback(callback: CallbackQuery):
    """Удалить товар из корзины"""
    try:
        item_id = int(callback.data.split("_")[2])
        
        # Получаем товар и корзину
        get_item = sync_to_async(CartItem.objects.select_related('product', 'cart').get)
        cart_item = await get_item(id=item_id)
        cart = cart_item.cart
        
        # Удаляем товар через sync_to_async с lambda
        delete_item = sync_to_async(lambda: CartItem.objects.filter(id=item_id).delete())
        await delete_item()
        
        # Получаем обновленный список товаров через sync_to_async с lambda
        get_items = sync_to_async(lambda: list(cart.items.select_related('product').all()))
        cart_items = await get_items()
        
        if not cart_items:
            await callback.message.edit_text("🛒 Ваша корзина пуста")
            return
            
        # Формируем сообщение с обновленной корзиной
        cart_text = "🛒 Ваша корзина:\n\n"
        total = 0
        
        for item in cart_items:
            product = item.product
            item_cost = item.quantity * product.price
            total += item_cost
            cart_text += (
                f"• {product.name}\n"
                f"  {item.quantity} x {product.price}₽ = {item_cost}₽\n"
            )
        
        cart_text += f"\n💰 Итого: {total}₽\n\n"
        cart_text += "Нажмите на товар для изменения количества"
        
        # Создаем клавиатуру для обновленной корзины
        cart_keyboard = create_cart_keyboard(cart_items)
        
        await callback.message.edit_text(
            cart_text,
            reply_markup=cart_keyboard
        )
        
    except Exception as e:
        logging.error(f"Ошибка при удалении товара: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

async def back_to_cart_callback(callback: CallbackQuery):
    """Вернуться к просмотру корзины"""
    try:
        customer = await sync_to_async(CustomerService.get_customer)(callback.from_user.id)
        cart_service = CartService()
        cart = await sync_to_async(cart_service.get_cart)(customer)
        cart_items = await sync_to_async(list)(cart.items.select_related('product').all())
        
        if not cart_items:
            await callback.message.edit_text("🛒 Ваша корзина пуста")
            return
            
        cart_text = "🛒 Ваша корзина:\n\n"
        total = 0
        
        for item in cart_items:
            product = item.product
            item_cost = item.quantity * product.price
            total += item_cost
            cart_text += (
                f"• {product.name}\n"
                f"  {item.quantity} x {product.price}₽ = {item_cost}₽\n"
            )
        
        cart_text += f"\n💰 Итого: {total}₽\n\n"
        cart_text += "Нажмите на товар для изменения количества"
        
        cart_keyboard = create_cart_keyboard(cart_items)
        await callback.message.edit_text(cart_text, reply_markup=cart_keyboard)
        
    except Exception as e:
        logging.error(f"Ошибка при возврате к корзине: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

async def clear_cart_callback(callback: CallbackQuery):
    """Очистить корзину"""
    try:
        # Получаем покупателя и его корзину
        customer = await sync_to_async(CustomerService.get_customer)(callback.from_user.id)
        cart_service = CartService()
        cart = await sync_to_async(cart_service.get_cart)(customer)
        
        if cart:
            # Удаляем все товары из корзины
            await sync_to_async(cart.items.all().delete)()
            
            # Отправляем сообщение об успешной очистке
            await callback.message.edit_text("🛒 Корзина очищена")
        else:
            await callback.message.edit_text("🛒 Ваша корзина пуста")
            
    except Exception as e:
        logging.error(f"Ошибка при очистке корзины: {e}")
        await callback.answer("Произошла ошибка при очистке корзины", show_alert=True)

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
    
    # Обработчики текстовых команд
    dp.message.register(handle_catalog, F.text == "Каталог")
    dp.message.register(handle_cart, F.text == "Корзина")
    dp.message.register(handle_shippay, F.text == "Оплата и доставка")
    dp.message.register(handle_bonus, F.text == "Бонусная система")
    dp.message.register(handle_operator, F.text == "Связь с оператором")
    dp.message.register(handle_about, F.text == "О магазине")
    
    # Обработчики для callback-запросов
    dp.callback_query.register(catalog_callback_handler, F.data.startswith("category_"))
    dp.callback_query.register(product_callback_handler, F.data.startswith("product_"))
    dp.callback_query.register(handle_catalog_menu, F.data == "catalog_menu")
    dp.callback_query.register(back_to_category_handler, F.data.startswith("back_to_category_"))
    dp.callback_query.register(add_to_cart_callback, F.data.startswith("add_to_cart_"))
    dp.callback_query.register(edit_cart_callback, F.data.startswith("edit_cart_"))
    
    # Обработчики для корзины
    dp.callback_query.register(cart_increase_callback, F.data.startswith("cart_increase_"))
    dp.callback_query.register(cart_decrease_callback, F.data.startswith("cart_decrease_"))
    dp.callback_query.register(cart_remove_callback, F.data.startswith("cart_remove_"))
    dp.callback_query.register(back_to_cart_callback, F.data == "back_to_cart")
    dp.callback_query.register(clear_cart_callback, F.data == "clear_cart")
    
    # Добавляем обработчик для ввода количества товара
    dp.message.register(handle_quantity_input, AddToCartStates.waiting_for_quantity)
    
    # Регистрируем обработчик всех остальных сообщений последним
    dp.message.register(handle_any_message)