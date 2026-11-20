"""Small helpers shared by every module: errors, role checks, number checks."""
from functools import wraps
from flask import g, jsonify


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message, self.status = message, status


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        if getattr(g, "user", None) is None:
            raise ApiError("Please log in.", 401)
        return fn(*a, **k)
    return wrapper


def role_required(role):
    """Role is checked on the SERVER for every request (NFR01)."""
    def deco(fn):
        @wraps(fn)
        @login_required
        def wrapper(*a, **k):
            if g.user.Role != role:
                raise ApiError(f"Only the Shop {role} can do this.", 403)
            return fn(*a, **k)
        return wrapper
    return deco


owner_only = role_required("Owner")
attendant_only = role_required("Attendant")


def whole_number(value, name, minimum=0):
    try:
        number = int(value)
        if str(value).strip() != str(number) and not isinstance(value, int):
            raise ValueError
    except (TypeError, ValueError):
        raise ApiError(f"{name} must be a whole number.")
    if number < minimum:
        raise ApiError(f"{name} must be {minimum} or more.")
    return number


def money(value, name):
    try:
        number = round(float(value), 2)
    except (TypeError, ValueError):
        raise ApiError(f"{name} must be a number.")
    if number <= 0:
        raise ApiError(f"{name} must be more than 0.")
    return number


def text(value, name, max_len):
    value = (value or "").strip() if isinstance(value, str) or value is None else str(value).strip()
    if not value:
        raise ApiError(f"{name} is required.")
    if len(value) > max_len:
        raise ApiError(f"{name} is too long.")
    return value
