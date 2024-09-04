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

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Определение классов
DB = clases.DataBase(config.DB_NAME)
keyboard = clases.KeyBoard()

# Создание БД
DB.create_db()
DB.add_god(config.GOD_ID)

# Telegram API
API_TOKEN = config.TOKEN

# Инициализация бота 
bot = Bot(token=API_TOKEN)
storage = MemoryStorage() 
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

class UserForm(StatesGroup):
    name = State()
    company = State()
    job_title = State()
    email = State()
    phone = State()
    confirmation = State()


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    #Проверяем есть ли пользователь в БД, если нет - добавляем
    if DB.chek_users(message.from_user.id) == False:
        DB.post_new_users(message.from_user.id)
        DB.post_users_info(message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
        await bot.send_message(message.from_user.id, "Тебя нет в базе, сейчас добавим")
    else:
        pass
    # Проверяем пользователя заполнил ли он анкету!
    if DB.check_guestion(message.from_user.id) == False:
        await bot.send_message(message.from_user.id, "Кажется ты еще не заполнил анкету!")
        # падаем в FSM и собираем данные
        await UserForm.name.set()
        await bot.send_message(message.from_user.id, "Как вас зовут?")
        
        #Принтуем пользователю все данные которые он ввел а также две инлайн кнопки: Подтвердить

        # Присылаем пользователю сообщение с благодарностью и отправялем инлайн кнопку со сылкой на наш сайт

        # Добавляем данные в БД

    else:
        pass


#FSM АНКЕТА
@dp.message_handler(state=UserForm.name)
async def process_name(message: types.Message, state: FSMContext):
    if DB.check_in_none(message.text) == True: # Проверка на символы
        async with state.proxy() as data:
            data['name'] = message.text
        await UserForm.next()
        await bot.send_message(message.from_user.id, "Напишите название организации которую вы представляете?")
    else:
        await bot.send_message(message.from_user.id, "Некорректное имя. Пожалуйста, попробуйте еще раз.")

#Здесь нет проверки
@dp.message_handler(state=UserForm.company)
async def process_company(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['company'] = message.text
    await UserForm.next()
    await bot.send_message(message.from_user.id, "Ваша должность в компании?")

@dp.message_handler(state=UserForm.job_title)
async def process_job_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['job_title'] = message.text
    await UserForm.next()
    await bot.send_message(message.from_user.id, "Напишите ваш актуальный e-mail:")

@dp.message_handler(state=UserForm.email)
async def process_email(message: types.Message, state: FSMContext):
    if DB.check_email(message.text) == True:
        async with state.proxy() as data:
            data['email'] = message.text
        await UserForm.next()
        await bot.send_message(message.from_user.id, "Напишите ваш актуальный номер телефона:")
    else:
        await bot.send_message(message.from_user.id, "Некорректный email. Пожалуйста, попробуйте еще раз.")

@dp.message_handler(state=UserForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    if DB.check_phone(message.text) == True:
        async with state.proxy() as data:
            data['phone'] = message.text
        DB.post_users_question_data(message.from_user.id, 
                                    name = data['name'], 
                                    company = data['company'], 
                                    job_title=data['job_title'], 
                                    email=data['email'], 
                                    phone_quest=data['phone'])
        DB.post_user_question(message.from_user.id)

        # Отметка, что пользователь прошел анкету
        # Изменения в счетчике анкет
        # Отправка сообщения с данными и кнопками подтверждения
        async with state.proxy() as data:
            confirmation_message = "Все данные, которые вы ввели:\n"
            for key, value in data.items():
                confirmation_message += f"{key}: {value}\n"
            confirmation_message += "Данные верны?"
            await bot.send_message(message.from_user.id, confirmation_message, reply_markup=get_confirmation_keyboard())
        
        await UserForm.confirmation.set()
        await state.finish()
    else:
        await bot.send_message(message.from_user.id, "Некорректный номер телефона. Пожалуйста, попробуйте еще раз.")


def get_confirmation_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("✅ Да", callback_data='confirm_yes'),
        InlineKeyboardButton("❌ Нет", callback_data='confirm_no')
    )
    return keyboard

@dp.callback_query_handler(lambda c: c.data in ['confirm_yes', 'confirm_no'], state=UserForm.confirmation)
async def process_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    if callback_query.data == 'confirm_yes':
        await bot.send_message(callback_query.from_user.id, "Спасибо! Ваши данные сохранены.")
        await state.finish()
    elif callback_query.data == 'confirm_no':
        await bot.send_message(callback_query.from_user.id, "Давайте попробуем еще раз.")
        await UserForm.name.set()
        await bot.send_message(callback_query.from_user.id, "Как вас зовут?")

# Запуск бота!
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)