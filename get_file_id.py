from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import config

# Инициализация бота
API_TOKEN = config.TOKEN
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, "Привет! Отправь мне файл, и я верну его ID.")

# Обработчик загрузки документа
@dp.message_handler(content_types=[types.ContentType.DOCUMENT])
async def handle_document(message: types.Message):
    file_id = message.document.file_id
    file_name = message.document.file_name
    file_size = message.document.file_size
    
    await bot.send_message(message.chat.id, f"ID загруженного файла: {file_id}")
    await bot.send_message(message.chat.id, f"Имя файла: {file_name}")
    await bot.send_message(message.chat.id, f"Размер файла: {file_size} байт")

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)