"""DukaTrack - start from the project root with: python Backend/app.py"""
import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, session, request, g
from models import db, User
from common import ApiError

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE)
PUBLIC = {"/api/login"}


def create_app(config=None):
    app = Flask(__name__, static_folder=os.path.join(PROJECT_ROOT, "static"), static_url_path="")
    app.config.update(
        # SQLite for the demo. For MySQL set DATABASE_URL=mysql+pymysql://user:password@localhost/dukatrack
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(BASE, "dukatrack.db")),
        SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-secret-before-real-use"),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
        IDLE_MINUTES=15, BACKUP_DIR=os.path.join(BASE, "backups"))
    if config:
        app.config.update(config)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    import access, catalog, transactions, forecast_api, reports, backup
    for module in (access, catalog, transactions, forecast_api, reports, backup):
        app.register_blueprint(module.bp)

    @app.before_request
    def guard():
        """Runs before every API call: who is this, and is the session still alive?"""
        g.user = None
        if not request.path.startswith("/api/"):
            return
        if request.method != "GET" and request.headers.get("X-Requested-With") != "DukaTrack":
            raise ApiError("Request refused.", 403)         # simple protection against forged requests
        if request.path in PUBLIC:
            return
        uid, seen = session.get("user_id"), session.get("last_seen")
        if uid and seen:
            idle = datetime.now() - datetime.fromisoformat(seen)
            user = db.session.get(User, uid)
            if idle > timedelta(minutes=app.config["IDLE_MINUTES"]) or not user or not user.IsActive:
                session.clear()
                raise ApiError("Session ended. Please log in again.", 401)
            g.user = user
            session["last_seen"] = datetime.now().isoformat()

    @app.errorhandler(ApiError)
    def api_error(e):
        return jsonify({"error": e.message}), e.status

    @app.get("/")
    def home():
        return app.send_static_file("Frontend/index.html")

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000, debug=False)
