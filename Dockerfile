# Use Ubuntu base image
FROM ubuntu:latest

# Update the package list and install Python 3 and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip build-essential

# Set Python3 as the default python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 10

# Copy the entire app to the /app directory
COPY . /app

# Set the working directory
WORKDIR /app

# Install Python dependencies using Python3's pip
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Expose the app port (optional, change this if using a different port)
EXPOSE 3000

# Default entrypoint for running the server
ENTRYPOINT ["python3", "server.py"]
