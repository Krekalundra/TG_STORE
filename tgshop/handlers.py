from asgiref.sync import sync_to_async
from aiogram import Dispatcher, types
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, MenuButtonCommands, BotCommand, MenuButtonDefault, ReplyKeyboardMarkup, KeyboardButton
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
    create_cart_item_keyboard,
    create_delivery_keyboard
)
from tgshop.models.categories import Category
import os
from django.conf import settings
import logging
from tgshop.services.customer import CustomerService
from aiogram.fsm.context import FSMContext
from tgshop.states import AddToCartStates, OrderStates
from tgshop.services.cart import CartService
from tgshop.models.order import Order, OrderItem

# Глобальная переменная для отслеживания состояния каталога
catalog_states = {}  # user_id: last_catalog_message_id

async def start_command(message: types.Message):
    """ Обработчик команды /start """
    # Создаем или получаем покупателя
    get_or_create = sync_to_async(CustomerService.get_or_create_customer)
    customer, created = await get_or_create(
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
        customer = await sync_to_async(CustomerService.get_customer)(message.from_user.id)
        
        if not customer:
            await message.answer("❌ Для доступа к корзине необходимо начать диалог с ботом командой /start")
            return
            
        # Получаем корзину покупателя
        cart_service = CartService()
        cart = await cart_service.get_cart(customer)
        
        if not cart:
            await message.answer("🛒 Ваша корзина пуста", reply_markup=main_keyboard)
            return
            
        # Проверяем наличие товаров в корзине
        has_items = await sync_to_async(lambda: cart.items.exists())()
        if not has_items:
            await message.answer("🛒 Ваша корзина пуста", reply_markup=main_keyboard)
            return
            
        # Формируем сообщение с товарами
        cart_items = await sync_to_async(lambda: list(cart.items.select_related('product').all()))()
        
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
        cart_keyboard = await sync_to_async(create_cart_keyboard)(cart_items)
        
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
    try:
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
    except Exception as e:
        logging.error(f"Ошибка при показе товара: {e}")
        await callback.answer("Произошла ошибка при загрузке товара", show_alert=True)

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
        await cart_service.add_product(
            customer=customer,
            product=product,
            quantity=quantity
        )
        
        # Получаем обновленную корзину
        cart = await cart_service.get_cart(customer)
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
        cart_keyboard = await sync_to_async(create_cart_keyboard)(cart_items)
        
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
        cart = await cart_service.get_cart(customer)
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
        
        cart_keyboard = await sync_to_async(create_cart_keyboard)(cart_items)
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
        cart = await cart_service.get_cart(customer)
        
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

async def checkout_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия кнопки оформления заказа"""
    try:
        # Получаем данные покупателя
        customer = await sync_to_async(CustomerService.get_customer)(callback.from_user.id)
        if not customer:
            await callback.answer("Необходимо начать диалог с ботом командой /start", show_alert=True)
            return

        # Получаем корзину
        cart_service = CartService()
        cart = await cart_service.get_cart(customer)
        
        # Проверяем, есть ли товары в корзине
        cart_items = await sync_to_async(list)(cart.items.all())
        if not cart_items:
            await callback.answer("Корзина пуста!", show_alert=True)
            return

        # Проверяем наличие сохраненного телефона
        if customer.phone:
            # Если телефон есть, предлагаем использовать его или ввести новый
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Использовать текущий", callback_data="use_current_phone")],
                [InlineKeyboardButton(text="📝 Ввести новый", callback_data="enter_new_phone")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
            ])
            await callback.message.edit_text(
                f"📱 Использовать текущий номер телефона?\n"
                f"Текущий номер: {customer.phone}",
                reply_markup=keyboard
            )
        else:
            # Если телефона нет, переходим к его вводу
            cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
            ])
            await state.set_state(OrderStates.waiting_for_phone)
            await callback.message.edit_text(
                "📱 Введите ваш номер телефона в формате +7XXXXXXXXXX",
                reply_markup=cancel_keyboard
            )
        
    except Exception as e:
        logging.error(f"Ошибка при оформлении заказа: {e}")
        await callback.answer("Произошла ошибка при оформлении заказа", show_alert=True)

async def use_current_phone_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик использования текущего телефона"""
    try:
        customer = await sync_to_async(CustomerService.get_customer)(callback.from_user.id)
        await state.update_data(phone=customer.phone)
        await show_delivery_options(callback.message, state)
    except Exception as e:
        logging.error(f"Ошибка при использовании текущего телефона: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

async def enter_new_phone_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик ввода нового телефона"""
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
    ])
    await state.set_state(OrderStates.waiting_for_phone)
    await callback.message.edit_text(
        "📱 Введите новый номер телефона в формате +7XXXXXXXXXX",
        reply_markup=cancel_keyboard
    )

async def show_delivery_options(message: types.Message, state: FSMContext):
    """Показать варианты доставки"""
    customer = await sync_to_async(CustomerService.get_customer)(message.chat.id)
    
    # Создаем клавиатуру с вариантами доставки
    delivery_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 CDEK", callback_data="delivery_cdek")],
        [InlineKeyboardButton(text="📦 Boxberry", callback_data="delivery_boxberry")],
        [InlineKeyboardButton(text="📦 Почта РФ", callback_data="delivery_russian_post")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
    ])

    if customer.delivery_method and customer.address:
        # Если есть сохраненные данные доставки
        await message.answer(
            f"📦 Текущие данные доставки:\n"
            f"Способ: {customer.delivery_method}\n"
            f"Адрес: {customer.address}\n\n"
            f"Использовать текущие данные или выбрать новые?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Использовать текущие", callback_data="use_current_delivery")],
                [InlineKeyboardButton(text="📝 Выбрать новые", callback_data="select_new_delivery")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
            ])
        )
    else:
        await message.answer(
            "Выберите способ доставки:",
            reply_markup=delivery_keyboard
        )
    await state.set_state(OrderStates.waiting_for_delivery)

async def use_current_delivery_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик использования текущих данных доставки"""
    try:
        customer = await sync_to_async(CustomerService.get_customer)(callback.from_user.id)
        
        # Получаем текущие данные из состояния
        data = await state.get_data()
        
        # Обновляем данные состояния
        await state.update_data({
            **data,  # сохраняем существующие данные (например, телефон)
            'delivery_type': customer.delivery_method,
            'address': customer.address
        })
        
        # Показываем подтверждение заказа
        order_info = (
            "📋 Подтвердите заказ:\n\n"
            f"📱 Телефон: {data.get('phone')}\n"
            f"📦 Доставка: {customer.delivery_method}\n"
            f"📍 Адрес: {customer.address}\n"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")]
        ])
        
        await callback.message.edit_text(
            order_info,
            reply_markup=keyboard
        )
        
        # Переходим к состоянию ожидания комментария
        await state.set_state(OrderStates.waiting_for_comment)
        
        # Запрашиваем комментарий
        cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
        ])
        
        await callback.message.answer(
            "Введите комментарий к заказу (или отправьте 'нет'):",
            reply_markup=cancel_keyboard
        )
        
    except Exception as e:
        logging.error(f"Ошибка при использовании текущих данных доставки: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

async def select_new_delivery_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора новых данных доставки"""
    delivery_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 CDEK", callback_data="delivery_cdek")],
        [InlineKeyboardButton(text="📦 Boxberry", callback_data="delivery_boxberry")],
        [InlineKeyboardButton(text="📦 Почта РФ", callback_data="delivery_russian_post")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
    ])
    await callback.message.edit_text(
        "Выберите способ доставки:",
        reply_markup=delivery_keyboard
    )

async def proceed_to_comment(message: types.Message, state: FSMContext):
    """Переход к вводу комментария"""
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
    ])
    await state.set_state(OrderStates.waiting_for_comment)
    await message.answer(
        "Введите комментарий к заказу (или отправьте 'нет'):",
        reply_markup=cancel_keyboard
    )

async def handle_phone_input(message: types.Message, state: FSMContext):
    """Обработчик ввода телефона"""
    phone = message.text.strip()
    if not phone.startswith('+7') or len(phone) != 12 or not phone[1:].isdigit():
        await message.answer("❌ Неверный формат номера. Введите номер в формате +7XXXXXXXXXX")
        return

    # Сохраняем телефон в состоянии
    await state.update_data(phone=phone)
    
    # Обновляем телефон в профиле пользователя
    customer = await sync_to_async(CustomerService.get_customer)(message.from_user.id)
    customer.phone = phone
    await sync_to_async(customer.save)()
    
    # Переходим к выбору способа доставки
    await show_delivery_options(message, state)

async def handle_delivery_choice(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора способа доставки"""
    delivery_type = callback.data.split('_')[1]
    
    # Преобразуем технические названия в читаемые
    delivery_names = {
        'cdek': 'CDEK',
        'boxberry': 'Boxberry',
        'russian_post': 'Почта РФ'
    }
    
    delivery_name = delivery_names.get(delivery_type, delivery_type)
    await state.update_data(delivery_type=delivery_name)
    
    # Создаем inline клавиатуру для отмены
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
    ])
    
    await state.set_state(OrderStates.waiting_for_address)
    await callback.message.edit_text(
        "Введите адрес доставки:",
        reply_markup=cancel_keyboard
    )

async def handle_address_input(message: types.Message, state: FSMContext):
    """Обработчик ввода адреса"""
    address = message.text.strip()
    if len(address) < 10:
        await message.answer("❌ Адрес слишком короткий. Пожалуйста, введите полный адрес доставки")
        return

    # Сохраняем адрес в состоянии
    await state.update_data(address=address)
    
    # Обновляем адрес и способ доставки в профиле пользователя
    data = await state.get_data()
    customer = await sync_to_async(CustomerService.get_customer)(message.from_user.id)
    customer.address = address
    customer.delivery_method = data['delivery_type']
    await sync_to_async(customer.save)()
    
    # Переходим к вводу комментария
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
    ])
    
    await state.set_state(OrderStates.waiting_for_comment)
    await message.answer(
        "Введите комментарий к заказу (или отправьте 'нет'):",
        reply_markup=cancel_keyboard
    )

async def handle_comment_input(message: types.Message, state: FSMContext):
    """Обработчик ввода комментария"""
    comment = message.text.strip()
    if comment.lower() == 'нет':
        comment = ''
    
    data = await state.get_data()
    await state.update_data(comment=comment)
    
    # Показываем подтверждение заказа
    order_info = (
        "📋 Подтвердите заказ:\n\n"
        f"📱 Телефон: {data['phone']}\n"
        f"📦 Доставка: {data['delivery_type']}\n"
        f"📍 Адрес: {data['address']}\n"
        f"💭 Комментарий: {comment or 'нет'}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")]
    ])
    
    await message.answer(order_info, reply_markup=keyboard)

