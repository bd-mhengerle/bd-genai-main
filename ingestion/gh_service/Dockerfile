FROM python:3.10-slim 

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y git
RUN apt-get install -y wkhtmltopdf

COPY requirements.txt convert.py log.py constants.py /app/

RUN pip install -r requirements.txt




