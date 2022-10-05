# Пиццерия в Телеграм.

Бот-Магазин в Телеграм  `bot.py` на основе [elastic path](https://www.elasticpath.com/), [инструкция как создать бота в Телеграм](https://way23.ru/%D1%80%D0%B5%D0%B3%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%86%D0%B8%D1%8F-%D0%B1%D0%BE%D1%82%D0%B0-%D0%B2-telegram.html).
Также использует виртуальные базы данных [Redis](https://app.redislabs.com/#/login), [инструкция по созданию бд Redis](https://pythonru.com/biblioteki/redis-python)

### Чувствительные данные

Для хранения используем переменные окружения и файл .env

Пример файла `.env`:

`TG_TOKEN=токен вашего телеграм бота` Можно получить у [@BotFather](https://way23.ru/%D1%80%D0%B5%D0%B3%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%86%D0%B8%D1%8F-%D0%B1%D0%BE%D1%82%D0%B0-%D0%B2-telegram.html)

`TG_CHAT_ID=ваш чат id` Сюда телеграм бот будет слать уведомления об ошибках

`REDIS_HOST=Redis host для бота Телеграм` можно получить в [личном кабинете](https://app.redislabs.com/#/login)

`REDIS_PORT=Redis port для бота Телеграм` можно получить в [личном кабинете](https://app.redislabs.com/#/login)

`REDIS_PASSWORD=Redis password для бота Телеграм` можно получить в [личном кабинете](https://app.redislabs.com/#/login)

`MOLTIN_CLIENT_ID=id клиента` можно получить в [личном кабинете](https://documentation.elasticpath.com/commerce-cloud/docs/concepts/security.html)

`MOLTIN_CLIENT_SECRET=секретный ключ клиента` можно получить [личном кабинете](https://documentation.elasticpath.com/commerce-cloud/docs/concepts/security.html)
`PAYMENT_TOKEN=платежныый токен` Можно получить у [@BotFather](https://way23.ru/%D1%80%D0%B5%D0%B3%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%86%D0%B8%D1%8F-%D0%B1%D0%BE%D1%82%D0%B0-%D0%B2-telegram.html)


### Как установить

Клонировать репозиторий
```bash
git clone git@github.com:CaDiBob/lesson_6.git
```

Python3 должен быть установлен затем используйте `pip`

```bash
pip install -r requirements.txt
```

### Как запустить

```bash
python bot.py
```
### Как запустить используя docker-compose

Клонировать репозиторий
```bash
git clone git@github.com:CaDiBob/lesson_6.git
```
[Docker и Docker-compose](https://docs.docker.com/get-docker/) должены быть установлены.

Затем нужно собрать контейнер командой:

```bash
sudo docker-compose build
```
И запустить его:
```bash
sudo docker-compose up -d
```
[Cсылка на бота Телеграм](https://t.me/CaD_pizza_shop_bot)

![](gif/pizza_bot.gif)

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).