async def confirm_order_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик подтверждения заказа"""
    try:
        data = await state.get_data()
        customer = await sync_to_async(CustomerService.get_customer)(callback.from_user.id)
        
        # Создаем заказ
        cart_service = CartService()
        cart = await cart_service.get_cart(customer)
        cart_items = await sync_to_async(lambda: list(cart.items.select_related('product').all()))()
        
        total_amount = sum(item.quantity * item.product.price for item in cart_items)
        
        # Создаем заказ через lambda с добавлением delivery_method
        create_order = sync_to_async(lambda: Order.objects.create(
            customer=customer,
            total_amount=total_amount,
            delivery_address=data['address'],
            delivery_method=data['delivery_type'],
            comment=data.get('comment', '')
        ))
        order = await create_order()
        
        # Создаем позиции заказа через lambda
        for item in cart_items:
            create_order_item = sync_to_async(lambda: OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            ))
            await create_order_item()
        
        # Очищаем корзину через lambda
        clear_cart = sync_to_async(lambda: cart.items.all().delete())
        await clear_cart()
        
        # Формируем сообщение с подтверждением для клиента
        confirmation_text = (
            f"✅ Заказ #{order.id} успешно оформлен!\n\n"
            f"📱 Телефон: {data['phone']}\n"
            f"📦 Способ доставки: {data['delivery_type']}\n"
            f"📍 Адрес: {data['address']}\n"
            f"💰 Сумма заказа: {total_amount}₽\n\n"
            "Наш менеджер свяжется с вами в ближайшее время."
        )
        
        # Формируем уведомление для оператора
        operator_notification = (
            f"🔔 Новый заказ #{order.id}!\n\n"
            f"👤 Покупатель: {customer.first_name or ''} {customer.last_name or ''}\n"
            f"📱 Телефон: {data['phone']}\n"
            f"📦 Способ доставки: {data['delivery_type']}\n"
            f"📍 Адрес: {data['address']}\n\n"
            f"🛍 Состав заказа:\n"
        )
        
        for item in cart_items:
            item_price = item.product.price
            item_total = item.quantity * item_price
            operator_notification += (
                f"• {item.product.name}\n"
                f"  {item.quantity} x {item_price}₽ = {item_total}₽\n"
            )
        
        operator_notification += (
            f"\n💰 Итого: {total_amount}₽\n"
            f"💭 Комментарий: {data.get('comment', 'нет')}"
        )
        
        # Отправляем уведомление напрямую на указанный ID
        try:
            await callback.bot.send_message(
                chat_id=7900302595,  # ID аккаунта @chaika_tea
                text=operator_notification
            )
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления оператору: {e}")
        
        await state.clear()
        await callback.message.edit_text(confirmation_text)
        
    except Exception as e:
        logging.error(f"Ошибка при создании заказа: {e}")
        await callback.answer("Произошла ошибка при оформлении заказа", show_alert=True)
        await state.clear()

async def cancel_order_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик отмены заказа"""
    await state.clear()
    await callback.message.edit_text("❌ Оформление заказа отменено")

