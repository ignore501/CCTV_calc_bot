import logging
import json

from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    ContextTypes, MessageHandler,
    filters, CallbackQueryHandler
)
import sqlite3

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
# set higher logging level for httpx to avoid
# all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)    # logging code. need to check later

main_keyboard = [
    ["дом/дача", "квартира", "магазин"],
    ["лифт", "офис", "склад"],
    ["ресторан/кафе", "аптека", "автомойка"],
    ["только улица", "школа", "Другое"]
]

info_kb = [
    ['Кол-во уличных камер', 'Кол-во внутренних камер'],
    ['Кол-во дней записи архива', 'Опциональные данные'], ['Начать заново', 'Рассчитать']
]

data_keys = dict.fromkeys([x for lst in info_kb for x in lst if x not in ['Рассчитать', 'Опциональные данные']], 0)

optional_kb = [
    ['Кол-во кабеля(по умол. 150 м.)', 'Запись звука'],
    ['Доступ со смартфона', 'АРМ'],
    ['Начать заново', 'Вернуться', 'Рассчитать']
]

prices = {
    'Кол-во уличных камер': 5000,
    'Кол-во внутренних камер': 4000,
    'Кол-во дней записи архива': 350
}

markup = ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True)

# Словарь для хранения данных всех пользователей
users_data = {}


