FROM python:3.13.2-slim-bullseye
LABEL authors="昼阳Helios"

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "main.py"]