import socks
import socket
import smtplib
import ssl
from flask import Flask, request, jsonify

# Proxy Configuration - Directly set in the script
PROXY_HOST = 'brd.superproxy.io'  # Proxy host
PROXY_PORT = 22228  # Proxy port
USERNAME = 'brd-customer-hl_19ba380f-zone-residential_proxy1-country-us'  # Proxy username
PASSWORD = 'ge8id0hnocik'  # Proxy password

# Configure SOCKS5 proxy
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
socket.socket = socks.socksocket  # Overwrite default socket with SOCKS5

# Create SSL context
ssl_context = ssl.create_default_context()

# Initialize Flask app
app = Flask(__name__)

def verifyemail(email):
    # Assuming mx records are retrieved already
    mx = ["smtp.example.com"]  # Replace with actual MX records

    print("MX Records:", mx)  # Debug: Log MX records

    if mx != 0 and len(mx) > 0:
        for port in [587, 465, 25]:
            try:
                # Set up the SMTP connection using proxy
                smtp = smtplib.SMTP(mx[0], port, timeout=10)
                smtp.set_debuglevel(2)  # Enable verbose logging for debugging
                smtp.ehlo()
                print(f"Trying port {port} on {mx[0]}")
                
                # Attempt the SMTP conversation
                smtp.quit()

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
    if not addr.endswith('@example.com'):  # Simple email validation check
        return jsonify({'Error': 'Invalid email address'}), 400

    # Test proxy connection before verification
    # Note: You can add your own test proxy connection method here
    return verifyemail(addr)

if __name__ == "__main__":
    print(f"Starting server with proxy: {PROXY_HOST}:{PROXY_PORT}")
    app.run(host='0.0.0.0', port=8080, debug=True)
