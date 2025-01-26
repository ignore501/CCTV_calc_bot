"""CCTV system price calculation telegram bot"""

import logging
import json
import sqlite3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# --- Data ---

prices = {
    "Кол-во уличных камер": 5000,
    "Кол-во внутренних камер": 4000,
    "Кол-во дней записи архива": 350,
}

options = {
    "Кол-во кабеля (по ум. 150 м.)": {
        "label": "Кол-во кабеля (по ум. 150 м.)",
        "price_per_meter": 100,
    },
    "Запись звука": {
        "label": "Запись звука",
        "price_per_camera": 1000,
    },
    "Доступ со смартфона": {
        "label": "Доступ со смартфона",
        "price_per_device": 500,
    },
    "АРМ": {
        "label": "АРМ",
        "price_per_arm": 10000,
    },
}
main_callback = [
    "дом/дача", "квартира", "магазин",
    "лифт", "офис", "склад",
    "ресторан/кафе", "аптека", "автомойка",
    "только улица", "школа", "Другое"
]


# --- Database ---
def create_table(conn):
    # Создаем таблицу в бд, если ее еще нет
    conn.execute('''
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
    conn.execute(
        '''
        INSERT INTO user_inputs (user_id, full_name, facility, input_data)
        VALUES (?, ?, ?, ?);
        ''',
        (user_id, full_name, facility, json.dumps(input_data))
    )
    conn.commit()


# --- Functions ---

def count_price(user_data):
    price = 0
    for key, value in prices.items():
        if user_data.get(key, "") != "":
            price += int(value) * int(user_data[key])
    print(price)
    for opt_type, opt_data in options.items():
        if user_data.get(opt_type, ""):
            if opt_type == "Кол-во кабеля (по ум. 150 м.)":
                price += int(user_data[opt_type]) * opt_data["price_per_meter"]
                print(price, opt_type)
            elif opt_type == "Запись звука":
                price += int(user_data[opt_type]) * opt_data["price_per_camera"]
                print(price, opt_type)
            elif opt_type == "Доступ со смартфона":
                price += int(user_data[opt_type]) * opt_data["price_per_device"]
                print(price, opt_type)
            elif opt_type == "АРМ":
                price += int(user_data[opt_type]) * opt_data["price_per_arm"]
                print(price, opt_type)
    return price, user_data


def create_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Дом/дача", callback_data="дом/дача"),
            InlineKeyboardButton("Квартира", callback_data="квартира"),
            InlineKeyboardButton("Магазин", callback_data="магазин"),
        ],
        [
            InlineKeyboardButton("Лифт", callback_data="лифт"),
            InlineKeyboardButton("Офис", callback_data="офис"),
            InlineKeyboardButton("Склад", callback_data="склад"),
        ],
        [
            InlineKeyboardButton("Ресторан/кафе", callback_data="ресторан/кафе"),
            InlineKeyboardButton("Аптека", callback_data="аптека"),
            InlineKeyboardButton("Автомойка", callback_data="автомойка"),
        ],
        [
            InlineKeyboardButton("Школа", callback_data="школа"),
            InlineKeyboardButton("Другое", callback_data="Другое"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_options_keyboard():
    keyboard = []
    for key in prices:
        keyboard.append(InlineKeyboardButton(key, callback_data=key))
    for opt_type, opt_data in options.items():
        keyboard.append(
            InlineKeyboardButton(opt_data["label"], callback_data=opt_type)
                        )
    keyboard.append(
        InlineKeyboardButton("Рассчитать", callback_data="Рассчитать")
        )
    keyboard = [
        [keyboard[0], keyboard[1]],
        [keyboard[2], keyboard[3]],
        [keyboard[4], keyboard[5]],
        [keyboard[6], keyboard[7]],
        [InlineKeyboardButton("Начать заново", callback_data=str("restart"))]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['first_mes_id'] = update.message.message_id
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name
    context.user_data[user_id] = {}
    print(context.user_data)
    await update.effective_chat.send_message(
        f"<b>?НА ДАННЫЙ МОМЕНТ ТИП ПОМЕЩЕНИЯ СОХР В БАЗУ С РАСЧЁТАМИ."
        f"НА САМ РАСЧЁТ НЕ ВЛИЯЕТ?\n"
        f"Приветствуем, {full_name}!\n"
        f"Для начала расчёта стоимости системы"
        f"видеонаблюдения выберите тип помещения:</b>",
        reply_markup=create_main_keyboard(), parse_mode='HTML'
    )

    with sqlite3.connect('bot_CCTV_user_info.db') as conn:
        create_table(conn)


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        for i in range(
            update.callback_query.message.message_id,
            context.user_data['first_mes_id'], -1
            ):
            await update.effective_chat.delete_message(message_id=i)
    except Exception:
        pass
    finally:
        await update.effective_chat.send_action(action='typing')
        user_id = update.effective_user.id
        full_name = update.effective_user.full_name
        context.user_data[user_id] = {}
        print(context.user_data)
        await update.effective_chat.send_message(
            f"<b>?НА ДАННЫЙ МОМЕНТ ТИП ПОМЕЩЕНИЯ СОХР В БАЗУ С РАСЧЁТАМИ."
            f"НА САМ РАСЧЁТ НЕ ВЛИЯЕТ?\n"
            f"Приветствуем, {full_name}!\n"
            f"Для начала расчёта стоимости системы"
            f"видеонаблюдения выберите тип помещения:</b>",
            reply_markup=create_main_keyboard(), parse_mode='HTML'
        )
        with sqlite3.connect('bot_CCTV_user_info.db') as conn:
            create_table(conn)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data
    user_data = context.user_data.get(user_id)
    print(data)
    try:
        await query.answer()  # Crucial: Answer the query immediately
        if user_data is None:
            user_data = {}
            context.user_data[user_id] = user_data

        if data == "Рассчитать":
            await total_price(update, context)

        elif data in main_callback:
            user_data["facility"] = data
            await query.edit_message_text(
                text=f'<b>Для расчёта системы видеонаблюдения в {data} потребуется ввести следующие данные:\n'
                f'Кол-во уличных камер\nКол-во внутренних камер\nКол-во дней записи архива\n'
                f'Опциональные данные(Кол-во кабеля(по умолчанию 150 м.), Запись звука,'
                f'Доступ со смартфона, Автоматизированное рабочее место(АРМ/ПК)).\n</b>',
                reply_markup=create_options_keyboard(),
                parse_mode='HTML'
            )
        elif data in prices or data in options:
            user_data["choice"] = data
            user_data["facility"] = user_data.get("facility", "")  # Preserve existing facility
            await query.edit_message_text(
                text=f"<b>Введите значение для {options.get(data, {'label': data})['label']}:</b>",
                parse_mode='HTML'
            )
        else:
            await query.answer("Неизвестная команда.")
            return
    except Exception as e:
        print(f"Error in button handler: {e}")
        await query.answer("Ошибка обработки команды.")


async def other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        text='<b>Для расчёта сложных систем рекомендуем обратиться к нашим специалистам.\n'
             '/возможно клиент впишет в открытой форме запрос  отправит нам</b>',
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Начать заново", callback_data=str("restart"))],
                [InlineKeyboardButton("Заказать обратную связь/далее выбор удобного способа",
                callback_data=str("contact"))]
            ]
        ),
        parse_mode='HTML'
    )


async def total_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id)
    if user_data is None:
        return await update.callback_query.edit_message_text(
            "<b>Сначала выберите тип помещения.</b>",
            reply_markup=create_main_keyboard(),
            parse_mode='HTML'
        )
    if 'Кол-во уличных камер' not in user_data.keys() and 'Кол-во внутренних камер' not in user_data.keys():
        await update.callback_query.edit_message_text(
            '<b>Нужно ввести хотя бы <i>ОДНУ</i> камеру(уличную или внутреннюю)</b>',
            reply_markup=create_options_keyboard(),
            parse_mode='HTML'
        )
        return

    price, full_info = count_price(user_data)
    disp_info = '\n'
    for k, v in full_info.items():
        if k not in ['facility', 'choice']:
            disp_info += f'{k}: {v}\n'
    print(user_data)
    await update.callback_query.edit_message_text(
        f"<b>Стоимость системы в помещении типа '{user_data.get('facility', 'Не указано')}': {price}\n"
        f"Введенные данные: {disp_info}\n"
        f"Этот расчёт не являюется финальным коммерческим предложением."
        f"Ниже можно ознакомиться со средней разницей суммы в расчете "
        f"и договоре на реальных примерах. "
        f"Более подробно вас проконсультируют наши специалисты:</b>",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Отправить нам ваш расчёт', callback_data=str('send_calc'))]]),
        parse_mode='HTML'
    )

    await context.bot.send_message(chat_id='7761258753', text='кто-то прошел')
    # Сохраняем данные пользователя в БД
    with sqlite3.connect('bot_CCTV_user_info.db') as conn:
        save_user_input(conn, user_id, update.effective_user.full_name, user_data['facility'], user_data)
        print('saved')


async def send_to_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        '<b>Отправлено. Спасибо за заявку, мы свяжемся с Вами в ближайшее время!</b>',
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton('Вернуться к расчёту', callback_data=str('Рассчитать'))],
                [InlineKeyboardButton('Начать заново', callback_data=str('restart'))]
            ]
        ),
        parse_mode='HTML'
    )


async def nums_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        user_data = context.user_data.get(user_id)
        num = int(update.message.text)
        user_data[user_data["choice"]] = num
        context.user_data[user_id] = user_data
        del user_data['choice']
        await update.message.reply_text(
            "<b>Данные приняты. Выберите следующие параметры.</b>",
            reply_markup=create_options_keyboard(),
            parse_mode='HTML'
        )

    except (ValueError, KeyError):
        if user_data.get('choice', '') == '':
            await update.message.reply_text('<b>Сначала нужно выбрать параметр</b>', parse_mode='HTML')
        else:
            await update.message.reply_text("<b>Пожалуйста, введите целое число.</b>", parse_mode='HTML')


def main():

    application = Application.builder().token("7809531969:AAF-x_Tdm_ojTxxPvwZIrFLL1JGIwoAu0F4").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler((CallbackQueryHandler(restart, pattern='restart')))
    application.add_handler(CallbackQueryHandler(send_to_us, pattern='send_calc'))
    application.add_handler(CallbackQueryHandler(other, pattern='Другое'))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT, nums_collector))
    application.run_polling(timeout=30)


if __name__ == "__main__":
    main()
