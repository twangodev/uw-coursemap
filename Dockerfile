# Use the official Python image
FROM python:3.9-slim

# Install system dependencies for Pipenv and Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Pipenv
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install dependencies via Pipenv
RUN pipenv install --system --deploy

# Copy the application code
COPY . .

# Expose the application port
EXPOSE 5000

# Define the default command using Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "server:app"]
