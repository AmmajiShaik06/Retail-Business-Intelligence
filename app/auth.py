from functools import wraps
from flask import session


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return {
                "status": "error",
                "message": "Login required"
            }, 401

        return f(*args, **kwargs)

    return decorated_function


def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                return {
                    "status": "error",
                    "message": "Login required"
                }, 401

            if session.get("role") != required_role:
                return {
                    "status": "error",
                    "message": "Access denied"
                }, 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator