import logging
import redis
import telegram
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    Filters,
    Updater,
)
from environs import Env
from geocoder import fetch_coordinates
from moltin import (
    connect_db,
    create_cart,
    get_cart_products,
    get_img,
    get_products,
    get_product_detail,
    get_product_info,
    get_cart_info_products,
    get_cart_sum,
    put_product_to_cart,
    remove_cart_item
)


HANDLE_MENU, HANDLE_DESCRIPTION, HANDLE_CART, HANDLE_WAITING = range(4)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class TelegramLogsHandler(logging.Handler):

    def __init__(self, chat_id, bot):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def handle_menu(update, context):
    logger.info('handle_menu')
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id
    db = context.bot_data['db']
    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']
    products = get_products(context, client_id, client_secret)
    context.user_data['products'] = products
    if not db.get(f'for_car_{user_id}'):
        cart_id = create_cart(context, client_id, client_secret, user_id)
        db.set(f'for_car_{user_id}', cart_id)
    cart_id = db.get(f'for_car_{user_id}')
    context.user_data['cart_id'] = cart_id
    bot = context.bot
    user_id = update.effective_user.id
    text = 'Добро пожаловать в нашу сеть пиццерий "Пиццеляндия"!'
    keyboard = list()
    for product in products['data']:
        keyboard.append(
            [
                InlineKeyboardButton(
                    product['name'],
                    callback_data=product['id']
                )
            ],
        )
    keyboard.append(
        [
            InlineKeyboardButton('Корзина', callback_data='Корзина')
        ]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        text=text,
        chat_id=user_id,
        reply_markup=reply_markup,
    )
    return HANDLE_DESCRIPTION


def handle_description(update, context):
    logger.info('handle_description')
    bot = context.bot
    user_id = update.effective_user.id
    product_id = update.callback_query.data
    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']
    context.user_data['product_id'] = product_id
    product_detail = get_product_detail(
        context, client_id, client_secret, product_id)
    product_info = get_product_info(product_detail)
    url_img = get_img(context, client_id, client_secret, product_detail)
    keyboard = [
        [InlineKeyboardButton('Положить в корзину',
                              callback_data='Положить в корзину')],
        [InlineKeyboardButton('Назад', callback_data='Назад')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_photo(
        photo=url_img,
        caption=product_info,
        chat_id=user_id,
        reply_markup=reply_markup,
    )
    return HANDLE_DESCRIPTION


def add_product_to_cart(update, context):
    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']
    cart_id = context.user_data['cart_id']
    product_id = context.user_data['product_id']
    put_product_to_cart(context, client_id, client_secret,
                        cart_id, product_id, quantity=1)
    return HANDLE_DESCRIPTION


def cart_info(update, context):
    bot = context.bot
    user_id = update.effective_user.id
    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']
    cart_id = context.user_data['cart_id']
    cart_products = get_cart_products(
        context, client_id, client_secret, cart_id)
    cart_info = get_cart_info_products(cart_products)
    cart_sum = get_cart_sum(context, client_id, client_secret, cart_id)
    keyboard = list()
    for product in cart_products:
        title = product['name']
        context.user_data['title'] = title
        product_id = product['id']
        keyboard.append(
            [
                InlineKeyboardButton(
                    f'Удалить из корзины {title}',
                    callback_data=product_id,
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                'В меню',
                callback_data='В меню',
            )
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                'Оплатить',
                callback_data='Оплатить',
            )
        ]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        text=f'{cart_info}\n{cart_sum}',
        chat_id=user_id,
        reply_markup=reply_markup,
    )
    return HANDLE_CART


def remove_item(update, context):
    bot = context.bot
    user_id = update.effective_user.id
    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']
    cart_id = context.user_data['cart_id']
    product_id = update.callback_query.data
    title = context.user_data['title']
    keyboard = [
        [InlineKeyboardButton('Корзина', callback_data='Корзина')]
    ]
    remove_cart_item(context, client_id, client_secret, cart_id, product_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        text=f'Товар {title} удален из корзины',
        chat_id=user_id,
        reply_markup=reply_markup,
    )
    return HANDLE_CART


def handle_waiting(update, context):
    bot = context.bot
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton('Корзина', callback_data='Корзина')],
        [InlineKeyboardButton('В меню', callback_data='В меню')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        text='''
        Хорошо, Пришлите нам ваш адрес текстом или геолокацию.
        ''',
        chat_id=user_id,
        reply_markup=reply_markup,
    )
    return HANDLE_WAITING


def check_coordinates(update, context):
    message = update.message
    current_position = (message.location.longitude, message.location.latitude)
    coords = f'{current_position[0]},{current_position[1]}'
    address_str = fetch_coordinates(coords)
    update.message.reply_text(address_str)
    return HANDLE_WAITING


def check_address(update, context):
    coords = update.message.text
    address_str = fetch_coordinates(coords)
    if not address_str:
        update.message.reply_text('Введите корректный адрес')
    update.message.reply_text(address_str)
    return HANDLE_WAITING


def cancel(update, context):
    update.message.reply_text(
        'До свидания! Мы всегда рады вам.'
    )
    return ConversationHandler.END


def error(update, context):
    logger.error(context.error)


def main():
    env = Env()
    env.read_env()
    db = connect_db()
    tg_token = env('TG_TOKEN')
    tg_chat_id = env('TG_CHAT_ID')
    client_id = env('MOLTIN_CLIENT_ID')
    client_secret = env('MOLTIN_CLIENT_SECRET')
    updater = Updater(tg_token)
    bot = telegram.Bot(tg_token)
    logger.addHandler(TelegramLogsHandler(tg_chat_id, bot))
    dispatcher = updater.dispatcher
    dispatcher.bot_data['client_id'] = client_id
    dispatcher.bot_data['client_secret'] = client_secret
    dispatcher.bot_data['db'] = db

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', handle_menu)],
        states={
            HANDLE_MENU: [
                CallbackQueryHandler(handle_menu),
            ],
            HANDLE_DESCRIPTION: [
                CallbackQueryHandler(cart_info, pattern=r'Корзина'),
                CallbackQueryHandler(handle_menu, pattern=r'Назад'),
                CallbackQueryHandler(
                    add_product_to_cart,
                    pattern=r'Положить в корзину'
                ),
                CallbackQueryHandler(handle_description, pattern=r'[0-9]'),
            ],
            HANDLE_CART: [
                CallbackQueryHandler(cart_info, pattern=r'Корзина'),
                CallbackQueryHandler(handle_waiting, pattern=r'Оплатить'),
                CallbackQueryHandler(handle_menu, pattern=r'В меню'),
                CallbackQueryHandler(remove_item),
            ],
            HANDLE_WAITING: [
                MessageHandler(Filters.location, check_coordinates),
                MessageHandler(Filters.text & ~Filters.command, check_address),
                CallbackQueryHandler(handle_waiting, pattern=r'Ввести снова'),
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
