import os
import redis
import requests
from environs import Env
import textwrap as tw
import time
from transliterate import translit

from properties import (
    flow_properties,
    user_flow_properties,
)


def add_deliverer_for_pizzeria(access_token, deliverer_tg_id):
    flow_slug = flow_properties['slug']
    pizzeries = get_all_entries(access_token, flow_slug)['data']
    for pizzeria in pizzeries:
        values = {
            'id': pizzeria['id'],
            'deliverer_tg_id': deliverer_tg_id,
        }
        update_entry(access_token, values, flow_slug)


def get_cart_sum(access_token, cart_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    answer = response.json()['data']
    total_price = answer['meta']['display_price']['with_tax']['amount']
    return total_price


def get_cart_products(access_token, cart_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    answer = response.json()['data']
    return answer


def get_order_info(products):
    order_info = str()
    for product in products:
        title = product['name']
        price = product['meta']['display_price']['with_tax']['unit']['amount']
        quantity = product['quantity']
        order_info += tw.dedent(f'''
        {title}: ₽{price}
        Количество {quantity} шт;
        ''')
    return order_info


def get_cart_info_products(products):
    products_info = str()
    for product in products:
        title = product['name']
        price = product['meta']['display_price']['with_tax']['unit']['amount']
        quantity = product['quantity']
        description = product['description']
        products_info += tw.dedent(f'''
        {title}
        {description}
        ₽{price}
        Количество {quantity} шт.
        ''')
    return products_info


def create_customer(access_token, email):
    url = 'https://api.moltin.com/v2/customers'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'type': 'customer',
            'name': 'customer',
            'email': email,
        },
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    answer = response.json()['data']
    return answer


def put_product_to_cart(access_token, cart_id, product_id, quantity):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity,
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    answer = response.json()
    return answer


def create_cart(access_token, user_id):
    url = 'https://api.moltin.com/v2/carts'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'name': f'{user_id}`s cart',
        }
    }
    response = requests.post(url, headers=headers, json=json_data,)
    response.raise_for_status()
    answer = response.json()['data']['id']
    return answer


def remove_cart_item(access_token, cart_id, product_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    answer = response.json()
    return answer


def get_cart_products(access_token, cart_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    answer = response.json()['data']
    return answer


def get_all_entries(access_token, flow_slug):
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    answer = response.json()
    return answer


def get_all_fields_by_flow(access_token, flow_slug):
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/fields'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    answer = response.json()
    return answer


def create_entry(access_token, values, flow_slug):
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'
    headers = {
        'Authorization': f'{access_token}',
    }
    json_data = {
        'data': {
            'type': 'entry',
        },
    }
    json_data['data'].update(
        values
    )
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    answer = response.json()
    return answer


def update_entry(access_token, values, flow_slug):
    entry_id = values['id']
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries/{entry_id}'
    headers = {
        'Authorization': f'{access_token}',
    }
    json_data = {
        'data': {
            'type': 'entry',
        },
    }
    json_data['data'].update(
        values
    )
    response = requests.put(url, headers=headers, json=json_data)
    response.raise_for_status()
    answer = response.json()
    return answer


def create_fields_to_flow(access_token, flow_id, fields_for_flow):
    url = 'https://api.moltin.com/v2/fields'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'type': 'field',
        },
    }
    answers = list()
    for field in fields_for_flow:
        json_data['data'].update(
            {
                'name': field['name'],
                'slug': field['slug'],
                'field_type': field['field_type'],
                'description': field['description'],
                'required': True,
                'enabled': True,
                'omit_null': False,
                'relationships':
                {
                    'flow':
                    {
                        'data':
                        {
                            'type': 'flow',
                            'id': flow_id,
                        },
                    },
                },
            }
        )
        response = requests.post(url, headers=headers, json=json_data)
        response.raise_for_status()
        answers.append(response.json())
    return answers


def create_field_to_flow(access_token, flow_id, fields_for_flow):
    url = 'https://api.moltin.com/v2/fields'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'type': 'field',
        },
    }
    json_data['data'].update(
        {
            'name': fields_for_flow['name'],
            'slug': fields_for_flow['slug'],
            'field_type': fields_for_flow['field_type'],
            'description': fields_for_flow['description'],
            'required': True,
            'enabled': True,
            'omit_null': False,
            'relationships':
            {
                'flow':
                {
                    'data':
                    {
                        'type': 'flow',
                        'id': flow_id,
                    },
                },
            },
        }
    )
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    answer = response.json()
    return answer


def save_flow_info_to_txt(answer):
    flow_name = answer['data']['slug']
    flow_id = answer['data']['id']
    os.makedirs('flows_info', exist_ok=True)
    folder = 'flows_info'
    with open(os.path.join(folder, f'flow_{flow_name}.txt'), 'w')as file:
        file.write(flow_id)


