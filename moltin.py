import requests
from environs import Env


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


def get_product(access_token):
    pass


def main():
    env = Env()
    env.read_env()
    client_id = env('MOLTIN_CLIENT_ID')
    client_secret = env('MOLTIN_CLIENT_SECRET')
    print(
        get_moltin_access_token(
            client_id,
            client_secret,
        )
    )


if __name__ == '__main__':
    main()
