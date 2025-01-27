# tgshop/tgshop/bot.py

import os
import sys
import logging
import asyncio
from pathlib import Path
from asgiref.sync import sync_to_async
import django
from django.core.management.base import BaseCommand

# aiogram 3.x
from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.filters.command import Command as AiogramCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
# 1. Добавляем в sys.path (если нужно)
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# 2. Настраиваем переменную окружения под Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tgshop.config.settings')

# 3. Инициируем Django
try:
    django.setup()
except Exception as e:
    raise RuntimeError(f"Ошибка при настройке Django: {e}")

# 4. Импортируем модель с токеном
from tgshop.models.settings import TelegramSettings

# 5. Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotManager:
    def __init__(self, token: str):
        # В aiogram 3.x инициализируем бота и диспетчер
        self.bot = Bot(token=token)
        self.dp = Dispatcher(storage=MemoryStorage())

    async def on_startup(self):
        logger.info("🟢 Бот запущен и слушает сообщения...")

    async def start_command(self, message: types.Message):
        await message.answer(f"Привет, {message.from_user.first_name}! 👋")

    async def handle_any_message(self, message: types.Message):
        keyboard = create_reply_keyboard()
        await message.answer("Привет! Выберите действие:", reply_markup=keyboard)

    async def handle_catalog(self, message: types.Message):
    # Здесь логика вывода каталога
        settings = await sync_to_async(TelegramSettings.load)()
        await message.answer(f"Привет, {settings.about}! 👋")

def create_reply_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Каталог"), KeyboardButton(text="Корзина")],  # Одна кнопка в строке
            [KeyboardButton(text="Оплата и доставка"), KeyboardButton(text="Бонусная система")],  # Две кнопки в одной строке
            [KeyboardButton(text="Связь с оператором"), KeyboardButton(text="О магазине")], # Снова две кнопки в одной строке
        ],
        resize_keyboard=True  # Уменьшить размер клавиатуры
    )
    return keyboard


class Command(BaseCommand):
    """
    Django-команда для запуска Telegram-бота.
    Используйте: python -m tgshop.bot
    или создайте management command, если хотите run_bot в manage.py.
    """
    help = 'Запуск Telegram-бота'

    def handle(self, *args, **options):
        try:
            # Загружаем токен из БД (TelegramSettings с pk=1)
            settings = TelegramSettings.load()
            if not settings.token:
                logger.error("❌ Токен бота не найден! Добавьте его в админке.")
                return

            bot_manager = BotManager(token=settings.token)

            # Регистрация обработчиков
            #  - при старте (startup)
            bot_manager.dp.startup.register(bot_manager.on_startup)
            #  - команда /start
            bot_manager.dp.message.register(
                bot_manager.start_command,
                AiogramCommand(commands=["start"])
            )
            bot_manager.dp.message.register(
                bot_manager.handle_catalog,
                F.text == "Каталог"  # Обработчик команды "Каталог"
            )
            #  - любые другие сообщения
            bot_manager.dp.message.register(bot_manager.handle_any_message)

            # Асинхронный запуск
            async def main():
                await bot_manager.dp.start_polling(bot_manager.bot)

            asyncio.run(main())

        except Exception as e:
            logger.error(f"🔥 Ошибка: {e}")



if __name__ == "__main__":
    # Запуск напрямую: python tgshop/tgshop/bot.py
    # (или python -m tgshop.bot в корне проекта)
    Command().handle()