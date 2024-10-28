#!/usr/bin/env python

from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, request, jsonify
import validators
import socks
import smtplib
import socket

# Proxy Configuration
PROXY_HOST = "gw.dataimpulse.com"
PROXY_PORT = 824
USERNAME = "86ec273c5006e3b6367b"  # Replace with your actual username
PASSWORD = "dc834684ea99c6a5"  # Replace with your actual password

# Set up SOCKS5 proxy for outgoing connections
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
socket.socket = socks.socksocket  # Override default socket with SOCKS5

# Flask app setup
app = Flask(__name__)

def verifyemail(email):
    mx = getrecords(email)
    if mx != 0:
        fake = findcatchall(email, mx)
        fake = 'Yes' if fake > 0 else 'No'
        
        # Verbose SMTP check with proxy
        try:
            smtp = smtplib.SMTP(mx[0])  # Use the first MX record
            smtp.set_debuglevel(1)  # Enable verbose output for SMTP interactions
            smtp.quit()
        except Exception as e:
            print(f"SMTP connection error: {e}")
            return jsonify({'error': 'SMTP connection error'}), 500

        results = checkemail(email, mx)
        status = 'Good' if results[0] == 250 else 'Bad'

        data = {
            'email': email,
            'mx': mx,
            'code': results[0],
            'message': results[1],
            'status': status,
            'catch_all': fake
        }
        return jsonify(data), 200
    else:
        return jsonify({'error': 'Error checking email address'}), 500

@app.route('/api/v1/verify/', methods=['GET'])
def search():
    addr = request.args.get('q')
    if not validators.email(addr):
        return jsonify({'Error': 'Invalid email address'}), 400
    data = verifyemail(addr)
    return data

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
