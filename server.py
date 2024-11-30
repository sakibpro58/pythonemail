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
USERNAME = "brd-customer-hl_19ba380f-zone-residential_proxy1"  # Replace with your actual username
PASSWORD = "ge8id0hnocik"  # Replace with your actual password

# SSL Certificate Path
SSL_CERT_PATH = "BrightDataSSLcertificate.crt"

# Set up SOCKS5 proxy and SSL context for outgoing connections
# socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
# ssl_context = ssl.create_default_context(cafile=SSL_CERT_PATH)

# Initialize Flask app
app = Flask(__name__)

def resolve_mx_via_google(mx_record):
    """Force using Google DNS for MX resolution."""
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['8.8.8.8', '8.8.4.4']  # Google DNS

    try:
        print(f"Attempting to resolve MX record for: {mx_record}")
        answers = resolver.resolve(mx_record, 'MX')
        for rdata in answers:
            print(f"Resolved {mx_record} to {rdata.exchange}")
            return str(rdata.exchange)
    except Exception as e:
        print(f"Failed to resolve {mx_record} with Google DNS: {e}")
        return None

def verifyemail(email):
    mx = getrecords(email)
    
    # Log the MX records for debugging
    print("MX Records:", mx)

    # Check if MX records are valid
    if mx != 0 and len(mx) > 0:
        fake = findcatchall(email, mx)
        fake = 'Yes' if fake > 0 else 'No'

        # Try resolving MX records via Google DNS if the regular method fails
        mx_resolved = resolve_mx_via_google(mx[0]) if mx else None
        if mx_resolved:
            try:
                # Set up the SMTP connection
                smtp = smtplib.SMTP(mx_resolved, 25)  # Use MX server and port 25 for SMTP
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
                    'mx': mx_resolved,
                    'code': results[0],
                    'message': results[1],
                    'status': status,
                    'catch_all': fake
                }
                return jsonify(data), 200
            except Exception as e:
                return jsonify({'error': 'SMTP connection error', 'details': str(e)}), 500
        else:
            return jsonify({'error': 'Failed to resolve MX record via Google DNS'}), 500
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
