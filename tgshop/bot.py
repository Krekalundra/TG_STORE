#tgshop/tgshop/bot.py

import os
import sys
import django
import logging
import asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from django.core.management.base import BaseCommand
# Добавляем корень проекта в sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Инициализация Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tgshop.config.settings')
django.setup()

from tgshop.models.settings import TelegramSettings

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self.bot = None
        self.dp = None

    async def on_startup(self):
        logger.info("🟢 Бот запущен и слушает сообщения...")

    async def start_command(self, message: types.Message):
        await message.answer(f"Привет, {message.from_user.first_name}! 👋")

    async def handle_any_message(self, message: types.Message):
        await message.answer("Не понял вас, я просто бот 🤖")

class Command(BaseCommand):
    help = 'Запуск Telegram-бота'

    def handle(self, *args, **options):
        try:
            settings = TelegramSettings.load()
            if not settings.token:
                logger.error("❌ Токен бота не найден! Добавьте его в админке.")
                return

            bot_manager = BotManager()
            bot_manager.bot = Bot(token=settings.token)
            bot_manager.dp = Dispatcher()

            # Регистрация обработчиков
            bot_manager.dp.startup.register(bot_manager.on_startup)
            bot_manager.dp.message.register(bot_manager.start_command, Command(commands=['start']))
            bot_manager.dp.message.register(bot_manager.handle_any_message)

            # Запуск бота
            async def main():
                await bot_manager.dp.start_polling(bot_manager.bot)

            asyncio.run(main())

        except Exception as e:
            logger.error(f"🔥 Ошибка: {e}")

if __name__ == "__main__":
    # Запуск через python3 bot.py (без использования Django-команд)
    Command().handle()