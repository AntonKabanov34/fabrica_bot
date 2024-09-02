import texts
import config
import sqlite3
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup

class DataBase:
    def __init__(self, db_name):
        """Управление базой данных"""
        self.db_name = db_name

    def create_db(self):
        """Создает БД и структуру"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Создаем таблицы, внутри БД
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tg_bot_users (
                id INTEGER PRIMARY KEY,
                chat_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                admin BOOLEAN DEFAULT FALSE,
                sent_catalog BOOLEAN DEFAULT FALSE,
                sent_price BOOLEAN DEFAULT FALSE
            )
            ''')
            print('Создана таблица ---tg_bot_users---')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_full_name (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                FOREIGN KEY (user_id) REFERENCES tg_bot_users(id)
            )
            ''')
            print('Создана таблица ---users_full_name---')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_e_mail (
                user_id INTEGER PRIMARY KEY,
                e_mail TEXT,
                FOREIGN KEY (user_id) REFERENCES tg_bot_users(id)
            )
            ''')
            print('Создана таблица ---users_e_mail---')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS phone_number (
                user_id INTEGER PRIMARY KEY,
                phone_number TEXT,
                FOREIGN KEY (user_id) REFERENCES tg_bot_users(id)
            )
            ''')
            print('Создана таблица ---phone_number---')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_registr (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                phone_number INTEGER UNIQUE,
                reg_date DATETIME,
                FOREIGN KEY (user_id) REFERENCES tg_bot_users(id)
            )
            ''')
            print('Создана таблица ---game_registr---')

            # Сохраняем изменения
            conn.commit()

            print(f"База данных {self.db_name} успешно создана или уже существует.")

    def create_new_db(self):
        """Создает таблицу для сбора данных FSM"""
        
        pass

    def user_exam(self, chat_id: int) -> bool:
        """Проверяет есть ли ID пользователя в базе"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT EXISTS(SELECT 1 FROM tg_bot_users WHERE chat_id = ?)
            ''', (chat_id,))
            result = cursor.fetchone()
            return result[0] == 1

    def add_god_admin(self, chat_id: int):
        """Добавляет бога-админа через обработчик текста"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE tg_bot_users
            SET admin = TRUE
            WHERE chat_id = ?
            ''', (chat_id,))
            conn.commit()

    def admin_exam(self, user_id: int) -> bool:
        """Проверяет является ли пользователь админом"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT admin FROM tg_bot_users WHERE chat_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            return result is not None and result[0]

    def add_new_user(self, chat_id: int, first_name: str, last_name: str, username: str):
        """Добавляет нового пользователя в БД"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO tg_bot_users (chat_id, first_name, last_name, username)
            VALUES (?, ?, ?, ?)
            ''', (chat_id, first_name, last_name, username))
            conn.commit()

    def save_user_name(self, chat_id: int, name: str) -> bool:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM tg_bot_users WHERE chat_id = ?', (chat_id,))
            user_id = cursor.fetchone()

            if user_id is None:
                return False

            user_id = user_id[0]
            cursor.execute('INSERT OR REPLACE INTO users_full_name (user_id, full_name) VALUES (?, ?)', (user_id, name))
            conn.commit()
            return True

    def save_user_email(self, chat_id:int, email:str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM tg_bot_users WHERE chat_id = ?', (chat_id,))
            user_id = cursor.fetchone()

            if user_id is None:
                return False

            user_id = user_id[0]
            cursor.execute('INSERT OR REPLACE INTO users_e_mail (user_id, e_mail) VALUES (?, ?)', (user_id, email))
            conn.commit()
            return True

    def save_user_telephone(self, chat_id:int, telephone:str):
        """Сохраняет в БД номер телефона пользователя, связываает его с CHAT_ID"""

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM tg_bot_users WHERE chat_id = ?', (chat_id,))
            user_id = cursor.fetchone()

            if user_id is None:
                return False

            user_id = user_id[0]
            cursor.execute('INSERT OR REPLACE INTO phone_number (user_id, phone_number) VALUES (?, ?)', (user_id, telephone))
            conn.commit()
            return True

class KeyBoard:
    def __init__(self):
        pass

    def get_main_menu(self):
        """Генерирует главное меню с кнопками."""
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton(texts.bot_info_button))
        markup.add(KeyboardButton(texts.catalog_button))
        markup.add(KeyboardButton(texts.ask_question_button))
        return markup
    
    def get_inline_buttons(self):
        """Генерирует инлайн-кнопки основного меню."""
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("Конкурс", callback_data=config.contest_1),InlineKeyboardButton("Получить каталог", callback_data=config.catalog_1))
        return markup
    
    def get_number_buttons(self):
        """Генерирует кнопку запроса номера телефона"""
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(KeyboardButton(text=texts.contest_get_phone_button, request_contact=True))
        return keyboard

class Form(StatesGroup):
    name = State()
    email = State()


        
