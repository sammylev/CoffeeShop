import json
from flask import request, _request_ctx_stack
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from jose import jwt
from urllib.request import urlopen
import logging
from logging import FileHandler, Formatter


AUTH0_DOMAIN = 'dev-sammylev.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffeeshop'
CLIENT_ID = 'rDKQ03XlEr3kjgznJVHtaeELsVQh6DUX'

# Set up logging

logging.basicConfig(filename='error.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header

'''
Get Auth Token Header. Split bearer and token

Returns: Token from header

Raises an AuthError if no header is present
Raise an AuthError if the header is malformed
'''


def get_token_auth_header():
    auth = request.headers.get('Authorization', None)

    if not auth:
        raise AuthError('Authorization header is missing', 401)

    parts = auth.split()

    if len(parts) != 2:
        raise AuthError('Invalid Header - 2 parts not detected', 401)
    elif parts[0].lower() != 'bearer':
        raise AuthError('Invalid Header - Must start with bearer', 401)

    return parts[1]


'''
Check permissions(permission, payload) method
Inputs:
    Permission: string permission (i.e. 'post:drink')
    Payload: decoded jwt payload

Returns: If success, true

Raise an AuthError if permissions are not included in the payload
Raise an AuthError if the requested permission string is not in the payload
'''


def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError('Invalid Header - Permissions not in payload/JWT', 400)

    if permission not in payload['permissions']:
        raise AuthError('unauthorized', 401)


'''
Verify Decode JWT
Inputs: Json web token (string)

Validates Auth0 token with key id and using /.well-known/jwks.json

Returns: Decoded payload

Raise an AuthError if token is expired
Raise an AuthError is invalid claims
Raise an AuthError if kid isn't in header
'''


def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    json_web_key = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}

    if 'kid' not in unverified_header:
        raise AuthError('Invalid Header - Kid not in header', 401)

    for key in json_web_key['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    if rsa_key:
        try:
            payload = jwt.decode(token,
                                 rsa_key,
                                 algorithms=ALGORITHMS,
                                 audience=API_AUDIENCE,
                                 issuer=f'https://{AUTH0_DOMAIN}/')
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError('Token Expired', 401)

        except jwt.JWTClaimsError:
            raise AuthError('Invalid Claims', 401)

        except Exception:
            raise AuthError('Invalid Header - Exception Found', 400)

    raise AuthError('Invalid Header - Unable to decode jwt', 400)


'''
Requires Auth decorator method

Inputs: string permission (i.e. 'post:drink')

Returns: Decorator which passes the decoded payload to the decorated method

Use the get_token_auth_header method to get the token
Use the verify_decode_jwt method to decode the jwt
Use the check_permissions method to check the requested permission
'''


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
