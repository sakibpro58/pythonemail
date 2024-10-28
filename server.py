#!/usr/bin/env python

from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, request, jsonify
import validators
import socks
import socket
import smtplib
import dns.resolver  # Ensure dnspython is installed (pip install dnspython)

# Proxy Configuration
PROXY_HOST = "gw.dataimpulse.com"
PROXY_PORT = 824
USERNAME = "86ec273c5006e3b6367b"  # Replace with your actual username
PASSWORD = "dc834684ea99c6a5"  # Replace with your actual password

# Set up SOCKS5 proxy for outgoing connections
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
socket.socket = socks.socksocket  # Override default socket with SOCKS5 for proxying connections

# Flask app setup
app = Flask(__name__)

# Function to retrieve MX records using an external DNS resolver
def get_mx_records(domain):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['8.8.8.8']  # Google DNS as an example
    try:
        mx_records = resolver.resolve(domain, 'MX')
        return [str(mx.exchange) for mx in mx_records]
    except Exception as e:
        print(f"DNS resolution error: {e}")
        return None

# Main email verification function
def verifyemail(email):
    domain = email.split('@')[-1]
    mx_records = get_mx_records(domain)
    if not mx_records:
        return jsonify({'error': 'No valid MX records found or DNS resolution failed'}), 500

    # Attempt SMTP SSL connection with the first MX record
    try:
        smtp = smtplib.SMTP_SSL(mx_records[0], 465)  # Port 465 for SMTP SSL
        smtp.set_debuglevel(1)  # Enable verbose output for SMTP interactions
        smtp.quit()
    except Exception as e:
        print(f"SMTP connection error: {e}")
        return jsonify({'error': 'SMTP connection error', 'details': str(e)}), 500

    # Perform further email checks using existing code
    fake = findcatchall(email, mx_records)
    fake = 'Yes' if fake > 0 else 'No'
    results = checkemail(email, mx_records)
    status = 'Good' if results[0] == 250 else 'Bad'

    data = {
        'email': email,
        'mx': mx_records,
        'code': results[0],
        'message': results[1],
        'status': status,
        'catch_all': fake
    }
    return jsonify(data), 200

@app.route('/api/v1/verify/', methods=['GET'])
def search():
    addr = request.args.get('q')
    if not validators.email(addr):
        return jsonify({'Error': 'Invalid email address'}), 400
    data = verifyemail(addr)
    return data

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
