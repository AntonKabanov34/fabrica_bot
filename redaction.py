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
import datetime
import os
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

class AdminMessage(StatesGroup):
    write_message = State()
    confirm_message = State()


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


# __________Обработчик кнопок из MainMenu()________________ 
        
# Обработчик команды products
@dp.message_handler(lambda message: message.text == texts.products)
async def process_products(message: types.Message):
    if DB.get_quest_users(message.from_user.id) == True:
        await bot.send_message(message.from_user.id, text=texts.mess_get_product, reply_markup=keyboard.get_product(), parse_mode="Markdown")
    else:
        await bot.send_message(message.from_user.id, 'Что-то не могу вас найти... Нажмите /start и заполните анкету')

# Обработчик команды prize
@dp.message_handler(lambda message: message.text == texts.prize)
async def process_prize(message: types.Message):
    if DB.get_quest_users(message.from_user.id) == True:
        await bot.send_message(message.from_user.id, texts.prize_welcome)
        # Проверка на доступность регистрации
        if DB.check_registration_game('game') == True:
            # Регистрация доступна проверка на id зарегестрированных
            if DB.chek_game_register_id(message.from_user.id) == False:
                # Игрок не зарегестрирован  - проводим интерактив.
                await bot.send_message(message.from_user.id, texts.prize_open, reply_markup=keyboard.get_prize_comunication('one'))
            else:
                lot = DB.format_lot_number(DB.get_user_lot(message.from_user.id)[0])
                await bot.send_message(message.from_user.id, text = f'{texts.prize_confirm_registr} {lot}', reply_markup=keyboard.get_main_menu())
                pass
        else:
            await bot.send_message(message.from_user.id, texts.prize_close, reply_markup=keyboard.get_main_menu())
            pass
    else:
        await bot.send_message(message.from_user.id, 'Что-то не могу вас найти... Нажмите /start и заполните анкету')

# Обработчик команды serch_stand
@dp.message_handler(lambda message: message.text == texts.serch_stand)
async def process_serch_stand(message: types.Message):
    if DB.get_quest_users(message.from_user.id) == True:
        await bot.send_photo(chat_id=message.from_user.id, photo=config.map_in, caption=texts.serch_stand_photo)
        await bot.send_sticker(chat_id=message.from_user.id, sticker=config.stiker_dora)
    else:
        await bot.send_message(message.from_user.id, 'Что-то не могу вас найти... Нажмите /start и заполните анкету')
    
# Обработчик команды fabric_info
@dp.message_handler(lambda message: message.text == texts.fabric_info)
async def process_fabric_info(message: types.Message):
    if DB.get_quest_users(message.from_user.id) == True:
        #Eсли пользователь не получил еще ни одного фан-факта
        if DB.get_data_ff(message.from_user.id) == False:
            await bot.send_photo(chat_id=message.from_user.id, photo=texts.fan_in_photo, caption=texts.fan_in, reply_markup=keyboard.get_next_fact())
        
        #Если пользователь посмотрел все фанфакты
        elif len(DB.get_data_ff(message.from_user.id)) >= 10:
            await bot.send_photo(chat_id=message.from_user.id, photo=texts.fan_in_photo, caption=texts.fan_in, reply_markup=keyboard.get_next_fact())
            #await bot.send_message(message.from_user.id, "Подробней о нас можно узнать на стенде")
        # Для всех остальных случаев, когда пользователь получил часть фактов но не все
        else:
            await bot.send_message(message.from_user.id, "Может еще один фан-факт?", reply_markup=keyboard.get_next_fact())


         
    else:
        await bot.send_message(message.from_user.id, 'Что-то не могу вас найти... Нажмите /start и заполните анкету')

 
#____________FSM АНКЕТА________________
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

#_________FSM MESSAGE_______
@dp.message_handler(state=AdminMessage.write_message)
async def process_write_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message_text'] = message.text
    
    await AdminMessage.next()
    await bot.send_message(message.from_user.id, f'{texts.post_message_chek}\n\n\"{message.text}\"\n\n{texts.post_message_chek_two}', reply_markup=keyboard.get_admin_message_confirm())


#________________CallBack___________________
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

# Обработчик контактов из телеграм
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

