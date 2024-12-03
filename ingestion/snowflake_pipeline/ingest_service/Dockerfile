FROM python:3.10-slim 

WORKDIR /app 

COPY main.py log.py constants.py models.py data_cleaning.py snowflake_client.py /app/

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]