# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for tabula-py
RUN apt-get update && apt-get install -y \
    openjdk-11-jre \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY python_server.py .

# Expose the port the app runs on
EXPOSE 5000

# Run the app
CMD ["python", "server.py"]
