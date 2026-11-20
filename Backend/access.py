"""Module 1 - Access control (FR01 to FR06)."""
from datetime import datetime, timedelta
from flask import Blueprint, request, session, g, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from common import ApiError, login_required, owner_only, text

bp = Blueprint("access", __name__)
MAX_ATTEMPTS, LOCK_MINUTES = 5, 15


def user_json(u):
    return {"id": u.UserID, "name": u.FullName, "phone": u.Phone, "username": u.Username,
            "role": u.Role, "active": u.IsActive}


@bp.post("/api/login")                      # FR01 (Owner) and FR02 (Attendant)
def login():
    data = request.get_json(silent=True) or {}
    username, password = (data.get("username") or "").strip(), data.get("password") or ""
    user = User.query.filter_by(Username=username).first()
    now = datetime.now()
    if user and user.LockedUntil and user.LockedUntil > now:
        mins = int((user.LockedUntil - now).total_seconds() // 60) + 1
        raise ApiError(f"Account locked. Try again in {mins} minute(s).", 423)
    if not user or not user.IsActive or not check_password_hash(user.PasswordHash, password):
        if user and user.IsActive:
            user.FailedAttempts += 1
            if user.FailedAttempts >= MAX_ATTEMPTS:          # lock for 15 minutes
                user.LockedUntil = now + timedelta(minutes=LOCK_MINUTES)
                user.FailedAttempts = 0
            db.session.commit()
        raise ApiError("Wrong username or password.", 401)   # same message for every case
    user.FailedAttempts, user.LockedUntil = 0, None
    db.session.commit()
    session.clear()
    session["user_id"], session["last_seen"] = user.UserID, now.isoformat()
    return jsonify(user_json(user))


@bp.post("/api/logout")                     # FR05 (Owner) and FR06 (Attendant)
@login_required
def logout():
    session.clear()
    return jsonify({"ok": True})


@bp.get("/api/me")
@login_required
def me():
    return jsonify(user_json(g.user))


@bp.post("/api/attendants")                 # FR03 Owner creates attendant account
@owner_only
def create_attendant():
    d = request.get_json(silent=True) or {}
    name = text(d.get("name"), "Name", 100)
    username = text(d.get("username"), "Username", 50)
    password = d.get("password") or ""
    phone = (d.get("phone") or "").strip()[:15]
    if len(password) < 8:
        raise ApiError("Temporary password must have at least 8 characters.")
    if User.query.filter_by(Username=username).first():
        raise ApiError("That username is already taken.")
    u = User(FullName=name, Phone=phone, Username=username, Role="Attendant",
             PasswordHash=generate_password_hash(password))     # only the hash is stored
    db.session.add(u)
    db.session.commit()
    return jsonify(user_json(u)), 201


@bp.get("/api/attendants")
@owner_only
def list_attendants():
    users = User.query.filter_by(Role="Attendant").order_by(User.FullName).all()
    return jsonify([user_json(u) for u in users])


@bp.post("/api/attendants/<int:uid>/deactivate")   # FR04 Owner deactivates attendant account
@owner_only
def deactivate_attendant(uid):
    u = db.session.get(User, uid)
    if not u or u.Role != "Attendant":
        raise ApiError("Attendant not found.", 404)
    u.IsActive = False                  # history is kept; login now fails
    db.session.commit()
    return jsonify(user_json(u))
