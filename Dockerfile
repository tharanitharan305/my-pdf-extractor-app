# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for tabula-py
# Use a multi-line command for clarity and to ensure all steps run in one layer
RUN apt-get update \
    && apt-get install -y openjdk-11-jre \
    # Clean up apt cache to keep the image size small
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY server.py .

# Expose the port the app runs on
EXPOSE 5000

# Run the app
CMD ["python", "server.py"]