async def handle_profile(message: types.Message):
    """Обработчик кнопки 'Личный кабинет'"""
    await delete_catalog_if_exists(message)
    try:
        # Получаем данные покупателя
        customer = await sync_to_async(CustomerService.get_customer)(message.from_user.id)
        if not customer:
            await message.answer("❌ Для доступа к личному кабинету необходимо начать диалог с ботом командой /start")
            return

        # Получаем заказы пользователя
        get_orders = sync_to_async(lambda: list(customer.orders.all().order_by('-created_at')))
        orders = await get_orders()

        # Формируем сообщение с данными пользователя
        profile_text = "👤 Личный кабинет\n\n"
        profile_text += f"📱 Телефон: {customer.phone or 'Не указан'}\n"
        profile_text += f"📍 Адрес: {customer.address or 'Не указан'}\n"
        profile_text += f"🚚 Способ доставки: {customer.delivery_method or 'Не указан'}\n\n"

        if orders:
            profile_text += "📦 Ваши заказы:\n\n"
            for order in orders:
                profile_text += (
                    f"Заказ #{order.id} от {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Статус: {dict(Order.STATUS_CHOICES).get(order.status)}\n"
                    f"Сумма: {order.total_amount}₽\n"
                    f"Доставка: {order.delivery_method}\n"
                    "-------------------\n"
                )
        else:
            profile_text += "У вас пока нет заказов"

        await message.answer(profile_text)

    except Exception as e:
        logging.error(f"Ошибка при просмотре личного кабинета: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке личного кабинета",
            reply_markup=main_keyboard
        )

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
    dp.message.register(handle_profile, F.text == "Личный кабинет")
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
    dp.callback_query.register(checkout_callback, F.data == "checkout")
    
    # Добавляем обработчик для ввода количества товара
    dp.message.register(handle_quantity_input, AddToCartStates.waiting_for_quantity)
    
    # Оформление заказа
    dp.callback_query.register(use_current_phone_callback, F.data == "use_current_phone")
    dp.callback_query.register(enter_new_phone_callback, F.data == "enter_new_phone")
    dp.callback_query.register(use_current_delivery_callback, F.data == "use_current_delivery")
    dp.callback_query.register(select_new_delivery_callback, F.data == "select_new_delivery")
    dp.message.register(handle_phone_input, OrderStates.waiting_for_phone)
    dp.callback_query.register(handle_delivery_choice, F.data.startswith("delivery_"))
    dp.message.register(handle_address_input, OrderStates.waiting_for_address)
    dp.message.register(handle_comment_input, OrderStates.waiting_for_comment)
    dp.callback_query.register(confirm_order_callback, F.data == "confirm_order")
    dp.callback_query.register(cancel_order_callback, F.data == "cancel_order")
    
    # Регистрируем обработчик всех остальных сообщений последним
    dp.message.register(handle_any_message)

    # Добавляем обработчик личного кабинета
    dp.message.register(handle_profile, F.text == "Личный кабинет")