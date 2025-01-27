# tgshop/tgshop/bot.py

import os
import sys
import logging
import asyncio
from pathlib import Path

import django
from django.core.management.base import BaseCommand

# aiogram 3.x
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command as AiogramCommand
from aiogram.fsm.storage.memory import MemoryStorage

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
        await message.answer("Не понял вас, я просто бот 🤖")


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