FROM python:3.10-alpine
WORKDIR /usr/src/app
COPY . .
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python", "bot.py"]
