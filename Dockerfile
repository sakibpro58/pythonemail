# Use Ubuntu base image
FROM ubuntu:latest

# Update the package list and install Python and Node.js
RUN apt-get update && \
    apt-get install -y build-essential python-dev python-pip curl

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Copy the entire app to the /app directory
COPY . /app

# Set the working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Node.js dependencies
RUN npm install

# Expose the app port (optional, change this if using a different port)
EXPOSE 3000

# Default entrypoint for running the Node.js server
ENTRYPOINT ["npm", "start"]

# If you need the Python app as well, you can have a different entry point for Python, though this can cause issues
# You may want to separate concerns, but here's how you'd do it for Node.js:
CMD ["npm", "start"]
