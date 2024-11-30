import os
from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, request, jsonify
import validators
import socks
import smtplib
import ssl

# Proxy Configuration - Get from environment variables
PROXY_HOST = os.getenv('PROXY_HOST', 'brd.superproxy.io')  # Default to proxy if env var not set
PROXY_PORT = int(os.getenv('PROXY_PORT', 33335))  # Default port
USERNAME = os.getenv('PROXY_USERNAME', 'hl_ad020a32')  # Proxy username
PASSWORD = os.getenv('PROXY_PASSWORD', '0pe6ey6amntt')  # Proxy password

# SSL Certificate Path (Optional, if using SSL cert for Bright Data)
SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', 'BrightDataSSLcertificate.crt')

# Set up SOCKS5 proxy and SSL context for outgoing connections
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
ssl_context = ssl.create_default_context(cafile=SSL_CERT_PATH)

# Initialize Flask app
app = Flask(__name__)

def verifyemail(email):
    mx = getrecords(email)
    
    # Log the MX records for debugging
    print("MX Records:", mx)

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
            return jsonify({'error': 'SMTP connection error', 'details': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid MX records or no MX records found'}), 500

@app.route('/api/v1/verify/', methods=['GET'])
def search():
    addr = request.args.get('q')
    if not validators.email(addr):
        return jsonify({'Error': 'Invalid email address'}), 400
    data = verifyemail(addr)
    return data

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
