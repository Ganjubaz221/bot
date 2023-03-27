import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)

from config import BOT_TOKEN, SBERBANK_ACCOUNT, TINKOFF_ACCOUNT, QIWI_ACCOUNT

# Инициализация логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определение состояний бота
(
    SELECT_ACTION,
    ENTER_AMOUNT,
    SELECT_PAYMENT_METHOD,
    SEND_BTC_ADDRESS,
    PAYMENT_CONFIRMATION,
) = range(5)

# ... здесь импортируйте Binance API и функции для работы с курсами и конвертацией ...
from binance import BinanceRestApi
from config import EXCHANGE_MARKUP

api_key = "zX6iKEIMBXY9dJyyz2a1etoKCEYcVtrAI4JqPrvc0ihVQWxGDCZyNYBpMiGOR66w"
api_secret = "s80evkPVnOF6kk6nDkN1UwdyQdB446M3pxsSbaZtostVn2j34i8vSU3BuQjG3EFc"

client = BinanceRestApi(api_key, api_secret)

def get_btc_rub_price():
    ticker_price = client.get_ticker_price("BTCRUB")
    return float(ticker_price["price"])

def calculate_price(amount_btc: float, is_buying: bool) -> float:
    btc_rub_price = get_btc_rub_price()
    markup = 1 + (EXCHANGE_MARKUP / 100) if is_buying else 1 - (EXCHANGE_MARKUP / 100)
    return amount_btc * btc_rub_price * markup

def convert_rub_to_btc(amount_rub: float, is_buying: bool) -> float:
    btc_rub_price = get_btc_rub_price()
    markup = 1 + (EXCHANGE_MARKUP / 100) if is_buying else 1 - (EXCHANGE_MARKUP / 100)
    return amount_rub / (btc_rub_price * markup)


#get_bank_acoount функция
import config

def get_bank_account(payment_method: str) -> str:
    if payment_method == "sberbank":
        return config.SBERBANK_ACCOUNT
    elif payment_method == "tinkoff":
        return config.TINKOFF_ACCOUNT
    elif payment_method == "qiwi":
        return config.QIWI_ACCOUNT
    else:
        raise ValueError("Invalid payment method")


#Обработчики команд
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CallbackQueryHandler

# Функция-обработчик для команды /start
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        ["Купить BTC", "Продать BTC"],
        ["Поддержка"],
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        "Приветственное сообщение.\n\nВыберите действие:",
        reply_markup=reply_markup,
    )

# Функция-обработчик для покупки BTC
def buy_btc(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Укажите сумму в BTC или же RUB:\n\nПример: 0.1 или 0,01 или 3940")

# Функция-обработчик для продажи BTC
def sell_btc(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Укажите сумму в BTC или же RUB:\n\nПример: 0.1 или 0,01 или 3940")

# Функция-обработчик для поддержки
def support(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f"Если у вас возникли вопросы, пожалуйста, свяжитесь с оператором {SUPPORT_USERNAME}")

# Функция-обработчик для ввода суммы покупки/продажи
def enter_amount(update: Update, context: CallbackContext) -> None:
    amount = update.message.text.replace(',', '.')
    if amount.isdigit():
        amount_rub = float(amount)
        amount_btc = convert_rub_to_btc(amount_rub, True)
    else:
        amount_btc = float(amount)
        amount_rub = calculate_price(amount_btc, True)
    
    context.user_data["amount_btc"] = amount_btc
    context.user_data["amount_rub"] = amount_rub

    update.message.reply_text(f"Вы получите: {amount_btc} BTC\n\nДля продолжения выберите способ оплаты:")

    keyboard = [
        [InlineKeyboardButton("Сбербанк", callback_data=f"payment_method:sberbank")],
        [InlineKeyboardButton("Тинькофф", callback_data=f"payment_method:tinkoff")],
        [InlineKeyboardButton("Qiwi кошелек", callback_data=f"payment_method:qiwi")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите способ оплаты:", reply_markup=reply_markup)

# Функция-обработчик для выбора способа оплаты
def select_payment_method(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    payment_method = query.data.split(':')[1]
    context.user_data["payment_method"] = payment_method

    query.edit_message_text(f"Выбран способ оплаты: {payment_method}\n\nВведите ваш BTC кошелек:")

# Функция-обработчик для отправки BTC кошелька
def send_btc_address(update: Update, context: CallbackContext) -> None:
    btc_address = update.message.text
    context.user_data["btc_address"] = btc_address

    payment_method = context.user_data["payment_method"]
    amount_rub = context.user_data["amount_rub"]

    update.message.reply_text(f"Время на оплату заявки: 20 минут!\n\n"
                              f"Итого к оплате: {amount_rub} рублей\n\n"
                              f"После оплаты средства будут переведены на кошелек: {btc_address}\n\n"
                              f"Если у вас возникли проблемы с оплатой, напишите оператору @Pav_Glash")

    keyboard = [
        ["Отмена", "Согласен"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Подтвердите оплату:", reply_markup=reply_markup)

# Функция-обработчик для подтверждения оплаты
def payment_confirmation(update: Update, context: CallbackContext) -> None:
    confirmation = update.message.text.lower()
    
    if confirmation == "согласен":
        payment_method = context.user_data["payment_method"]
        bank_account = get_bank_account(payment_method)
        update.message.reply_text(f"Номер карты банка: {bank_account}\n\n"
                                  f"После оплаты нажмите кнопку 'Оплатил'", reply_markup=ReplyKeyboardRemove())
    elif confirmation == "отмена":
        start(update, context)
    else:
        update.message.reply_text("Выберите одну из предложенных опций: 'Отмена' или 'Согласен'")

# cancel-обработчик
def cancel(update: Update, context: CallbackContext) -> None:
    # Возвращаем пользователя на главный экран с тремя кнопками
    start(update, context)

# paid-обработчик
def paid(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user = update.effective_user

    # Отправляем сообщение в чат с информацией о том, что пользователь оплатил
    context.bot.send_message(
        chat_id=config.CHAT_ID,
        text=f'Пользователь {user.first_name} сказал, что перевел деньги на указанные реквизиты.'
    )

    # Возвращаем пользователя на главный экран с тремя кнопками
    start(update, context)

#Конец замены

from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler

# Остальные импорты и определения функций ...


# Определение состояний для ConversationHandler
SELECT_ACTION, ENTER_AMOUNT, SELECT_PAYMENT_METHOD, SEND_BTC_ADDRESS, PAYMENT_CONFIRMATION, CANCEL = range(6)

def main():
    updater = Updater(config.BOT_TOKEN)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_ACTION: [
                CallbackQueryHandler(buy_btc, pattern='^buy_btc$'),
                CallbackQueryHandler(sell_btc, pattern='^sell_btc$'),
                CallbackQueryHandler(support, pattern='^support$'),
            ],
            ENTER_AMOUNT: [MessageHandler(Filters.text, enter_amount)],
            SELECT_PAYMENT_METHOD: [CallbackQueryHandler(select_payment_method, pattern='^(sberbank|tinkoff|qiwi)$')],
            SEND_BTC_ADDRESS: [MessageHandler(Filters.text, send_btc_address)],
            PAYMENT_CONFIRMATION: [CallbackQueryHandler(payment_confirmation, pattern='^accept$'), CallbackQueryHandler(cancel, pattern='^cancel$')],
            CANCEL: [CommandHandler('cancel', cancel)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('paid', paid))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

