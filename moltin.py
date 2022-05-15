import json
import requests
from environs import Env
from pprint import pprint


from transliterate import translit

from fields import fields


def create_field_to_flow(access_token, field, flow_id):
    url = 'https://api.moltin.com/v2/fields'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'type': 'field',
            'name': field,
            'slug': field,
            'field_type': 'string',
            'validation_rules': [],
            'description': field,
            'required': True,
            'default': 0,
            'enabled': True,
            'relationships': {
                'flow': {
                    'data': {
                        'type': 'flow',
                        'id': flow_id,
                    },
                },
            },
        },
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    answer = response.json()
    return answer

def create_flow(access_token):
    url = 'https://api.moltin.com/v2/flows'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    json_data = {
        'data': {
            'type': 'flow',
            'name': 'Pizzeria',
            'slug': 'Pizzeria',
            'description': 'Адреса и координаты пицерий',
            'enabled': True,
        },
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    answer = response.json()
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


def get_moltin_access_token(client_id, client_secret):
    url = 'https://api.moltin.com/oauth/access_token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    answer = response.json()['access_token']
    return answer


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


def get_all_pizzas():
    url = 'https://dvmn.org/media/filer_public/a2/5a/a25a7cbd-541c-4caf-9bf9-70dcdf4a592e/menu.json'
    response = requests.get(url)
    response.raise_for_status()
    answer = response.json()
    return answer


def main():
    env = Env()
    env.read_env()
    client_id = env('MOLTIN_CLIENT_ID')
    client_secret = env('MOLTIN_CLIENT_SECRET')
    access_token = get_moltin_access_token(
        client_id,
        client_secret,
    )
    flow_id = create_flow(access_token)['data']['id']
    for field in fields:
        print(create_field_to_flow(access_token, field, flow_id))
    exit()
    create_currency(access_token)
    products = get_all_pizzas()

    for product in products:
        try:
            product_id = create_product(access_token, product)['data']['id']
            file_id = upload_image(access_token, product)['data']['id']
            print(create_main_image(access_token, product_id, file_id))
        except Exception:
            print(f'Не загрузилась: {product.get("name")}')
            continue


if __name__ == '__main__':
    main()
