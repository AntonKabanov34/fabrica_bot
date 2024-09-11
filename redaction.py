from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InputFile, InlineKeyboardMarkup, InlineKeyboardButton
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
DB.add_god(config.GOD_ID)
DB.ensure_coun_table_has_record() #Создает первую запись в таблице coun
DB.create_game() #Создает игру с выключеным статусом

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

class AdminMess(StatesGroup):
    mess = State()
    confirmation = State()


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    #Проверяем есть ли пользователь в БД, если нет - добавляем
    if DB.chek_users(message.from_user.id) == False:
        DB.post_new_users(message.from_user.id)
        DB.post_users_info(message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
        DB.post_counter('start')
        await bot.send_message(message.from_user.id, texts.start_text)
    else:
        pass # Явный указатель на следующее действие
    
    # Проверяем пользователя заполнил ли он анкету!
    if DB.check_guestion(message.from_user.id) == False:
        await bot.send_message(message.from_user.id, texts.quest_welcome)
        # падаем в FSM и собираем данные
        await UserForm.name.set()
        await bot.send_message(message.from_user.id, texts.what_name, parse_mode="Markdown")
    else:
        # С возвращением
        await bot.send_message(message.from_user.id, texts.restart, reply_markup=keyboard.get_main_menu())


# Обработчик кнопок из MainMenu() 
# Обработчик команды products
@dp.message_handler(lambda message: message.text == texts.products)
async def process_products(message: types.Message):
    await bot.send_message(message.from_user.id, text=texts.mess_get_product, reply_markup=keyboard.get_product(), parse_mode="Markdown")

# Обработчик команды prize
@dp.message_handler(lambda message: message.text == texts.prize)
async def process_prize(message: types.Message):
    await bot.send_message(message.from_user.id, texts.prize_welcome)
    # Проверка на доступность регистрации
    if DB.check_registration_game('game') == True:
        # Регистрация доступна проверка на id зарегестрированных
        if DB.chek_game_register_id(message.from_user.id) == False:
            # Игрок не зарегестрирован  - проводим интерактив.
            await bot.send_message(message.from_user.id, texts.prize_open, reply_markup=keyboard.get_prize_comunication('one'))
        else:
            lot = DB.format_lot_number(DB.get_user_lot(message.from_user.id))
            await bot.send_message(message.from_user.id, text = f'{texts.prize_confirm_registr} {lot}', reply_markup=keyboard.get_main_menu())
            pass
    else:
        await bot.send_message(message.from_user.id, texts.prize_close, reply_markup=keyboard.get_main_menu())
        pass


# Обработчик команды serch_stand
@dp.message_handler(lambda message: message.text == texts.serch_stand)
async def process_serch_stand(message: types.Message):
    await bot.send_message(message.from_user.id, 'Здесь будет инструкция, как нас найти')

# Обработчик команды fabric_info
@dp.message_handler(lambda message: message.text == texts.fabric_info)
async def process_fabric_info(message: types.Message):
    await bot.send_message(message.from_user.id, 'Фан факты о нас')

 
#FSM АНКЕТА
@dp.message_handler(state=UserForm.name)
async def process_name(message: types.Message, state: FSMContext):
    if DB.check_in_none(message.text) == True: # Проверка на символы
        async with state.proxy() as data:
            data['name'] = message.text
        await UserForm.next()
        await bot.send_message(message.from_user.id, texts.what_company, parse_mode="Markdown")
    else:
        await bot.send_message(message.from_user.id, texts.what_name_no, parse_mode="Markdown")

@dp.message_handler(state=UserForm.company)
async def process_company(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['company'] = message.text
    await UserForm.next()
    await bot.send_message(message.from_user.id, texts.what_title, parse_mode="Markdown")

@dp.message_handler(state=UserForm.job_title)
async def process_job_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['job_title'] = message.text
    await UserForm.next()
    await bot.send_message(message.from_user.id, texts.what_email, parse_mode="Markdown")

@dp.message_handler(state=UserForm.email)
async def process_email(message: types.Message, state: FSMContext):
    if DB.check_email(message.text) == True:
        async with state.proxy() as data:
            data['email'] = message.text
        await UserForm.next()
        await bot.send_message(message.from_user.id, texts.what_phone, parse_mode="Markdown")
    else:
        await bot.send_message(message.from_user.id, texts.what_email_no)

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
         # Отправка сообщения с данными и кнопками подтверждения
        async with state.proxy() as data:
            confirmation_message = (
    f"{texts.q_title}:\n\n"
    f"*{texts.q_name}:* {data['name']}\n"
    f"*{texts.q_company}:* {data['company']}\n"
    f"*{texts.q_j_title}:* {data['job_title']}\n"
    f"*{texts.q_email}:* {data['email']}\n"
    f"*{texts.q_phone}:* {data['phone']}\n\n"
    f"{texts.q_out}?"
)
            await bot.send_message(message.from_user.id, confirmation_message, reply_markup=keyboard.get_confirmation_keyboard(), parse_mode="Markdown")
        
        await UserForm.confirmation.set()
    else:
        await bot.send_message(message.from_user.id, texts.what_phone_no)

@dp.callback_query_handler(lambda c: c.data in ['confirm_yes', 'confirm_no'], state=UserForm.confirmation)
async def process_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    if callback_query.data == 'confirm_yes':
        #Выход на политику конфиденциальности
        await bot.edit_message_text(message_id=callback_query.message.message_id, chat_id=callback_query.from_user.id, text=texts.quest_out_politic, reply_markup=keyboard.get_politic_confirmation())
        
        # Отметка, что пользователь подтвердил данные
        DB.post_user_question(callback_query.from_user.id)
        
        # Изменения в счетчиках
        DB.post_counter('registration')
        DB.post_counter('email_all')
        DB.post_counter('phone_all')
        await state.finish()
    
    elif callback_query.data == 'confirm_no':
        await bot.send_message(callback_query.from_user.id, texts.quest_restart)
        await UserForm.name.set()
        await bot.send_message(callback_query.from_user.id, texts.what_name, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == 'confirm_politic')
async def process_update_db(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    #Поменяли статус в БД - принял политику конфиденциальности
    DB.post_user_agreements(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, texts.quest_out, reply_markup=keyboard.get_main_menu())

#Колбеки для получения прайслиста и каталога
@dp.callback_query_handler(lambda c: c.data in ['get_catalog', 'get_price_list'])
async def process_product_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    
    if callback_query.data == 'get_catalog':
        await bot.send_message(callback_query.from_user.id, "Отправляем каталог...")
        await bot.send_document(callback_query.from_user.id, document=config.CATALOG_FILE_ID, caption="Здесь вы найдете всю линейку товаров Фабркии Творчества.")
        DB.post_counter('catalog')
        # Отметка об отправке
    elif callback_query.data == 'get_price_list':
        # Сообщение с отпарвкой каталога
        await bot.send_message(callback_query.from_user.id, texts.post_price_text)
    
        # Принтуем сообщение и прайсы
        await bot.send_document(callback_query.from_user.id, document=config.PRICE_GLAMA_FILE_ID, caption=texts.post_glama_caption)
        await bot.send_document(callback_query.from_user.id, document=config.PRICE_MOZAIKA_FILE_ID, caption=texts.post_mozaika_caption)
        await bot.send_document(callback_query.from_user.id, document=config.PRICE_RUS_H_FILE_ID, caption=texts.post_russian_h_caption)
        await bot.send_document(callback_query.from_user.id, document=config.PRICE_KIKI_FILE_ID, caption=texts.post_kiki_caption)
        await bot.send_document(callback_query.from_user.id, document=config.PRICE_SALES_FILE_ID, caption=texts.post_sales_caption)
        #Отметка об отправке
        DB.post_counter('price')

        await bot.send_message(callback_query.from_user.id, texts.post_price_out)

#Колбеки для розыгрыша
@dp.callback_query_handler(lambda c: c.data in ['next_step_prize', 'registration_final'])
async def process_product_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    if callback_query.data == 'next_step_prize':
        #Нюансы регистрации
        await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=texts.prize_rules, reply_markup=keyboard.get_prize_comunication('two'))
    elif callback_query.data == 'registration_final':
        await bot.send_message(chat_id = callback_query.from_user.id, text=texts.prize_final_mess, reply_markup=keyboard.get_contact_keyboard())

# Обработчик контактов  
@dp.message_handler(content_types=['contact'])
async def process_contact(message: types.Message):
    if message.contact:
        #Запись номеров
        DB.post_telegram_phone(message.from_user.id, message.contact.phone_number)
        if DB.get_game_count() >= 0:
            new_gamer = DB.get_game_count() + 1
            DB.post_new_gamer(message.from_user.id, new_gamer)
            lot = DB.format_lot_number(new_gamer)
            await bot.send_message(message.from_user.id, text = f"{texts.prize_lot} {lot}\n{texts.prize_true_out}", reply_markup=keyboard.get_main_menu())
        else:
            print('Что-то пошло нетак в блоке регистрации игроков')
            pass          
    else:
        await bot.send_message(message.from_user.id, text = texts.new_gamer_error, reply_markup=keyboard.get_main_menu())
        print('Ошибка в блоке создания новых игроков в розфыгрыше')
        

# Запуск бота!
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    

#Список подсчитаных каунтеров
    #start
    #Registration
    #email_all
    #catalog
    #price
    #phone_all