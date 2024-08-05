from secret_data import t, c
#Первый запуск: 
#Запусти бота, нажать /start и отправь боту актуальную версию каталога
#Возьми из терминала актуальную версию FILE_ID
#Вставь актуальну версию в листе config в переменную CATALOG_FILE_ID
#Сохрани файл и перезапусти бота

#bot
TOKEN = t 

#DB
DB_NAME = 'USERS.db'

#PDF_CATALOG_ID
CATALOG_FILE_ID = c

#gt
TABLE_TOKEN = '' #.json

#God_voice
add_admin = 'add_perfect_admin' #делает сказавшего админом
admin_menu = 'get_admin_menu' #Получаем меню админа inline
xml_dumb = 'get_all_db' #отправляет дамп БД в формате xml

#КОЛБЭКИ С КНОПОК - НЕ ТРОГАТЬ!
catalog_1 = 'catalog_one' #Первая кнопка запроса каталога
contest_1 = 'contest_one' #Первая кнопка регистрации в конкурсе
