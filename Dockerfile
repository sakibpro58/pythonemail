# Use Alpine Linux as the base image
FROM alpine:latest

# Install Python3, pip3, and necessary dependencies
RUN apk add --no-cache python3 py3-pip py3-dnspython py3-pysocks py3-validators py3-flask py3-flask-restx \
    && pip3 install --upgrade pip

# Copy the app files to the /app directory
COPY . /app

# Set /app as the working directory
WORKDIR /app

# Install any additional Python dependencies from requirements.txt, if needed
RUN pip3 install -r requirements.txt

# Expose the port Flask will be running on (optional, adjust based on your app's config)
EXPOSE 5000

# Start the Flask server
ENTRYPOINT ["python3"]
CMD ["server.py"]
