FROM python:3.10-slim

# Install LibreOffice
RUN apt-get update --fix-missing && \
    apt-get install -y libreoffice && \
    echo "LibreOffice installed" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY main.py models.py constants.py /app/

RUN mkdir /app/data

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]