# Start with a standard Python 3.9 image
FROM python:3.9-slim

# Install system dependencies needed by Camelot
RUN apt-get update && apt-get install -y \
    ghostscript \
    tk \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your server code into the container
COPY server.py .

# Tell the container to run your Flask server when it starts
CMD ["python", "server.py"]