def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_inputs (
            input_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            facility TEXT,
            input_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()


def save_user_input(conn, user_id, full_name, facility, input_data):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_inputs (user_id, full_name, facility, input_data)
        VALUES (?, ?, ?, ?);
    ''', (user_id, full_name, facility, json.dumps(input_data)))
    conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    full_name = update.effective_user.full_name

    with sqlite3.connect('bot_CCTV_user_info.db')as conn:
        create_table(conn)

    users_data[user_id] = {
        'facility': '',
        'choice': '',
        'Кол-во уличных камер': '',
        'Кол-во внутренних камер': '',
        'Кол-во дней записи архива': '',
        'Кол-во кабеля(по ум. 150 м.)': '',
        'Запись звука': '',
        'Доступ со смартфона': '',
        'АРМ': ''
    }

    await update.message.reply_text(
        f'Приветствуем, {full_name}, начнем расчет. Выберите тип помещения\U00002935',
        reply_markup=markup
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = users_data.get(user_id, {})
    #
    # # if user_data is None:
    # #     user_data = {
    # #         'facility': '',
    # #         'choice': '',
    # #         'Кол-во уличных камер': '',
    # #         'Кол-во внутренних камер': '',
    # #         'Кол-во дней записи архива': '',
    # #         'Кол-во кабеля(по ум. 150 м.)': '',
    # #         'Запись звука': '',
    # #         'Доступ со смартфона': '',
    # #         'АРМ': ''
    # #     }
    users_data[user_id] = user_data
    print(users_data)
    message = update.message.text
    if message == 'Другое':
        await update.message.reply_text(
            text=f'Для расчёта сложных систем рекомендуем обратиться к нашим специалистам',
            reply_markup=ReplyKeyboardMarkup([['Связаться с нами'], ['Оставить заявку']]))
    elif message in [x for lst in main_keyboard for x in lst]:
        user_data['facility'] = message
        await update.message.reply_text(
            text=f'Для расчёта системы видеонаблюдения в {message} потребуется ввести следующие данные:\n'
                 f'Кол-во уличных камер\nКол-во внутренних камер\nКол-во дней записи архива\n'
                 f'Опциональные данные(Кол-во кабеля(по умолчанию 150 м.), Запись звука,'
                 f'Доступ со смартфона, Автоматизированное рабочее место(АРМ/ПК)\n'
                 f'Нажмите на каждую из кнопок и отправьте данные в чат',
            reply_markup=ReplyKeyboardMarkup(info_kb, one_time_keyboard=False))
        print(user_data)
    elif message == 'Вернуться':
        await update.message.reply_text(
            text=f'Для расчёта системы видеонаблюдения в {user_data["facility"]} потребуется ввести следующие данные:\n'
                 f'Кол-во уличных камер\nКол-во внутренних камер\nКол-во дней записи архива\n'
                 f'Опциональные данные(Кол-во кабеля(по умолчанию 150 м.), Запись звука,'
                 f'Доступ со смартфона, Автоматизированное рабочее место(АРМ/ПК)\n'
                 f'Нажмите на каждую из кнопок и отправьте данные в чат',
            reply_markup=ReplyKeyboardMarkup(info_kb, one_time_keyboard=False))
    elif message in data_keys:
        user_data['choice'] = message
        await update.message.reply_text(text=f'Отправьте в чат {message} целым числом', reply_markup=None)
    elif message in [x for lst in optional_kb for x in lst]:
        if message == 'Кол-во кабеля(по ум. 150 м.)':
            user_data['choice'] = message
            await update.message.reply_text(
                text=f'Отправьте в чат {message.rstrip("(по умолчанию 150 м.)").lower()} целым числом',
                reply_markup=None
            )
        elif message == 'Запись звука':
            user_data['choice'] = message
            await update.message.reply_text(
                text=f'Отправьте в чат количество камер требующих запись звука',
                reply_markup=None
            )
        elif message == 'Доступ со смартфона':
            user_data['choice'] = message
            await update.message.reply_text(
                text=f'Отправьте в чат количество гаджетов требующих доступ к просмотру камер',
                reply_markup=None
            )
        elif message == 'АРМ':
            user_data['choice'] = message
            await update.message.reply_text(
                text=f'Отправьте в чат количество автоматизированных рабочих мест(АРМ/ПК).'
                     f'АРМ - это рабочее место, оборудованное компьютерной техникой,'
                     f'программным обеспечением и средствами автоматизации.',
                reply_markup=None
            )


async def nums_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Записываем данные в словарь
    user_id = update.effective_user.id
    user_data = users_data.get(user_id, None)
    if user_data is None:
        user_data = {
            'facility': '',
            'choice': '',
            'Кол-во уличных камер': '',
            'Кол-во внутренних камер': '',
            'Кол-во дней записи архива': '',
            'Кол-во кабеля(по ум. 150 м.)': '',
            'Запись звука': '',
            'Доступ со смартфона': '',
            'АРМ': ''
        }
        users_data[user_id] = user_data

    if update.message.text.isnumeric():
        users_data[user_id][user_data['choice']] = update.message.text
    else:
        await update.message.reply_text(
            text=f'Нужно ввести число, попробуйте снова',
            reply_markup=ReplyKeyboardMarkup(info_kb, one_time_keyboard=False)
        )


async def optional_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=f'Выберите опции', reply_markup=ReplyKeyboardMarkup(optional_kb, one_time_keyboard=False)
    )


def count_price(user_data: dict):
    price = 0
    for n in prices.keys():
        if user_data[n] != '':
            price += int(prices[n]) * int(user_data[n])
    if user_data['Кол-во кабеля(по ум. 150 м.)']:
        price += int(user_data['Кол-во кабеля(по ум. 150 м.)']) * 100
    if user_data['Запись звука']:
        price += int(user_data['Запись звука']) * 1000
    if user_data['Доступ со смартфона']:
        price += int(user_data['Доступ со смартфона']) * 500
    if user_data['АРМ']:
        price += int(user_data['АРМ']) * 10000
    del user_data['choice']
    return price, user_data


async def total_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = users_data.get(user_id, None)

    if user_data is None:
        user_data = {
            'facility': '',
            'choice': '',
            'Кол-во уличных камер': '',
            'Кол-во внутренних камер': '',
            'Кол-во дней записи архива': '',
            'Кол-во кабеля(по ум. 150 м.)': '',
            'Запись звука': '',
            'Доступ со смартфона': '',
            'АРМ': ''
        }
        users_data[user_id] = user_data

    if any([True for x in [y for y in user_data.values() if y.isnumeric()] if int(x) < 0]):
        await update.message.reply_text(
            f'Значения не могут быть меньше нуля, пожалуйста введите корректные данные',
            reply_markup=ReplyKeyboardMarkup(info_kb, one_time_keyboard=False)
        )
    elif user_data['Запись звука'] and int(user_data['Запись звука']) > int(user_data['Кол-во уличных камер']) + int(
            user_data['Кол-во внутренних камер']):
        await update.message.reply_text(
            f'Количество камер со звуком не может превышать общее количество камер,'
            f'пожалуйста измените вводные данные',
            reply_markup=ReplyKeyboardMarkup(info_kb, one_time_keyboard=False)
        )
    elif user_data['Кол-во внутренних камер'] == '' and user_data['Кол-во уличных камер'] == '':
        await update.message.reply_text(
            f'Для правильного расчёта нужно ввести хотя бы одну камеру(уличную или внутреннюю)',
            reply_markup=ReplyKeyboardMarkup(info_kb, one_time_keyboard=False)
        )
    else:
        price, full_info = count_price(user_data)
        await update.message.reply_text(f'Стоимость системы в помещении типа {user_data["facility"]}: {price}\n'
                                        f'Введенные данные: {full_info.items()}')

        await update.message.reply_text(f'Этот расчёт не являюется финальным коммерческим предложением.'
                                        f'Ниже можно ознакомиться со средней разницей суммы в расчете'
                                        f'и договоре на реальных примерах.'
                                        f'Более подробно вас проконсультируют наши специалисты:',
                                        reply_markup=InlineKeyboardMarkup(
                                            [[InlineKeyboardButton('Отправить нам ваш расчёт',
                                                                   callback_data=str('send_calc'))]]))
        # Сохраняем данные пользователя в БД
        with sqlite3.connect('bot_CCTV_user_info.db') as conn:
            save_user_input(conn, user_id, update.effective_user.full_name, user_data['facility'], user_data)


async def send_to_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        'Отправлено. Спасибо за заявку, мы свяжемся с Вами в ближайшее время!',
        reply_markup=None
    )

if __name__ == "__main__":
    application = Application.builder().token("7809531969:AAF-x_Tdm_ojTxxPvwZIrFLL1JGIwoAu0F4").build()

    start_handler = CommandHandler('start', start)
    restart_handler = MessageHandler(filters.Text(['Начать заново']), start)
    price_handler = MessageHandler(filters.Text(['Рассчитать']), total_price)
    nums_handler = MessageHandler(filters.Text([str(n) for n in range(1000)]), nums_collector)
    message_handler = MessageHandler(filters.TEXT, message_handler)
    optional_handler = MessageHandler(filters.Regex(r'Опциональные данные'), optional_handler)
    callback_handler = CallbackQueryHandler(send_to_us, pattern='send_calc')

    application.add_handler(start_handler)
    application.add_handler(restart_handler)
    application.add_handler(nums_handler)
    application.add_handler(price_handler)
    application.add_handler(optional_handler)
    application.add_handler(message_handler)
    application.add_handler(callback_handler)

    application.run_polling(timeout=90)
