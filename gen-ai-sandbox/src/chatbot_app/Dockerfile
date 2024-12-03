FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in api_requirements.txt
COPY api_requirements.txt .
RUN pip install --no-cache-dir -r api_requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV CONFIG DEV

# Run app.py when the container launches
CMD ["uvicorn", "chatbot.api:app", "--host", "0.0.0.0", "--port", "8080"]
