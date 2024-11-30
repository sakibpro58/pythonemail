#!/usr/bin/env python

from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, request, jsonify
import validators
import socks
import smtplib
import ssl
import dns.resolver

# Proxy Configuration
PROXY_HOST = "brd.superproxy.io"
PROXY_PORT = 33335  # Updated to Bright Data's required port
USERNAME = "hl_19ba380f"  # Replace with your actual username
PASSWORD = "ge8id0hnocik"  # Replace with your actual password

# SSL Certificate Path
SSL_CERT_PATH = "BrightDataSSLcertificate.crt"

# Set up SOCKS5 proxy and SSL context for outgoing connections
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
ssl_context = ssl.create_default_context(cafile=SSL_CERT_PATH)

# Initialize Flask app
app = Flask(__name__)

def verifyemail(email):
    try:
        mx = getrecords(email)
        
        # Log the MX records for debugging
        print("MX Records:", mx)

        if not mx or len(mx) == 0:
            return {'error': 'No MX records found for the domain'}, 500

        fake = findcatchall(email, mx)
        fake = 'Yes' if fake > 0 else 'No'

        try:
            # Set up the SMTP connection
            smtp = smtplib.SMTP(mx[0], 25)  # Use MX server and port 25 for SMTP
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
            return data, 200
        except smtplib.SMTPConnectError as e:
            return {'error': 'SMTP connection error', 'details': str(e)}, 500
        except Exception as e:
            return {'error': 'SMTP error', 'details': str(e)}, 500
    except dns.resolver.NoAnswer as e:
        return {'error': 'DNS resolution error: No MX records found', 'details': str(e)}, 500
    except dns.resolver.NXDOMAIN as e:
        return {'error': 'DNS resolution error: Domain does not exist', 'details': str(e)}, 500
    except Exception as e:
        return {'error': 'Unexpected error during verification', 'details': str(e)}, 500


@app.route('/api/v1/verify/', methods=['GET'])
def search():
    addr = request.args.get('q')
    if not validators.email(addr):
        return jsonify({'Error': 'Invalid email address'}), 400

    response, status_code = verifyemail(addr)

    # Check if the error message is related to DNS resolution
    if status_code == 500 and 'Failed to resolve MX record via Google DNS' in response.get('error', ''):
        return jsonify({'error': 'Failed to resolve MX record. Please check the domain or MX records.'}), 500

    return jsonify(response), status_code

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