#Колбеки для меню администратора
@dp.callback_query_handler(lambda c: c.data in ['post_all_message', 'get_game_status', 'get_bot_state', 'get_xml_file', 'post_registration_status', 'post_list_gamers', 'cancel_game_menu', 'post_status_game_open', 'post_status_game_close', 'post_gamer_list', 'post_gamer_del', 'next_fun_fact'])
async def process_product_callback(callback_query: types.CallbackQuery):
    #_____________Функционал для отправки сообщений всем пользователям_____________
    if callback_query.data == 'post_all_message':
        await AdminMessage.write_message.set()
        await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=texts.post_message)
    
    #____________Управление игрой________________ 
    elif callback_query.data == 'get_game_status':
        await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=texts.post_game_control, reply_markup=keyboard.game_main_menu())

    # Изменение статуса регистрации
    elif callback_query.data == 'post_registration_status':
        status_now = 'Открыта' if DB.check_registration_game('game') else 'Закрыта'
        await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=f'{texts.post_game_registr_text} {status_now}', reply_markup=keyboard.game_registr_control())
        pass

    # Открыть регистрацию
    elif callback_query.data == 'post_status_game_open':
        if DB.check_registration_game('game') == True:
            await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text='Это защитное сообщение, регистарция в игру уже ОТКРЫТА')
        else:
            DB.post_game_status('game', 1)
            await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text='Регистрация в игре ОТКРЫТА')
        pass
    # Закрыть регистрацию
    elif callback_query.data == 'post_status_game_close':
        if DB.check_registration_game('game') == False:
            await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text='Это защитное сообщение, регистарция в игру уже ЗАКРЫТА')
        else:
            DB.post_game_status('game', 0)
            await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text='Регистрация в игре ЗАКРЫТА')
        pass


    # Управление списком игроков
    elif callback_query.data == 'post_list_gamers':
        await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=texts.post_gamer_list_text, reply_markup=keyboard.gamer_list_menu())
        pass

    elif callback_query.data == 'post_gamer_list':
        # Получаем список chat_id участников
        chat_ids = DB.get_game_register_data()
        if not chat_ids:
            await bot.send_message(callback_query.from_user.id, "Нет данных для отправки.")
            return

        # Создаем словарь для хранения данных
        gamers = {}

        # Получаем данные для каждого chat_id
        for chat_id in chat_ids:
            result = DB.get_user_lot(chat_id)
            if result:
                loto_number, phone_telegram = result
                gamers[loto_number] = phone_telegram
        print(gamers)
        # Создаем временный файл для Excel с датой в названии
        current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = f"game_register_data_{current_date}.xlsx"
        DB.create_excel_file(gamers, file_path)

        try:
            with open(file_path, 'rb') as file:
                await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text='Контрольный лист участников:')
                await bot.send_document(chat_id=callback_query.from_user.id, document=file)
            os.remove(file_path)
            print(f"Файл успешно отправлен и удален: {file_path}")
        except Exception as e:
            print(f"Ошибка при отправке или удалении файла: {e}")
        pass
    
    elif callback_query.data == 'post_gamer_del':
        #Проверяем октрыта или закрыта регистрация, если открыта, не даем очистить список игроков
        if DB.check_registration_game('game') == False:
            DB.clear_game_register()
            await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text='Список участников успешно очищен')

            pass
        else:
            await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text='Регистрация в игре ОТКРЫТА!\nЗакройте регистрацию прежде чем очистить список игроков и лотов')

    elif callback_query.data == 'next_fun_fact':
        fact_now = DB.get_data_ff(callback_query.from_user.id)
        # Ситуация с нулевыми фактами
        if fact_now == False:
            from random import randint
            fact_post = randint(1,10)
            DB.post_data_ff(callback_query.from_user.id, fact_post)
            post = texts.ff_data[fact_post]
            if post[0] == 'gif':
                await bot.send_animation(chat_id=callback_query.from_user.id, animation=post[2], caption=post[1], reply_markup=keyboard.get_next_fact())
                await bot.answer_callback_query(callback_query.id)
            else:
                await bot.send_photo(chat_id=callback_query.from_user.id, photo=post[2], caption=post[1], reply_markup=keyboard.get_next_fact())
                await bot.answer_callback_query(callback_query.id)
            pass
        elif len(fact_now.split(',')) >= 10:
            if DB.get_quest_users(callback_query.from_user.id) == True:
                await bot.send_photo(chat_id=callback_query.from_user.id, photo=config.map_in, caption=texts.fan_map_close)
                await bot.send_sticker(chat_id=callback_query.from_user.id, sticker=config.stiker_dora)
            else:
                await bot.send_message(callback_query.from_user.id, 'Что-то не могу вас найти... Нажмите /start и заполните анкету')
                pass
        else:
            from random import randint
            #Спсиок отправленных фанфактов 
            fact_all=list(texts.ff_data.keys())
            now = fact_now.split(',')
            now = [int(item) for item in now]
            result_list = set(fact_all) - set(now)
            result_list = list(result_list)
            
            # Номер следующего факта (индекс)
            fact_post = randint(0, len(result_list)-1)
            
            print(f'Список ключей фанфактов: {fact_all}')
            print(f'Опубликованные факты: {now}')
            print(f'Остаток по фактам: {result_list}')
            print(f'Индекс следующего факта: {fact_post}')


            DB.post_data_ff(callback_query.from_user.id, result_list[fact_post])
            #Номер фан факта {result_list[fact_post]}'
            #тест отправки гиф result_list[fact_post]][0]
            resultats = texts.ff_data[[result_list[fact_post]][0]]
            print(f'Результат извлечения из словаря: {resultats}')
            if resultats[0] == 'gif':
                await bot.send_animation(chat_id=callback_query.from_user.id, animation=resultats[2], caption=resultats[1], reply_markup=keyboard.get_next_fact())
                await bot.answer_callback_query(callback_query.id)
            else:
                await bot.send_photo(chat_id=callback_query.from_user.id, photo=resultats[2], caption=resultats[1], reply_markup=keyboard.get_next_fact())
                await bot.answer_callback_query(callback_query.id)
            pass

    #Выход из всех меню
    elif callback_query.data == 'cancel_game_menu':
        await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=texts.post_cansel_menu)
        pass


    #Функционал для получения данных о пользователях
    elif callback_query.data == 'get_bot_state':
        # Принтует текущие данные о состоянии бота
        mes = f"Данные записанные в БД:\n\nКол-во нажатий СТАРТ: {DB.get_all_count('start')}\nКол-во заполненых анкет: {DB.get_all_count('registration')}\nКол-во отправленных каталогов: {DB.get_all_count('catalog')}\nКол-во отправленных прайсов: {DB.get_all_count('price')}\nКол-во электронных адресов: {DB.get_all_count('email_all')}\nКол-во анкетных телефонов: {DB.get_all_count('phone_all')}\nКол-во регистраций (СЕЙЧАС): {DB.get_game_count()}\nОбщее число регистраций: {DB.get_personal_phone()}"
        await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=mes)
        pass

    elif callback_query.data == 'get_xml_file':
        current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path =f'{DB.get_users_data_xml(current_date)}'

        try:
            with open(file_path, 'rb') as file:
                await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text='Дамп текущей БД:')
                await bot.send_document(chat_id=callback_query.from_user.id, document=file)
            os.remove(file_path)
            print(f"Файл успешно отправлен и удален: {file_path}")
        except Exception as e:
            print(f"Ошибка при отправке или удалении файла: {e}")
        pass