def get_flow_id(filename):
    folder = 'flows_info'
    with open(os.path.join(folder, filename))as file:
        flow_id = file.read()
    return flow_id


def add_flow(access_token, flow_properties):
    url = 'https://api.moltin.com/v2/flows'
    headers = {
        'Authorization': f'{access_token}',
    }
    json_data = {
        'data': {
            'type': 'flow',
            'name': flow_properties['name'],
            'slug': flow_properties['slug'],
            'description': flow_properties['description'],
            'enabled': True,
        },
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    answer = response.json()
    save_flow_info_to_txt(answer)
    return answer


def create_currency(access_token):
    url = 'https://api.moltin.com/v2/currencies'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'type': 'currency',
            'code': 'RUB',
            'exchange_rate': 1,
            'format': '₽{price}',
            'decimal_point': '.',
            'thousand_separator': ',',
            'decimal_places': 2,
            'default': True,
            'enabled': True,
        },
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    answer = response.json()
    return answer


def get_moltin_access_token_info(client_id, client_secret):
    url = 'https://api.moltin.com/oauth/access_token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    answer = response.json()
    return answer


def update_access_token(access_token_info, client_id, client_secret):
    curret_time = time.time()
    birth_time = access_token_info['expires']
    lifetime = access_token_info['expires_in']
    access_token = access_token_info['access_token']
    if curret_time > (birth_time + lifetime):
        return get_moltin_access_token_info(client_id, client_secret)['access_token']
    return access_token


def create_main_image(access_token, product_id, file_id):
    url = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'type': 'main_image',
            'id': file_id,
        },
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    answer = response.json()
    return answer


def get_img(access_token, product_detail):
    image_id = product_detail['relationships']['main_image']['data']['id']
    url = f'https://api.moltin.com/v2/files/{image_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    answer = response.json()
    image_url = answer['data']['link']['href']
    return image_url


def upload_image(access_token, product):
    image_url = product.get('product_image')
    url = 'https://api.moltin.com/v2/files'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    files = {
        'file_location': (None, image_url.get('url')),
    }
    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()
    answer = response.json()
    return answer


def create_product(access_token, product):
    url = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'type': 'product',
            'name': product['name'],
            'slug': translit(product['name'], reversed=True),
            'sku': str(product['id']),
            'description': product['description'],
            'manage_stock': False,
            'price': [
                {
                    'amount': product['price'],
                    'currency': 'RUB',
                    'includes_tax': True,
                },
            ],
            'status': 'live',
            'commodity_type': 'physical',
        },
    }

    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    answer = response.json()
    return answer


def get_products(access_token):
    url = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    answer = response.json()
    return answer


def get_product_detail(access_token, product_id):
    url = f'https://api.moltin.com/v2/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    answer = response.json()['data']
    return answer


def get_product_info(product_detail):
    price = product_detail['meta']['display_price']['with_tax']['amount']
    title = product_detail['name']
    description = product_detail['description']
    return tw.dedent(f'''
    {title} ₽{price}.

    {description}
    ''')


def get_all_pizzas():
    url = 'https://dvmn.org/media/filer_public/a2/5a/a25a7cbd-541c-4caf-9bf9-70dcdf4a592e/menu.json'
    response = requests.get(url)
    response.raise_for_status()
    answer = response.json()
    return answer


def get_addresses():
    url = 'https://dvmn.org/media/filer_public/90/90/9090ecbf-249f-42c7-8635-a96985268b88/addresses.json'
    response = requests.get(url)
    response.raise_for_status()
    answer = response.json()
    return answer


def add_addressee(access_token, context):
    flow_slug = user_flow_properties['slug']
    addressee = context.user_data['addressee']
    addressee_lon, addressee_lat = addressee
    devivery_cart_id = context.user_data['devivery_cart_id']
    user_id = context.user_data['user_id']
    values = {
        'user_id': user_id,
        'cart_id': devivery_cart_id,
        'lon': addressee_lon,
        'lat': addressee_lat,
    }
    try:
        create_entry(access_token, values, flow_slug)
    except requests.exceptions.HTTPError as err:
        print(err)
    return 'Upload complided'


def add_addresses(access_token):
    addresses = get_addresses()
    flow_slug = flow_properties['slug']
    for address in addresses:
        try:
            values = {
                'address': address['address']['full'],
                'alias': address['alias'],
                'lon': float(address['coordinates']['lon']),
                'lat': float(address['coordinates']['lat']),
            }
            create_entry(access_token, values, flow_slug)
        except requests.exceptions.HTTPError as err:
            print(err)
    return 'Upload complided'


def connect_db():
    env = Env()
    env.read_env()
    db = redis.Redis(
        host=env('REDIS_HOST'),
        password=env('REDIS_PASSWORD'),
        port=env('REDIS_PORT'),
        decode_responses=True,
    )
    return db
