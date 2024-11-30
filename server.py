import socks
import smtplib
import ssl
import socket
import dns.resolver
import re
import urllib.request

# Bright Data Proxy credentials
PROXY_HOST = "brd.superproxy.io"
PROXY_PORT = 33335
USERNAME = "brd-customer-hl_19ba380f-zone-residential_proxy1"  # Replace with your username
PASSWORD = "ge8id0hnocik"  # Replace with your password

# Set up SOCKS5 proxy for DNS and HTTP requests
socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, USERNAME, PASSWORD)
socket.socket = socks.socksocket

# Proxy handler for urllib requests (HTTP/HTTPS)
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler(
        {'http': f'http://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}',
         'https': f'http://{USERNAME}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}'}))

# Test if proxy is working by opening a URL
try:
    response = opener.open('https://geo.brdtest.com/mygeo.json')
    print(f"Proxy working: {response.read()}")
except Exception as e:
    print(f"Error connecting via proxy: {str(e)}")

# Function to validate email syntax using regular expression
def is_valid_email_syntax(email):
    # Regular expression for basic email validation
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(regex, email):
        return True
    return False

# Function to check MX records via DNS resolution
def check_mx_records(domain):
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False

# Function to check SMTP connection
def check_smtp_connection(email):
    domain = email.split('@')[1]
    try:
        # Resolve MX record
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(mx_records[0].exchange)

        # Connect to the SMTP server
        server = smtplib.SMTP(mx_record, 25, timeout=10)
        server.set_debuglevel(0)
        server.helo()
        server.mail('test@example.com')
        code, message = server.rcpt(email)
        server.quit()

        if code == 250:
            return True
        else:
            return False
    except Exception as e:
        print(f"SMTP connection error: {str(e)}")
        return False

# Function to handle email verification
def verify_email(email):
    if not is_valid_email_syntax(email):
        return {"status": "error", "message": "Invalid email syntax"}
    
    domain = email.split('@')[1]
    if not check_mx_records(domain):
        return {"status": "error", "message": "DNS resolution failed for MX record"}
    
    if not check_smtp_connection(email):
        return {"status": "error", "message": "SMTP connection error"}
    
    return {"status": "success", "message": "Email is valid"}

# Example usage
email_to_verify = 'test@pavoi.com'
verification_result = verify_email(email_to_verify)

print(f"Verification result for {email_to_verify}: {verification_result}")
