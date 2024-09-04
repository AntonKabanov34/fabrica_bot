import texts
import config
import sqlite3
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
import re

class DataBase:
    def __init__(self, db_name):
        """Управление базой данных"""
        self.db_name = db_name
    
    # Создания
    def create_db(self):
        """Создание БД и таблиц"""
        create_table_queries = [
            """
            CREATE TABLE IF NOT EXISTS bot_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS users_data (
                id INTEGER PRIMARY KEY,
                user_name TEXT,
                first_name TEXT,
                last_name TEXT,
                name TEXT,
                company TEXT,
                job_title TEXT,
                email TEXT,
                phone_quest TEXT,
                agreement INTEGER DEFAULT 0,
                phone_telegram TEXT,
                FOREIGN KEY (id) REFERENCES bot_users (id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY,
                FOREIGN KEY (id) REFERENCES bot_users (id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS question (
                id INTEGER PRIMARY KEY,
                FOREIGN KEY (id) REFERENCES bot_users (id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS game_register (
                id INTEGER PRIMARY KEY,
                FOREIGN KEY (id) REFERENCES bot_users (id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS coun (
                start INTEGER DEFAULT 0,
                registration INTEGER DEFAULT 0,
                catalog INTEGER DEFAULT 0,
                price INTEGER DEFAULT 0,
                game_now INTEGER DEFAULT 0,
                game_all INTEGER DEFAULT 0,
                email_all INTEGER DEFAULT 0,
                phone_all INTEGER DEFAULT 0
            );
            """
        ]

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            for query in create_table_queries:
                cursor.execute(query)
            conn.commit()

    def add_god(self, chat_id):
        """Добавление первой записи chat_id в таблицы bot_users и admin"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            try:
                # Добавляем chat_id в таблицу bot_users
                cursor.execute("INSERT INTO bot_users (chat_id) VALUES (?)", (chat_id,))
                user_id = cursor.lastrowid  # Получаем id только что добавленной записи

                # Добавляем запись в таблицу admin с соответствующим user_id
                cursor.execute("INSERT INTO admin (id) VALUES (?)", (user_id,))
                conn.commit()
                return True  # Возвращаем True, если добавление прошло успешно
            except sqlite3.IntegrityError:
                # Если chat_id уже существует в таблице bot_users, откатываем транзакцию
                conn.rollback()
                return False  # Возвращаем False, если добавление не удалось

    # Проверки
    def chek_users(self, chat_id):
        """Проверяет есть ли обратившийся в списке пользователей"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM bot_users WHERE chat_id = ?", (chat_id,))
            result = cursor.fetchone()
            # Возвращаем True, если пользователь найден, иначе False
            return result is not None  
        
    def check_guestion(self, chat_id):
        """Проверка наличия chat_id в таблицах bot_users и question"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Проверяем наличие chat_id в таблице bot_users
            cursor.execute("SELECT id FROM bot_users WHERE chat_id = ?", (chat_id,))
            result = cursor.fetchone()
            if result is None:
                print(f"Пользователь с chat_id {chat_id} не найден в таблице bot_users")
                pass # Вернуть что-то другое, чтобы попросить пользователя нажать на /start
            else:
                user_id = result[0]
                # Проверяем наличие user_id в таблице question
                cursor.execute("SELECT id FROM question WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                return result is not None  # Возвращаем True, если запись найдена, иначе False

    def check_phone(self, number) -> bool:
        """Проверяет корректность введенного номера телефона"""
        pattern = r'^(\+7|8)\d{10}$'
        return re.match(pattern, number) is not None

    def check_email(self, email) -> bool:
        """Проверяет корректность введенного email"""
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(pattern, email) is not None

    def check_in_none(self, data: str) -> bool:
        """Входящая строка должна содержать хотя бы 2 буквы. Латинские или русские"""
        pattern = r'[a-zA-Zа-яА-Я]'
        letters = re.findall(pattern, data)
        return len(letters) >= 2


    #Обновление данных в БД
    def post_new_users(self, chat_id):
        """Добавляет пользователя в БД, таблица bot_users"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO bot_users (chat_id) VALUES (?)", (chat_id,))
            conn.commit()
            return True  # Возвращаем True, если вставка прошла успешно
    
    def post_users_info(self, chat_id, user_name, first_name, last_name):
        """Добавляет данные о пользователе полученные из месседж бокса в таблицу users_data"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            try:
                # Сначала находим id пользователя в таблице bot_users
                cursor.execute("SELECT id FROM bot_users WHERE chat_id = ?", (chat_id,))
                result = cursor.fetchone()
                if result is None:
                    return False  # Пользователь не найден
                user_id = result[0]

                # Добавляем информацию о пользователе в таблицу users_data
                cursor.execute("""
                    INSERT INTO users_data (id, user_name, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                """, (user_id, user_name, first_name, last_name))
                conn.commit()
                return True  # Возвращаем True, если добавление прошло успешно
            except sqlite3.Error as e:
                print(f"Ошибка при добавлении данных пользователя: {e}")
                conn.rollback()
                return False  # Возвращаем False, если добавление не удалось

    def post_users_question_data(self, chat_id, name, company, job_title, email, phone_quest):
        """Добавляет анкетные данные в таблицу users_data"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            try:
                # Находим индекс записи в таблице bot_users по chat_id
                cursor.execute("SELECT id FROM bot_users WHERE chat_id = ?", (chat_id,))
                result = cursor.fetchone()
                if result is None:
                    return False  # Пользователь не найден
                user_id = result[0]

                # Вставляем или обновляем данные в таблице users_data
                cursor.execute("""
                    INSERT INTO users_data (id, name, company, job_title, email, phone_quest)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    company=excluded.company,
                    job_title=excluded.job_title,
                    email=excluded.email,
                    phone_quest=excluded.phone_quest
                """, (user_id, name, company, job_title, email, phone_quest))
                conn.commit()
                return True  # Возвращаем True, если вставка прошла успешно
            
            except sqlite3.Error as e:
                print(f"Ошибка при добавлении анкетных данных: {e}")
                conn.rollback()
                return False  # Возвращаем False, если вставка не удалась

    def post_user_agreements(self, answer:int):
        """Меняет данные в таблице users_data, в столбце agreement. Вызывается в случае answer=1"""
        pass

    def post_user_question(self, chat_id):
        """Находит id пользователя в bot_users и добавляет id пользователя в таблицу question"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            try:
                # Находим id пользователя в таблице bot_users по chat_id
                cursor.execute("SELECT id FROM bot_users WHERE chat_id = ?", (chat_id,))
                result = cursor.fetchone()
                if result is None:
                    return False  # Пользователь не найден
                user_id = result[0]

                # Добавляем id пользователя в таблицу question
                cursor.execute("INSERT INTO question (id) VALUES (?)", (user_id,))
                conn.commit()
                return True  # Возвращаем True, если вставка прошла успешно
            
            except sqlite3.Error as e:
                print(f"Ошибка при добавлении id пользователя в таблицу question: {e}")
                conn.rollback()
                return False  # Возвращаем False, если вставка не удалась

    def post_counter(self, param):
        """Обращается к таблице coun и меняет значение на +1 по param"""
        pass

    #Получить данные

    def get_count(self):
        """Проходит по БД и получает всю актуальную информацию по цифрам"""
        pass

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
    

class Form(StatesGroup):
    name = State()
    email = State()


        
