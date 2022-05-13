#!/usr/bin/env python
import requests


def dowload_json(url):
    response = requests.get(url)
    response.raise_for_status()
    answer = response.json()
    return answer

def main():
    addresses = dowload_json('https://dvmn.org/media/filer_public/a2/5a/a25a7cbd-541c-4caf-9bf9-70dcdf4a592e/menu.json')
    print(addresses)
    print()
    menu = dowload_json('https://dvmn.org/media/filer_public/a2/5a/a25a7cbd-541c-4caf-9bf9-70dcdf4a592e/menu.json')
    print(menu)


if __name__ == '__main__':
    main()
