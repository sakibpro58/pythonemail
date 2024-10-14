#!/usr/bin/env python

from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, request, jsonify
import validators

app = Flask(__name__)

# Function to verify the email
def verifyemail(email):
    mx = getrecords(email)
    if mx != 0:
        fake = findcatchall(email, mx)
        fake = 'Yes' if fake > 0 else 'No'
        results = checkemail(email, mx)
        
        if results[0] == 666:
            return {'email': email, 'error': results[1], 'mx': mx, 'status': 'Error'}
        status = 'Good' if results[0] == 250 else 'Bad'

        data = {
            'email': email,
            'mx': mx,
            'code': results[0],
            'message': results[1],
            'status': status,
            'catch_all': fake
        }
        return data
    else:
        return {'error': 'Error checking email address'}

# API route to verify email
@app.route('/api/v1/verify/', methods=['GET'])
def search():
    addr = request.args.get('email')
    
    # Validate the email format
    if not validators.email(addr):
        return jsonify({'Error': 'Invalid email address'}), 400
    
    # Get verification result
    data = verifyemail(addr)
    return jsonify(data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
