# -*- coding:utf-8 -*-
from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission


# Decorator function with parameters, 3-layer function
def permission_required(permissions):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.can(permissions):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Call the decorator function above
def admin_required(f):
    return permission_required(Permission.ADMINISTRATOR)(f)     # With parameters, and transfer function
