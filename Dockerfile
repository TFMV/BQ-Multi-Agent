# Stage 1: Build environment
FROM python:3.10-slim as build

# Set the working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the image
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime environment
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy installed packages from the build stage
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Copy the rest of the application code into the image
COPY . .

# Command to run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
