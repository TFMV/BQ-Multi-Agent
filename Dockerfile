# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Copy the service account key file into the Docker image
COPY sa.json /app/service-account-key.json

# Debug step: List files in the working directory and potential subdirectories
RUN find /app -name '*.db' -exec ls -la {} \;

# Delete any SQLite database files found in the /app directory or subdirectories
RUN find /app -name '*.db' -exec rm -f {} \;

# Expose the port the app runs on
EXPOSE 8080

# Run the application with increased timeout and more workers
CMD find /app -name '*.db' -exec rm -f {} \; && gunicorn -b 0.0.0.0:8080 --timeout 240 --workers 4 app:app
