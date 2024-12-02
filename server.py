import os
from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, request, jsonify
import validators
import socks
import smtplib
import ssl
import socket

# Proxy Configuration - Directly set in the script without username
PROXY_HOST = 'gate.smartproxy.com'  # Proxy host
PROXY_PORT = 7000  # Proxy port
PASSWORD = 'liUFvsaye3l4+4QlU7'  # Proxy password (no username required)

# Configure SOCKS5 proxy
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, PASSWORD, None)
socket.socket = socks.socksocket  # Overwrite default socket with SOCKS5

# Create SSL context
ssl_context = ssl.create_default_context()

# Initialize Flask app
app = Flask(__name__)

# Function to test proxy connection with enhanced error logging
def test_proxy_connection():
    try:
        # Test connection to a known server (httpbin.org) via proxy
        test_host = "httpbin.org"
        test_port = 80
        
        # Create a socket connection using the proxy
        with socket.create_connection((test_host, test_port)) as s:
            s.sendall(b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\n\r\n")
            response = s.recv(1024).decode()
            print("Proxy connection successful. Response:", response)
            return True
    except socket.timeout:
        print(f"Proxy connection failed: Timeout while connecting to {test_host}:{test_port}")
    except socket.gaierror:
        print(f"Proxy connection failed: DNS resolution error for {test_host}")
    except Exception as e:
        print(f"Proxy connection failed: {e}")
    
    return False

# Verify email function
def verifyemail(email):
    mx = getrecords(email)
    print("MX Records:", mx)  # Debug: Log MX records

    if mx != 0 and len(mx) > 0:
        for port in [587, 465, 25]:  # Attempt connection on common SMTP ports
            try:
                # Set up the SMTP connection using proxy
                smtp = smtplib.SMTP(mx[0], port, timeout=10)
                smtp.set_debuglevel(2)  # Enable verbose logging for debugging
                smtp.ehlo()
                print(f"Trying port {port} on {mx[0]}")
                
                # Attempt the SMTP conversation
                smtp.quit()

                # Return success if connection is made
                data = {'email': email, 'status': 'Good'}
                return jsonify(data), 200
            except Exception as e:
                print(f"SMTP connection failed on port {port}: {e}")
                continue  # Try next port

        return jsonify({'error': 'SMTP connection failed on all ports'}), 500
    else:
        return jsonify({'error': 'Invalid MX records or no MX records found'}), 500

@app.route('/api/v1/verify/', methods=['GET'])
def search():
    addr = request.args.get('q')
    if not addr:
        return jsonify({'Error': 'No email address provided'}), 400

    # Use validators module to validate email
    if not validators.email(addr):
        return jsonify({'Error': 'Invalid email address'}), 400

    # Test proxy connection before verification
    if not test_proxy_connection():
        return jsonify({'error': 'Proxy connection failed'}), 500

    return verifyemail(addr)

if __name__ == "__main__":
    print(f"Starting server with proxy: {PROXY_HOST}:{PROXY_PORT}")
    app.run(host='0.0.0.0', port=8080, debug=True)
