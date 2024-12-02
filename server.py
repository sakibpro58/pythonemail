#!/usr/bin/env python

from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, jsonify, request
import validators
import socks
import smtplib
import urllib.request
import json
import logging
import socket

# Proxy Configuration (Smartproxy)
PROXY_HOST = "gate.smartproxy.com"
PROXY_PORT = 7000
USERNAME = "user-sp3wtagw87-session-1"
PASSWORD = "liUFvsaye3l4+4QlU7"

# Set up SOCKS5 proxy for outgoing connections
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
socks.wrapmodule(smtplib)

# Initialize Flask app
app = Flask(__name__)

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logging.debug(f"Using proxy: {PROXY_HOST}:{PROXY_PORT}")

def check_ip():
    """Check and log the current IP address through the proxy."""
    try:
        proxy_support = urllib.request.ProxyHandler({
            'http': f'socks5h://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}',
            'https': f'socks5h://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}'
        })
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)

        with urllib.request.urlopen('https://ip.smartproxy.com/json') as response:
            ip_data = json.load(response)
            logging.info("Current IP through proxy: %s", ip_data['ip'])
    except Exception as e:
        logging.error("Error fetching IP through proxy: %s", e)

check_ip()

def get_ipv4_mx_records(mx_records):
    """Filter MX records to return only IPv4 addresses."""
    ipv4_records = []
    for record in mx_records:
        try:
            ipv4_address = socket.gethostbyname(record)
            ipv4_records.append(ipv4_address)
        except socket.gaierror as e:
            logging.warning(f"Skipping IPv6 or invalid record: {record}, Error: {e}")
    return ipv4_records

def verifyemail(email):
    mx = getrecords(email)
    logging.debug("Original MX Records: %s", mx)

    ipv4_mx = get_ipv4_mx_records(mx)
    logging.debug("Filtered IPv4 MX Records: %s", ipv4_mx)

    if not ipv4_mx:
        logging.error("No valid IPv4 MX records found for %s", email)
        return jsonify({'error': 'No valid IPv4 MX records found'}), 500

    fake = findcatchall(email, ipv4_mx)
    fake = 'Yes' if fake > 0 else 'No'

    try:
        smtp = smtplib.SMTP(ipv4_mx[0], 25)
        smtp.set_debuglevel(1)
        smtp.ehlo()

        results = checkemail(email, ipv4_mx)
        status = 'Good' if results[0] == 250 else 'Bad'

        smtp.quit()

        data = {
            'email': email,
            'mx': ipv4_mx,
            'code': results[0],
            'message': results[1],
            'status': status,
            'catch_all': fake
        }
        return jsonify(data), 200
    except Exception as e:
        logging.error("SMTP connection error: %s", e)
        return jsonify({'error': 'SMTP connection error', 'details': str(e)}), 500

@app.route('/api/v1/verify/', methods=['GET'])
def search():
    addr = request.args.get('q')
    if not validators.email(addr):
        logging.warning("Invalid email address provided: %s", addr)
        return jsonify({'Error': 'Invalid email address'}), 400
    data = verifyemail(addr)
    return data

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
