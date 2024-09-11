from secret_data import t, c, g, p_l_g, p_l_m, p_l_r_h, p_l_k, p_l_s, c_t
# Запустить скрипт get_file_id
# Отпарвить файлы в чат 
# Получить ID файлов и встаивть их в лист secret_data

#bot
TOKEN = t 

#DB
DB_NAME = 'USERS.db'

#GOD
GOD_ID = g

#PDF_CATALOG_ID
CATALOG_FILE_ID = c
PRICE_GLAMA_FILE_ID = p_l_g
PRICE_MOZAIKA_FILE_ID = p_l_m
PRICE_RUS_H_FILE_ID = p_l_r_h
PRICE_KIKI_FILE_ID = p_l_k
PRICE_SALES_FILE_ID = p_l_s

CONTACT_TELEPHONE = c_t

#gt
TABLE_TOKEN = '' #.json

#God_voice
add_admin = 'add_perfect_admin' #делает сказавшего админом
admin_menu = 'get_admin_menu' #Получаем меню админа inline
xml_dumb = 'get_all_db' #отправляет дамп БД в формате xml

#КОЛБЭКИ С КНОПОК - НЕ ТРОГАТЬ!
catalog_1 = 'catalog_one' #Первая кнопка запроса каталога
contest_1 = 'contest_one' #Первая кнопка регистрации в конкурсе
