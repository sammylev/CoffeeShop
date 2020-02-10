import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
import logging
from logging import FileHandler, Formatter

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

# Set up logging
error_log = FileHandler('error.log')
error_log.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
error_log.setLevel(logging.INFO)
app.logger.setLevel(logging.INFO)
app.logger.addHandler(error_log)

# ROUTES


'''
Endpoint: /drinks
Auth: None
Arguments: None
Returns: List of drinks in short format
Expected Success Code: 200
drinks = [drink.short() for drink in all_drinks]
'''


@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.order_by(Drink.id).all()

    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drinks]
    })


'''
Endpoint: /drinks-details
Auth: get:drinks-detail
Arguments: None
Returns: List of drinks in long format
Expected Success Code: 200
'''


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drink_detail(jwt):
    drinks = [drink.long() for drink in Drink.query.all()]
    print(type(drinks))

    return jsonify({
        'success': True,
        'drinks': drinks
    })


'''
Endpoint: /drinks
Auth: post:drinks
Arguments: None
Returns: Array with newly created drink
Expected Success Code: 200
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    data = request.get_json()

    if 'title' and 'recipe' not in data:
        abort(422)

    title = data['title']
    recipe = json.dumps(data['recipe'])

    drink = Drink(title=title, recipe=recipe)

    drink.insert()

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


'''
Endpoint: /drinks/<drink id>
Auth: patch:drinks
Arguments: Integer of drink ID
Returns: Array with updated drink information
Expected Success Code: 200
Failure: 404. Drink of specified ID was not found
'''


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, drink_id):
    drink = Drink.query.get(drink_id)

    if drink is None:
        abort(404)

    data = request.get_json()

    if 'title' in data:
        drink.title = data['title']

    if 'recipe' in data:
        drink.recipe = json.dumps(data['recipe'])

    drink.update()

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


'''
Endpoint: /drinks/<drink id>
Auth: delete:drinks
Arguments: Integer of drink ID
Returns: ID of deleted drink
Expected Success Code: 200
Failure: 404. Drink of specified ID was not found
'''


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, drink_id):
    data = request.get_json()

    drink = Drink.query.get(drink_id)

    if drink is None:
        abort(404)

    drink.delete()

    return jsonify({
        'success': True,
        'delete': drink.id
    })


# Error Handling
'''
Error handler for 422
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
Error handler for 404
'''


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


'''
Error handler for 401
'''


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized"
    }), 401


'''
Error handler for 400
'''


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


'''
AuthError handler
'''


@app.errorhandler(AuthError)
def process_AuthError(error):
    response = jsonify(error.error)
    response.status_code = error.status_code

    return response
