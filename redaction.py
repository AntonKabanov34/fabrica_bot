from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InputFile
import config
import texts
import clases
import logging
import re

# Определение классов
DB = clases.DataBase(config.DB_NAME)
keyboard = clases.KeyBoard()

# Создание БД
DB.create_db()

# Telegram API
API_TOKEN = config.TOKEN

# Инициализация бота 
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()  # Используйте MemoryStorage для отладки
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if DB.user_exam(message.from_user.id):
        await bot.send_message(message.from_user.id, texts.restart, reply_markup=keyboard.get_inline_buttons())
    else:
        DB.add_new_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name, message.from_user.username)
        await bot.send_message(message.from_user.id, text=texts.start_text, reply_markup=keyboard.get_inline_buttons())


# Запуск бота!
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)