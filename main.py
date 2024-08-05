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

class Form(StatesGroup):
    name = State()
    email = State()

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if DB.user_exam(message.from_user.id):
        await bot.send_message(message.from_user.id, texts.restart, reply_markup=keyboard.get_inline_buttons())
    else:
        DB.add_new_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name, message.from_user.username)
        await bot.send_message(message.from_user.id, text=texts.start_text, reply_markup=keyboard.get_inline_buttons())

# Хендлер обработки файлId
@dp.message_handler(content_types=types.ContentTypes.DOCUMENT)
async def get_file_id(message: types.Message):
    file_id = message.document.file_id
    print(f"File ID: {file_id}")

# Хендлер для супер-пользователя
@dp.message_handler(text=[config.add_admin])
async def handle_message(message: types.Message):
    if message.text == config.admin:
        DB.add_god_admin(message.from_user.id)
        await bot.send_message(chat_id=message.from_user.id, text=texts.you_admin)

# Хендлер main_menu
@dp.message_handler(text=[texts.bot_info_button, texts.catalog_button, texts.ask_question_button])
async def handle_message(message: types.Message):  
    if message.text == texts.bot_info_button:
        await bot.send_message(chat_id=message.from_user.id, text='Это блок информации о боте!')
    elif message.text == texts.catalog_button:
        await bot.send_message(chat_id=message.from_user.id, text='Это кнопка которая дублирует отправку каталога!')
    elif message.text == texts.ask_question_button:
        await bot.send_message(chat_id=message.from_user.id, text='Это кнопка прямого вопроса!')

# Хендлер для inline
@dp.callback_query_handler(lambda c: c.data == config.contest_1)
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    # Здеь будет функция запроса контактной информации от пользователя 
    await bot.send_message(callback_query.from_user.id, text=texts.contest_info, reply_markup=keyboard.get_number_buttons())

# Обработчик запроса номера телефона  
@dp.message_handler(content_types=types.ContentTypes.CONTACT)
async def process_contact(message: types.Message):
    phone_number = message.contact.phone_number
    print(phone_number)
    await bot.send_message(message.from_user.id, text=texts.contest_ok, reply_markup=types.ReplyKeyboardRemove())


@dp.callback_query_handler(lambda c: c.data == config.catalog_1)
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_reply_markup(callback_query.from_user.id, callback_query.message.message_id, reply_markup=None)
    await bot.send_message(callback_query.from_user.id, text=texts.catalog_info_txt)
    await Form.name.set()
    await bot.send_message(callback_query.from_user.id, text=texts.catalog_name_txt)

@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text
    await state.update_data(name=name)
    
    if not DB.save_user_name(message.chat.id, name):
        await message.reply("Произошла странная ошибка. Пожалуйста, свяжитесь с администратором - @Hrassf")
        await state.finish()
        return
    
    await message.reply(f"Спасибо, {name}! Приятно познакомится!")
    await Form.email.set()
    await bot.send_message(message.from_user.id, text=texts.catalog_mail_txt)

@dp.message_handler(state=Form.email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await message.reply("Некорректный email. Пожалуйста, введите корректный email.")
        return
    
    await state.update_data(email=email)
    data = await state.get_data()
    
    if not DB.save_user_email(message.chat.id, email):
        await message.reply("Произошла странная ошибка. Пожалуйста, свяжитесь с администратором - @Hrassf")
        await state.finish()
        return
    
    #Поменять текст
    await message.reply(f"Спасибо, {data['name']}! Ваш email {email} сохранен. Отправляем вам каталог!")
    #Отправляем файл каталога с помощью FILE_ID
    await message.answer_document(document=config.CATALOG_FILE_ID)
    await state.finish()

# Запуск бота!
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)