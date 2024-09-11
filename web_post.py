#Имитирует ввод польхователем данных в форму на сайте фаб-арт
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def submit_form(url, name, email, phone):
    # Инициализация WebDriver
    driver = webdriver.Chrome()

    try:
        # Открываем страницу
        driver.get(url)

        # Ждем некоторое время, чтобы страница полностью загрузилась
        time.sleep(5)

        # Находим поля ввода и заполняем их
        name_input = driver.find_element(By.ID, 'input_6967513689601')
        email_input = driver.find_element(By.ID, 'input_6967513689600')
        phone_input = driver.find_element(By.ID, 'input_6967513689602')

        name_input.send_keys(name)
        email_input.send_keys(email)
        phone_input.send_keys(phone)

        # Находим кнопку отправки и отправляем форму
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()

        # Ждем некоторое время, чтобы форма была отправлена
        time.sleep(5)

        print("Форма успешно отправлена!")

    finally:
        # Закрываем браузер
        driver.quit()

if __name__ == "__main__":
    url = 'https://fabrica-tvorchestva.ru/event'
    name = 'Тестовый человек'
    email = 'antuas_тестинг@gmail.com'
    phone = '89274567564'

    submit_form(url, name, email, phone)


