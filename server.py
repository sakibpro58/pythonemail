#!/usr/bin/env python

from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, request, jsonify
import validators
import socks
import smtplib
import ssl
import dns.resolver  # For external DNS resolution
import socket

# Proxy Configuration
PROXY_HOST = "brd.superproxy.io"
PROXY_PORT = 33335
USERNAME = "brd-customer-hl_19ba380f-zone-residential_proxy1"
PASSWORD = "ge8id0hnocik"

# SSL Certificate Path
SSL_CERT_PATH = "BrightDataSSLcertificate.crt"

# Set up SOCKS5 proxy for outgoing connections
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
socket.socket = socks.socksocket  # Override default socket with SOCKS5 proxy

# Initialize Flask app
app = Flask(__name__)

def resolve_dns_via_proxy(mx_record):
    """Resolve the MX record through SOCKS proxy using an external DNS server."""
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['8.8.8.8', '8.8.4.4']  # Google DNS
    socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
    socket.socket = socks.socksocket  # Set the default socket to route via the proxy

    try:
        answers = resolver.resolve(mx_record, 'MX')
        for rdata in answers:
            print(f"Resolved {mx_record} to {rdata.exchange}")
            return str(rdata.exchange)
    except Exception as e:
        print(f"DNS resolution failed for {mx_record} through proxy: {e}")
        return None

def verifyemail(email):
    mx_records = getrecords(email)
    
    # Log MX records for debugging
    print("Fetched MX Records:", mx_records)

    if not mx_records:
        return jsonify({'error': 'No MX records found'}), 500

    # Resolve the first MX record
    mx_ip = resolve_dns_via_proxy(mx_records[0])
    if not mx_ip:
        return jsonify({'error': 'DNS resolution failed for MX record'}), 500

    # Check for catch-all domain
    fake = findcatchall(email, mx_records)
    fake = 'Yes' if fake > 0 else 'No'

    try:
        # Attempt SMTP connection
        smtp = smtplib.SMTP(mx_ip, 25)
        smtp.set_debuglevel(1)  # Enable SMTP debugging
        smtp.ehlo()
    except Exception as e:
        print(f"SMTP connection failed on port 25: {e}")
        try:
            # Retry using STARTTLS on port 587
            smtp = smtplib.SMTP(mx_ip, 587)
            smtp.set_debuglevel(1)
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context(cafile=SSL_CERT_PATH))
        except Exception as e:
            return jsonify({'error': 'SMTP connection error', 'details': str(e)}), 500

    try:
        # Run email verification
        results = checkemail(email, mx_records)
        status = 'Good' if results[0] == 250 else 'Bad'

        # Close the SMTP connection
        smtp.quit()

        data = {
            'email': email,
            'mx': mx_records,
            'resolved_ip': mx_ip,
            'code': results[0],
            'message': results[1],
            'status': status,
            'catch_all': fake
        }
        return jsonify(data), 200
    except Exception as e:
        smtp.quit()
        return jsonify({'error': 'Verification failed', 'details': str(e)}), 500

@app.route('/api/v1/verify/', methods=['GET'])
def search():
    addr = request.args.get('q')
    if not validators.email(addr):
        return jsonify({'Error': 'Invalid email address'}), 400
    return verifyemail(addr)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
