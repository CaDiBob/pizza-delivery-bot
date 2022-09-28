import requests
from environs import Env
from geopy import distance
from moltin import get_all_entries
from properties import flow_properties
import textwrap as tw


def fetch_coordinates(address):
    env = Env()
    env.read_env()
    yandex_apikey = env.str('YANDEX_GEOCODER_API')
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": yandex_apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json(
    )['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return float(lon), float(lat)


def get_distance(access_token, addressee):
    addressee_lon, addressee_lat = addressee
    flow_slug = flow_properties['slug']
    pizzerias_addresses = get_all_entries(access_token, flow_slug)['data']
    distances = list()
    for pizzeria_address in pizzerias_addresses:
        one_route = dict()
        address = pizzeria_address['address']
        lon = pizzeria_address['lon']
        lat = pizzeria_address['lat']
        distance_for_order = round(
            distance.distance((addressee_lat, addressee_lon),
                              (lat, lon)).meters,
        )
        one_route.update(
            {
                'address': address,
                'distance': distance_for_order,
            }
        )
        distances.append(one_route)
    return distances


def get_text_distance(distances):
    order_distances = [distance['distance'] for distance in distances]
    min_order_distance = min(order_distances)
    if min_order_distance in range(0, 501):
        pizzeria_address = [
            distance['address']
            for distance in distances if min_order_distance == distance['distance']
        ]
        pizzeria_address , *_ = pizzeria_address
        return tw.dedent(f'''
        Может, зберете пиццу из нашей пиццерии неподалеку?
        она всего в {min_order_distance} метрах от вас!
        Вот её адрес: {pizzeria_address}
        А можем и беплатно доставить, нам не сложно.
        ''')
    elif min_order_distance in range(502, 5001):
        return tw.dedent(f'''
        Похоже к вам придется ехать. Доствака будет стоить 100 рубдей.
        Доставка или самовывоз?
        ''')
    elif min_order_distance in range(5002, 20001):
        return tw.dedent(f'''
        Похоже к вам придется ехать. Доствака будет стоить 300 рубдей.
        Доставка или самовывоз?
        ''')
    else:
        min_order_distance = min_order_distance / 1000
        return tw.dedent(f'''
        Извините так далеко мы пиццу не доставим. Ближайщая пиццерия
        аж в {min_order_distance} километрах от вас
        ''')