#Колбеки для обработки FSM_Message
@dp.callback_query_handler(lambda c: c.data in ['confirm_message_yes', 'confirm_message_no', 'confirm_message_cancel'], state=AdminMessage.confirm_message)
async def process_confirm_message(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    
    if callback_query.data == 'confirm_message_yes':
        async with state.proxy() as data:
            message_text = data['message_text']
            users = DB.get_all_users()
            eror_users = 0
            mess_admin = f'{texts.post_message_out}\n\n"{message_text}"\n\nБыло отправлено {len(users)} пользователям\nОшибок при отправлении: {eror_users} (сообщения не доставлены: пользователя нет или он заблокировал бота)'
            for user_id in users:
                if user_id == callback_query.from_user.id:
                    continue 
                try:
                    await bot.send_message(chat_id=user_id, text=message_text)
                except Exception as e:
                    eror_users = eror_users + 1
                    
            await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=mess_admin)
            await state.finish()

    
    elif callback_query.data == 'confirm_message_no':
        await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=texts.post_message_reply)
        await AdminMessage.write_message.set()
    
    elif callback_query.data == 'confirm_message_cancel':
        await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=texts.post_message_cancel)
        await state.finish()




#____________Голос БОГА________________
@dp.message_handler(lambda message: message.text.lower() in ['get_god_menu'])
async def process_prize(message: types.Message):
    if DB.chek_admin(message.from_user.id) == True:
        await bot.send_message(message.from_user.id, "Здарова админ, че хочешь?", reply_markup=keyboard.get_admin_main_menu()) 
    else:
        pass 


# Отправить сообщение всем пользователям FSM - ТЕКСТ - ПОДТВЕРЖДЕНИЕ - ОТПРАВКА
# Замена статуса регистрации в игре - 2 команды ON/OF + отправка текущего статуса
# Получить список участников розыгрыша СООБЩЕНИЕМ и XML + текущая дата
# Удалить список участников полностью
# Получить список всех пользователей бота в формате XML

#____________start_____________________
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