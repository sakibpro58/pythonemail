import socks
import smtplib
import socket
import dns.resolver
import urllib.request
import re
from flask import Flask, jsonify, request

# Bright Data Proxy credentials
PROXY_HOST = "brd.superproxy.io"
PROXY_PORT = 33335
USERNAME = "brd-customer-hl_19ba380f-zone-residential_proxy1"  # Replace with your username
PASSWORD = "ge8id0hnocik"  # Replace with your password

# Initialize Flask app
app = Flask(__name__)

# Set up SOCKS5 proxy for DNS and HTTP requests
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
socket.socket = socks.socksocket

# Proxy handler for urllib requests (HTTP/HTTPS)
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler(
        {'http': f'http://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}',
         'https': f'http://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}'}))

# Test if proxy is working by opening a URL
try:
    response = opener.open('https://geo.brdtest.com/mygeo.json')
    print(f"Proxy working: {response.read()}")
except Exception as e:
    print(f"Error connecting via proxy: {str(e)}")


# Function to validate email syntax
def is_valid_email_syntax(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    match = re.match(regex, email)
    if match:
        print(f"Valid email syntax: {email}")
        return True
    else:
        print(f"Invalid email syntax: {email}")
        return False


# Function to check MX records via DNS resolution
def check_mx_records(domain):
    try:
        dns.resolver.resolve(domain, 'MX')
        print(f"MX records found for {domain}")
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN) as e:
        print(f"DNS resolution failed for {domain}: {str(e)}")
        return False


# Function to check SMTP connection
def check_smtp_connection(email):
    domain = email.split('@')[1]
    try:
        # Resolve MX record
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(mx_records[0].exchange)
        print(f"MX Record found: {mx_record}")

        # Connect to the SMTP server
        server = smtplib.SMTP(mx_record, 25, timeout=10)
        server.set_debuglevel(1)  # Enable detailed debug output
        server.helo()
        server.mail('test@example.com')
        code, message = server.rcpt(email)
        server.quit()

        if code == 250:
            return True
        else:
            print(f"SMTP error code: {code}, message: {message}")
            return False
    except Exception as e:
        print(f"SMTP connection error: {str(e)}")
        return False


# Function to handle email verification
def verify_email(email):
    print(f"Verifying email: {email}")
    
    if not is_valid_email_syntax(email):
        return {"status": "error", "message": "Invalid email syntax"}

    domain = email.split('@')[1]
    print(f"Checking MX records for domain: {domain}")
    
    if not check_mx_records(domain):
        return {"status": "error", "message": "DNS resolution failed for MX record"}

    print(f"Checking SMTP connection for email: {email}")
    
    if not check_smtp_connection(email):
        return {"status": "error", "message": "SMTP connection error"}

    return {"status": "success", "message": "Email is valid"}


# API route for email verification
@app.route('/api/v1/verify/', methods=['GET'])
def api_verify_email():
    email = request.args.get('email')
    if not email:
        return jsonify({"status": "error", "message": "No email provided"}), 400
    
    verification_result = verify_email(email)
    return jsonify(verification_result)


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
