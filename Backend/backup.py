"""Module 6 - Data protection (FR16). Backups are saved OUTSIDE the web folder, so they cannot be downloaded
from the browser; only the Shop Owner can start one."""
import gzip, json, os
from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, jsonify, g, current_app
from models import db, User, Category, Product, Sale, SaleItem, StockMovement, Forecast, BackupLog
from common import owner_only

bp = Blueprint("backup", __name__)
TABLES = [User, Category, Product, Sale, SaleItem, StockMovement, Forecast]   # all records (NFR07)


def plain(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


@bp.post("/api/backups")                     # FR16
@owner_only
def make_backup():
    folder = current_app.config["BACKUP_DIR"]
    os.makedirs(folder, exist_ok=True)
    name = datetime.now().strftime("dukatrack-backup-%Y%m%d-%H%M%S.json.gz")
    try:
        data = {m.__tablename__: [{c.name: plain(getattr(r, c.name)) for c in m.__table__.columns}
                                  for r in m.query.all()] for m in TABLES}
        with gzip.open(os.path.join(folder, name), "wt", encoding="utf-8") as fh:
            json.dump(data, fh)
        os.chmod(os.path.join(folder, name), 0o600)       # readable by the owner account only
        status = "Success"
    except Exception:
        status, name = "Failed", None
    log = BackupLog(UserID=g.user.UserID, FileName=name, BackupDate=datetime.now(), Status=status)
    db.session.add(log)
    db.session.commit()
    return jsonify({"status": status, "file": name}), 201 if status == "Success" else 500


@bp.get("/api/backups")
@owner_only
def list_backups():
    logs = BackupLog.query.order_by(BackupLog.BackupDate.desc()).limit(10).all()
    return jsonify([{"date": b.BackupDate.isoformat(timespec="minutes"), "file": b.FileName,
                     "status": b.Status, "by": db.session.get(User, b.UserID).FullName} for b in logs])
