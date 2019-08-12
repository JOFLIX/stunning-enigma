# -*- coding:utf-8 -*-
from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User, AnonymousUser
from . import api
from .errors import unauthorized, forbidden


auth = HTTPBasicAuth()

# The api verifies that the user is logged in. Each time the api is verified, the api first comes to this decorator function, and comes to the before_request function.
@auth.verify_password
def verify_password(email_or_token, password):
    if email_or_token == '':                  # Anonymous User
        g.current_user = AnonymousUser()
        return True
    if password == '':              # Verify with token
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token).first()   # Query by normal mailbox
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@api.route('/token')
def get_token():
    if g.current_user.is_anonymous or g.token_used:  # Anonymous user or token has been used
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(expiration=3600), 'expiration': 3600})

# Check if the user has passed verification before each request
@api.before_app_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')

@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')
