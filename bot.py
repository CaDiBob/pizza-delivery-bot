import logging
import textwrap as tw

import telegram
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, Filters, MessageHandler,
                          PreCheckoutQueryHandler, Updater)

from geocoder import (fetch_coordinates, get_delivery_info,
                      get_min_distance)
from moltin import (add_addressee, connect_db, create_cart,
                    get_cart_info_products, get_cart_products, get_cart_sum,
                    get_img, get_moltin_access_token_info, get_product_detail,
                    get_product_info, get_products, put_product_to_cart,
                    remove_cart_item, update_access_token,)

(
    HANDLE_MENU,
    HANDLE_DESCRIPTION,
    HANDLE_CART,
    HANDLE_WAITING,
    HANDLE_DELIVERY,
    HANDLE_USER_REPLY,
) = range(6)

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
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id
    db = connect_db()
    access_token = context.bot_data['access_token']
    products = get_products(access_token)
    context.user_data['products'] = products
    if not db.get(f'for_cart_{user_id}'):
        cart_id = create_cart(access_token, user_id)
        db.set(f'for_cart_{user_id}', cart_id)
    cart_id = db.get(f'for_cart_{user_id}')
    context.user_data['cart_id'] = cart_id
    bot = context.bot
    text = 'Добро пожаловать в нашу сеть пиццерий "Пиццеляндия"!'

    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        for product in products['data']
    ]
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
    bot = context.bot
    user_id = update.effective_user.id
    product_id = update.callback_query.data
    access_token = context.bot_data['access_token']
    context.user_data['product_id'] = product_id
    product_detail = get_product_detail(access_token, product_id)
    product_info = get_product_info(product_detail)
    url_img = get_img(access_token, product_detail)
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
    access_token = context.bot_data['access_token']
    cart_id = context.user_data['cart_id']
    product_id = context.user_data['product_id']
    put_product_to_cart(access_token, cart_id, product_id, quantity=1)
    update.callback_query.answer('Товар добавлен в корзину')
    return HANDLE_DESCRIPTION


def cart_info(update, context):
    bot = context.bot
    user_id = update.effective_user.id
    access_token = context.bot_data['access_token']
    cart_id = context.user_data['cart_id']
    cart_products = get_cart_products(access_token, cart_id)
    cart_info = get_cart_info_products(cart_products)
    cart_sum = get_cart_sum(access_token, cart_id)
    context.user_data['cart_sum'] = cart_sum
    context.user_data['cart_info'] = cart_info
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
    text = f'{cart_info}\nОбщая сумма товаров: ₽{cart_sum}'
    bot.send_message(
        text=text,
        chat_id=user_id,
        reply_markup=reply_markup,
    )
    return HANDLE_CART


def remove_item(update, context):
    bot = context.bot
    user_id = update.effective_user.id
    access_token = context.bot_data['access_token']
    cart_id = context.user_data['cart_id']
    product_id = update.callback_query.data
    title = context.user_data['title']
    keyboard = [
        [InlineKeyboardButton('Корзина', callback_data='Корзина')]
    ]
    remove_cart_item(access_token, cart_id, product_id)
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


