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

# Proxy Configuration (Updated to Smartproxy)
PROXY_HOST = "gate.smartproxy.com"  # New proxy host (Smartproxy)
PROXY_PORT = 7000  # Updated to the new Smartproxy port
USERNAME = "sp3wtagw87"  # Replace with your Smartproxy username
PASSWORD = "liUFvsaye3l4+4QlU7"  # Replace with your Smartproxy password

# Set up SOCKS5 proxy for outgoing connections
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)

# Initialize Flask app
app = Flask(__name__)

# Logging setup to ensure proxy usage
logging.basicConfig(level=logging.DEBUG)
logging.debug(f"Using proxy: {PROXY_HOST}:{PROXY_PORT}")

def check_ip():
    """Function to check and log the current IP address through the proxy."""
    try:
        # Setting up the proxy for the requests made through urllib
        proxy_support = urllib.request.ProxyHandler({
            'http': f'socks5h://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}',
            'https': f'socks5h://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}'
        })
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)
        
        # Fetch the current IP address via proxy
        with urllib.request.urlopen('https://ip.smartproxy.com/json') as response:
            ip_data = json.load(response)
            logging.info("Current IP through proxy: %s", ip_data['ip'])
    except Exception as e:
        logging.error("Error fetching IP through proxy: %s", e)

check_ip()

def verifyemail(email):
    mx = getrecords(email)
    
    # Log the MX records for debugging
    logging.debug("MX Records: %s", mx)

    # Check if MX records are valid
    if mx != 0 and len(mx) > 0:
        fake = findcatchall(email, mx)
        fake = 'Yes' if fake > 0 else 'No'
        
        try:
            # Set up the SMTP connection
            smtp = smtplib.SMTP(mx, 25)  # Use MX server and port 25 for SMTP
            smtp.set_debuglevel(1)  # Enable verbose logging for SMTP debugging
            
            # Perform EHLO command to initiate session
            smtp.ehlo()
            
            # Run the email verification
            results = checkemail(email, mx)
            status = 'Good' if results[0] == 250 else 'Bad'
            
            # Close the SMTP connection
            smtp.quit()
            
            data = {
                'email': email,
                'mx': mx,
                'code': results[0],
                'message': results[1],
                'status': status,
                'catch_all': fake
            }
            return jsonify(data), 200
        except Exception as e:
            logging.error("SMTP connection error: %s", e)
            return jsonify({'error': 'SMTP connection error', 'details': str(e)}), 500
    else:
        logging.error("Invalid MX records or no MX records found for %s", email)
        return jsonify({'error': 'Invalid MX records or no MX records found'}), 500

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
