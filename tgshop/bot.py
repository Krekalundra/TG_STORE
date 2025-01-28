import os
import sys
import logging
import asyncio
from pathlib import Path
import django
from django.core.management.base import BaseCommand

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tgshop.config.settings')

try:
    django.setup()
except Exception as e:
    raise RuntimeError(f"Ошибка при настройке Django: {e}")

# Импортируем обработчики и настройки
from tgshop.models.settings import TelegramSettings
from tgshop.handlers import register_handlers  # Функция для подключения обработчиков

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """ Django-команда для запуска Telegram-бота. """

    help = "Запуск Telegram-бота"

    def handle(self, *args, **options):
        try:
            # Загружаем токен из БД
            settings = TelegramSettings.load()
            if not settings.token:
                logger.error("❌ Токен бота не найден! Добавьте его в админке.")
                return

            bot = Bot(token=settings.token)
            dp = Dispatcher(storage=MemoryStorage())

            # Подключаем обработчики
            register_handlers(dp)

            async def main():
                logger.info("🟢 Бот запущен и слушает сообщения...")
                await dp.start_polling(bot)

            asyncio.run(main())

        except Exception as e:
            logger.error(f"🔥 Ошибка: {e}")

if __name__ == "__main__":
    Command().handle()