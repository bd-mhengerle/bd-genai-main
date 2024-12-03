FROM python:3.10-slim

WORKDIR /app

RUN mkdir -p /app/images

COPY requirements.txt constants.py main.py models.py log.py /app/

RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]