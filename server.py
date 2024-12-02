import os
from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, request, jsonify
import validators
import socks
import smtplib
import ssl
import socket

# Proxy Configuration - Get from environment variables
PROXY_HOST = os.getenv('PROXY_HOST', 'brd.superproxy.io')  # Default proxy host
PROXY_PORT = int(os.getenv('PROXY_PORT', 22228))  # Default proxy port
USERNAME = os.getenv('PROXY_USERNAME', 'brd-customer-hl_19ba380f-zone-residential_proxy1-country-us')  # Proxy username
PASSWORD = os.getenv('PROXY_PASSWORD', 'ge8id0hnocik')  # Proxy password

# SSL Certificate Path
SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', 'BrightDataSSLcertificate.crt')

# Configure SOCKS5 proxy
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
socket.socket = socks.socksocket  # Overwrite default socket with SOCKS5

# Create SSL context
ssl_context = ssl.create_default_context(cafile=SSL_CERT_PATH)

# Initialize Flask app
app = Flask(__name__)

# Function to test proxy connection
def test_proxy_connection():
    try:
        import requests
        proxies = {
            "http": f"socks5h://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}",
            "https": f"socks5h://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}",
        }
        url = "https://geo.brdtest.com/welcome.txt"
        response = requests.get(url, proxies=proxies, verify=SSL_CERT_PATH)
        if response.status_code == 200:
            print("Proxy connection successful. Response:", response.text)
            return True
        else:
            print(f"Proxy test failed. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Proxy connection failed: {e}")
        return False

# Verify email function
def verifyemail(email):
    mx = getrecords(email)
    print("MX Records:", mx)  # Debug: Log MX records

    if mx != 0 and len(mx) > 0:
        fake = findcatchall(email, mx)
        fake = 'Yes' if fake > 0 else 'No'

        try:
            # Set up the SMTP connection
            smtp = smtplib.SMTP(mx, 25)
            smtp.set_debuglevel(2)  # Enable verbose logging for debugging
            smtp.ehlo()

            results = checkemail(email, mx)
            status = 'Good' if results[0] == 250 else 'Bad'
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
            return jsonify({'error': 'SMTP connection error', 'details': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid MX records or no MX records found'}), 500

@app.route('/api/v1/verify/', methods=['GET'])
def search():
    addr = request.args.get('q')
    if not validators.email(addr):
        return jsonify({'Error': 'Invalid email address'}), 400

    # Test proxy connection before verification
    if not test_proxy_connection():
        return jsonify({'error': 'Proxy connection failed'}), 500

    return verifyemail(addr)

if __name__ == "__main__":
    print(f"Starting server with proxy: {PROXY_HOST}:{PROXY_PORT}")
    app.run(host='0.0.0.0', port=8080, debug=True)
