#!/usr/bin/env python

from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, request, jsonify
import validators
import socks
import smtplib
import ssl

# Proxy Configuration
PROXY_HOST = "brd.superproxy.io"
PROXY_PORT = 33335  # Updated to Bright Data's required port
USERNAME = "hl_ad020a32"  # Replace with your actual username
PASSWORD = "0pe6ey6amntt"  # Replace with your actual password

# SSL Certificate Path
SSL_CERT_PATH = "BrightData SSL certificate (port 33335).crt"

# Configure SOCKS5 proxy and SSL context for outgoing connections
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
ssl_context = ssl.create_default_context(cafile=SSL_CERT_PATH)

# Initialize Flask app
app = Flask(__name__)

def verifyemail(email):
    mx = getrecords(email)
    if mx != 0:
        fake = findcatchall(email, mx)
        fake = 'Yes' if fake > 0 else 'No'
        
        try:
            # Set up the SMTP connection
            smtp = smtplib.SMTP(mx[0][1], 25)  # Example port, adjust if needed
            smtp.set_debuglevel(1)  # Enable verbose logging for debugging
            
            # Send a test EHLO command
            smtp.ehlo()
            
            # Perform email verification here
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
            return jsonify({'error': 'SMTP connection error', 'details': str(e)}), 500
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