def check_tg_location(update, context):
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id
    access_token = context.bot_data['access_token']
    message = update.message
    current_position = (message.location.longitude, message.location.latitude)
    coords = f'{current_position[0]},{current_position[1]}'
    addressee = fetch_coordinates(coords)
    context.user_data['addressee'] = addressee
    min_distance_to_order = get_min_distance(access_token, context)
    context.user_data['min_distance_to_order'] = min_distance_to_order
    keyboard = [
        [InlineKeyboardButton('Доставка', callback_data='Доставка')],
        [InlineKeyboardButton('Самовывоз', callback_data='Самовывоз')],
        [InlineKeyboardButton('Корзина', callback_data='Корзина')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    delivery_info = get_delivery_info(context, min_distance_to_order)
    update.message.reply_text(delivery_info, reply_markup=reply_markup)
    return HANDLE_DELIVERY


def check_address_text(update, context):
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id
    access_token = context.bot_data['access_token']
    coords = update.message.text
    addressee = fetch_coordinates(coords)
    context.user_data['addressee'] = addressee
    if not addressee:
        update.message.reply_text('Введите корректный адрес')
    min_distance_to_order = get_min_distance(access_token, context)
    context.user_data['min_distance_to_order'] = min_distance_to_order
    keyboard = [
        [InlineKeyboardButton('Доставка', callback_data='Доставка')],
        [InlineKeyboardButton('Самовывоз', callback_data='Самовывоз')],
        [InlineKeyboardButton('Корзина', callback_data='Корзина')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    delivery_info = get_delivery_info(context, min_distance_to_order)
    update.message.reply_text(delivery_info, reply_markup=reply_markup)
    return HANDLE_DELIVERY


def send_delivery_info_to_deliverer(context):
    access_token = context.bot_data['access_token']
    addressee = context.user_data['addressee']
    bot = context.bot
    min_distance_to_order = context.user_data['min_distance_to_order']
    addressee_lon, addressee_lat = addressee
    deliverer_tg_id = min_distance_to_order['deliverer_tg_id']
    user_id = context.user_data['user_id']
    db = connect_db()
    devivery_cart_id = db.get(f'for_car_{user_id}')
    context.user_data['devivery_cart_id'] = devivery_cart_id
    add_addressee(access_token, context)
    context.job_queue.run_once(
        send_notification_customer, 3600, context=user_id)
    cart_sum = context.user_data['cart_sum']
    cart_info = context.user_data['cart_info']
    bot.send_message(
        text=tw.dedent(
            f'Новая доставка: {cart_info}\n Сумма: ₽{cart_sum}'
        ),
        chat_id=deliverer_tg_id,
    )
    bot.send_location(
        chat_id=deliverer_tg_id,
        latitude=addressee_lat,
        longitude=addressee_lon,
    )
    return HANDLE_DELIVERY


def send_info_for_pickup(update, context):
    bot = context.bot
    user_id = update.effective_user.id
    min_distance_to_order = context.user_data['min_distance_to_order']
    pizzeria_lon = min_distance_to_order['pizzeria_lon']
    pizzeria_lat = min_distance_to_order['pizzeria_lat']
    pizzeria_address = min_distance_to_order['address']
    keyboard = [
        [InlineKeyboardButton('Меню', callback_data='Меню')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_location(
        chat_id=user_id,
        latitude=pizzeria_lat,
        longitude=pizzeria_lon,
    )
    text = f'Спасибо за оплату!\nБлижайщая пиццерия: {pizzeria_address}'
    bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=reply_markup
    )
    return HANDLE_MENU


def send_notification_customer(context):
    bot = context.bot
    user_id = context.job.context
    text = tw.dedent('''
    Приятного аппетита! *место для рекламы*
    *сообщение что делать если пицца не пришла*
    '''
                     )
    bot.send_message(
        text=text,
        chat_id=user_id
    )


def handle_pickup(update, context):
    query = update.callback_query.data
    context.user_data['delivery_mode'] = query
    cart_sum = context.user_data['cart_sum']
    bot = context.bot
    user_id = update.effective_user.id
    text = tw.dedent(
        f'''
        Вы выбрали cамовывоз, теперь можете оплатить ваш заказ.
        Сумма к оплате: ₽{cart_sum}
        '''
    )
    bot.send_message(
        text=text,
        chat_id=user_id
    )
    context.bot.send_invoice(
        chat_id=user_id,
        title='Оплата заказа из пиццерии',
        description='You here',
        payload='payment-for-pizza',
        provider_token=context.bot_data['payment_token'],
        currency='RUB',
        need_name=True,
        need_phone_number=True,
        prices=[LabeledPrice('Заказ из пиццерии', cart_sum * 100)],
    )
    return HANDLE_USER_REPLY


def handle_delivery(update, context):
    query = update.callback_query.data
    context.user_data['delivery_mode'] = query
    delivery_price = context.user_data['delivery_price']
    cart_sum = context.user_data['cart_sum']
    order_price = delivery_price + cart_sum
    bot = context.bot
    user_id = update.effective_user.id
    text = tw.dedent(
        f'''
        Вы выбрали доставку, теперь можете оплатить ваш заказ.
        Сумма к оплате: ₽{order_price}
        '''
    )
    bot.send_message(
        text=text,
        chat_id=user_id
    )
    context.bot.send_invoice(
        chat_id=user_id,
        title='Оплата заказа из пиццерии',
        description='You here',
        payload='payment-for-pizza',
        provider_token=context.bot_data['payment_token'],
        currency='RUB',
        need_name=True,
        need_phone_number=True,
        prices=[LabeledPrice('Заказ из пиццерии', order_price * 100)],
    )
    return HANDLE_USER_REPLY


def precheckout_callback(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload != 'payment-for-pizza':
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        query.answer(ok=True)
    return HANDLE_USER_REPLY


def successful_payment_callback(update, context):
    query = context.user_data['delivery_mode']
    keyboard = [
        [InlineKeyboardButton('Меню', callback_data='Меню')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if query == 'Доставка':
        send_delivery_info_to_deliverer(context)
        update.message.reply_text(
            'Спасибо! Ваши данные переданы курьеру',
            reply_markup=reply_markup
        )
    if query == 'Самовывоз':
        send_info_for_pickup(update, context)
    return HANDLE_MENU


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
    tg_token = env('TG_TOKEN')
    tg_chat_id = env('TG_CHAT_ID')
    client_id = env('MOLTIN_CLIENT_ID')
    client_secret = env('MOLTIN_CLIENT_SECRET')
    payment_token = env('PAYMENT_TOKEN')
    access_token_info = get_moltin_access_token_info(client_id, client_secret)
    access_token = update_access_token(access_token_info, client_id, client_secret)
    updater = Updater(tg_token)
    bot = telegram.Bot(tg_token)
    logger.addHandler(TelegramLogsHandler(tg_chat_id, bot))
    dispatcher = updater.dispatcher
    dispatcher.bot_data['payment_token'] = payment_token
    dispatcher.bot_data['access_token'] = access_token
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
                MessageHandler(Filters.location, check_tg_location),
                MessageHandler(Filters.text & ~Filters.command,
                               check_address_text),
            ],
            HANDLE_DELIVERY: [
                CallbackQueryHandler(cart_info, pattern='Корзина'),
                CallbackQueryHandler(
                    handle_delivery, pattern='Доставка'
                ),
                CallbackQueryHandler(
                    handle_pickup,
                    pattern='Самовывоз'
                ),
                CallbackQueryHandler(handle_menu, pattern=r'Меню'),
            ],
            HANDLE_USER_REPLY: [
                PreCheckoutQueryHandler(precheckout_callback),
                MessageHandler(Filters.successful_payment,
                               successful_payment_callback),
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_chat=False,
        allow_reentry=True,
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
