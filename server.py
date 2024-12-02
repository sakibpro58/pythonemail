#!/usr/bin/env python

from flask import Flask, jsonify, request
import validators
import dns.resolver
import smtplib
import logging

# Proxy Configuration (if required)
import socks
PROXY_HOST = "gate.smartproxy.com"
PROXY_PORT = 7000
USERNAME = "user-sp3wtagw87-session-1"
PASSWORD = "liUFvsaye3l4+4QlU7"
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)

# Initialize Flask app
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

def resolve_mx_records(domain):
    """
    Resolve MX records for a domain using dnspython.
    """
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        mx_records = [str(r.exchange).rstrip('.') for r in answers]
        return mx_records
    except dns.resolver.NoAnswer:
        logging.error(f"No MX records found for domain: {domain}")
        return []
    except dns.resolver.NXDOMAIN:
        logging.error(f"Domain does not exist: {domain}")
        return []
    except dns.resolver.Timeout:
        logging.error(f"Timeout occurred while resolving MX records for: {domain}")
        return []
    except Exception as e:
        logging.error(f"Error resolving MX records for {domain}: {e}")
        return []

def verifyemail(email):
    """
    Verify email address by resolving MX records and attempting SMTP handshake.
    """
    domain = email.split('@')[-1]
    mx_records = resolve_mx_records(domain)
    
    if not mx_records:
        return jsonify({'email': email, 'status': 'Invalid', 'message': 'No MX records found'}), 400

    try:
        # Attempt SMTP handshake with the first MX record
        smtp = smtplib.SMTP(mx_records[0], 25)
        smtp.set_debuglevel(1)
        smtp.ehlo()
        smtp.quit()
        
        # Successful handshake implies the email's domain is functional
        return jsonify({'email': email, 'status': 'Valid', 'message': 'SMTP handshake successful'}), 200
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error for {email}: {e}")
        return jsonify({'email': email, 'status': 'Invalid', 'message': str(e)}), 400
    except Exception as e:
        logging.error(f"Unexpected error for {email}: {e}")
        return jsonify({'email': email, 'status': 'Error', 'message': str(e)}), 500

@app.route('/api/v1/verify/', methods=['GET'])
def search():
    addr = request.args.get('q')
    if not validators.email(addr):
        logging.warning(f"Invalid email address provided: {addr}")
        return jsonify({'error': 'Invalid email address'}), 400
    return verifyemail(addr)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
