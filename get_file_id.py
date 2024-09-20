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

# Обработчик загрузки GIF-файла
@dp.message_handler(content_types=[types.ContentType.ANIMATION])
async def handle_animation(message: types.Message):
    file_id = message.animation.file_id
    file_name = message.animation.file_name
    file_size = message.animation.file_size
    
    await bot.send_message(message.chat.id, f"ID загруженного GIF-файла: {file_id}")
    await bot.send_message(message.chat.id, f"Имя файла: {file_name}")
    await bot.send_message(message.chat.id, f"Размер файла: {file_size} байт")

@dp.message_handler(content_types=types.ContentType.STICKER)
async def get_sticker_id(message: types.Message):
    sticker_id = message.sticker.file_id
    print(f"Sticker file_id: {sticker_id}")

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def get_photo_id(message: types.Message):
    # Получаем file_id последнего (самого большого) фото в сообщении
    photo_id = message.photo[-1].file_id
    print(f"Photo file_id: {photo_id}")

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)