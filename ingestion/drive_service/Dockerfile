FROM python:3.10-slim 

WORKDIR /app

COPY main.py log.py constants.py requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

