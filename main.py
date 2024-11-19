import telebot
import schedule
import time
import requests
from datetime import datetime
import pytz
import logging
from requests.exceptions import ConnectionError

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot('7783596961:AAFhPxwNsjX0s2woiv0tPL7W9Gk-s5Kb7Nk')
API_KEY = '4348b5adfe229797d37b8d2f1cec1503'
chat_id = None

def get_current_time():
    kyiv_tz = pytz.timezone('Europe/Kiev')
    current_time = datetime.now(kyiv_tz).strftime("%H:%M")
    return current_time

def get_weather():
    url = f'http://api.openweathermap.org/data/2.5/weather?q=Lviv,UA&appid={API_KEY}&units=metric&lang=ua'
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        temp = int(weather_data["main"]["temp"])
        weather_description = weather_data["weather"][0]["description"]
        wind_speed = weather_data["wind"]["speed"]

        # Перевірка на наявність даних про опади
        rain_amount = weather_data.get("rain", {}).get("1h", None)
        if rain_amount is not None:
            rain_probability = min(int(rain_amount * 10), 100)
        else:
            rain_probability = 0

        message = (
            f"📍 *Погода у Львові*\n"
            f"🕒 Час оновлення: {get_current_time()}\n"
            f"🌡️ Температура: {temp}°C\n"
            f"🌤️ Опис: {weather_description.capitalize()}\n"
            f"💨 Вітер: {wind_speed} м/с\n"
            f"🌧️ Імовірність опадів: {rain_probability}%"
        )
        return message
    else:
        logging.error("Не вдалося отримати дані про погоду.")
        return "Не вдалося отримати дані про погоду."

@bot.message_handler(commands=['start'])
def main(message):
    global chat_id
    chat_id = message.chat.id
    bot.send_message(chat_id, "Бот запущений! Я надсилатиму погоду у Львові в 7:00, 14:00 та 20:00.", reply_markup=get_weather_button())

@bot.my_chat_member_handler()
def added_to_chat(message):
    global chat_id
    if message.new_chat_member.status == "member":
        chat_id = message.chat.id
        bot.send_message(chat_id, "Привіт! Я тепер у вашому чаті і надсилатиму погоду у Львові в 7:00, 14:00 та 20:00.", reply_markup=get_weather_button())

def get_weather_button():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    weather_button = telebot.types.KeyboardButton("Гляну погоду прямо зараз")
    markup.add(weather_button)
    return markup

@bot.message_handler(func=lambda message: message.text == "Гляну погоду прямо зараз")
def send_weather_now(message):
    weather = get_weather()
    bot.send_message(message.chat.id, weather, parse_mode='Markdown')

def send_scheduled_weather():
    if chat_id:
        weather = get_weather()
        try:
            bot.send_message(chat_id, weather, parse_mode='Markdown')
        except ConnectionError as e:
            logging.error("Не вдалося надіслати повідомлення через проблеми зі з'єднанням: %s", e)

# Розклад повідомлень
schedule.every().day.at("07:00").do(send_scheduled_weather)
schedule.every().day.at("14:00").do(send_scheduled_weather)
schedule.every().day.at("20:00").do(send_scheduled_weather)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, timeout=5)
        except Exception as e:
            logging.error("Помилка під час роботи бота: %s", e)
            time.sleep(15)  # Очікування перед перезапуском

if __name__ == '__main__':
    import threading

    scheduler_thread = threading.Thread(target=run_scheduler)
    bot_thread = threading.Thread(target=run_bot)

    scheduler_thread.start()
    bot_thread.start()

    scheduler_thread.join()
    bot_thread.join()
