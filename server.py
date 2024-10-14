#!/usr/bin/env python

from libs.mx import getrecords
from libs.email import checkemail, findcatchall
from flask import Flask, request, jsonify
import validators

def verifyemail(email):
    mx = getrecords(email)
    if mx != 0:
        fake = findcatchall(email, mx)
        if fake > 0:
            fake = 'Yes'
        else:
            fake = 'No'
        
        results = checkemail(email, mx)
        if results[0] == 666:
            return jsonify({'email': email, 'error': results[1], 'mx': mx, 'status': 'Error'}), 500
        if results[0] == 250:
            status = 'Good'
        else:
            status = 'Bad'

        data = {
            'email': email,
            'mx': mx,
            'code': results[0],
            'message': results[1],
            'status': status,
            'catch_all': fake
        }
        return jsonify(data), 200
    else:
        return jsonify({'error': 'Error checking email address'}), 500

app = Flask(__name__)

@app.route('/api/v1/verify/', methods=['GET'])
def search():
    addr = request.args.get('q')
    if not validators.email(addr):
        return jsonify({'Error': 'Invalid email address'}), 400
    data = verifyemail(addr)
    return data

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
