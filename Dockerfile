# syntax=docker/dockerfile:1

FROM python:3.7-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY ./source ./source

COPY config.ini .

CMD ["python", "./source/main.py", "--host=0.0.0.0"]
