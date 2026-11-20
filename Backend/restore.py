"""Restores the database from a backup file made by FR16.   python restore.py backups/<file>.json.gz
WARNING: replaces everything currently stored."""
import gzip, json, sys
from datetime import datetime, date
from app import create_app
from models import db, User, Category, Product, Sale, SaleItem, StockMovement, Forecast

ORDER = [User, Category, Product, Sale, SaleItem, StockMovement, Forecast]


def convert(column, value):
    if value is None:
        return None
    kind = column.type.__class__.__name__
    if kind == "DateTime":
        return datetime.fromisoformat(value)
    if kind == "Date":
        return date.fromisoformat(value)
    return value


if __name__ == "__main__":
    with gzip.open(sys.argv[1], "rt", encoding="utf-8") as fh:
        data = json.load(fh)
    app = create_app()
    with app.app_context():
        for m in reversed(ORDER):
            m.query.delete()
        for m in ORDER:
            for row in data[m.__tablename__]:
                db.session.add(m(**{c.name: convert(c, row[c.name]) for c in m.__table__.columns}))
            db.session.flush()
        db.session.commit()
        print("Restored from", sys.argv[1])
