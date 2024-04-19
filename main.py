import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Update
import logging
import datetime
import pytz
import json

# Загрузка настроек
with open('settings.json') as json_file:
    settings = json.load(json_file)

# Подключение к Google Sheets API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(credentials)

# Открытие таблицы по URL
sheet = client.open_by_url(settings['spreadsheet_url']).worksheet(settings['worksheet'])


#Функция обрезки лишних символов на конце строки
def cutlast(s, tail):
    if s[-len(tail):] == tail:
        s = s[:-len(tail)] 
    return s

# Функция для обработки команды /start
def start(update, context):
    update.message.reply_text('Привет! Отправь мне данные о пройденном километраже, имени события и его стоимости.')

# Функция для сохранения данных в Google таблице
def save_data(update, context):
    chat_id = update.message.chat.id
    date_msg_utc = update.message.forward_date if update.message.forward_date else update.message.date
    tz = pytz.timezone('Europe/Moscow')
    date_msg = date_msg_utc.astimezone(tz)
    
    data = update.message.text.split()
    cost = data.pop(-1)
    cost = cutlast(cost, 'руб.')
    cost = cutlast(cost, 'руб')
    cost = cutlast(cost, 'р.')
    cost = cutlast(cost, 'р')

    if data[0].isnumeric():
        kilometers = data.pop(0)
    else:
        kilometers = ''

    event = ' '.join(data)
    time = date_msg.strftime("%Y-%m-%d-%H:%M")

    if cost.isnumeric() and event:
        row = [time, kilometers, event, cost]
        print(row)
        sheet.append_row(row)
        update.message.reply_text('Данные успешно сохранены в Google таблице.')
    else:
        update.message.reply_text('Неверный формат данных. Попробуйте еще раз.')

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Создание обработчиков команд и сообщений
updater = Updater(settings['bottoken'])
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, save_data))

# Запуск бота
updater.start_polling()
updater.idle()
