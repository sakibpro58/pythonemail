import os
from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, request, jsonify
import validators
import socks
import smtplib
import ssl
import socket

# Proxy Configuration - Set directly here (since we're not using .env)
PROXY_HOST = 'brd.superproxy.io'  # Default proxy host
PROXY_PORT = 22228  # Default proxy port
USERNAME = 'brd-customer-hl_19ba380f-zone-residential_proxy1-country-us'  # Proxy username
PASSWORD = 'ge8id0hnocik'  # Proxy password

# SSL Certificate Path (Optional, if using SSL cert for Bright Data)
SSL_CERT_PATH = 'BrightDataSSLcertificate.crt'

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
        test_host = "httpbin.org"
        test_port = 80
        with socket.create_connection((test_host, test_port)) as s:
            s.sendall(b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\n\r\n")
            response = s.recv(1024).decode()
            print("Proxy connection successful. Response:", response)
            return True
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
            # Force using IPv4 for SMTP connection
            smtp_host = mx[0]  # Assume mx[0] is the primary MX record
            smtp_port = 25

            # Create an IPv4 socket
            smtp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            smtp_socket.connect((smtp_host, smtp_port))

            # Use the SMTP connection
            smtp = smtplib.SMTP()
            smtp.sock = smtp_socket  # Manually set the socket to the created IPv4 socket
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
