"""Module 4 - Forecasting (FR15, FR17, FR18)."""
from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify, g
from sqlalchemy import func
from models import db, Product, Sale, SaleItem, Forecast
from common import ApiError, login_required, owner_only, whole_number
from forecasting import forecast_total, daily_series

bp = Blueprint("forecast", __name__)


def sales_rows(product_id, before_day=None):
    """(day, quantity) of completed sales for a product, optionally only before a day."""
    q = db.session.query(func.date(Sale.SaleDate), func.sum(SaleItem.Quantity)) \
        .join(SaleItem, SaleItem.SaleID == Sale.SaleID) \
        .filter(Sale.Status == "Completed", SaleItem.ProductID == product_id)
    if before_day:
        q = q.filter(Sale.SaleDate < datetime.combine(before_day, datetime.min.time()))
    rows = q.group_by(func.date(Sale.SaleDate)).all()
    return [(date.fromisoformat(str(d)), int(qty)) for d, qty in rows]


def make_forecast(product, days, start_day, user_id, generated_at):
    """Used by the API and by the seed script (for past forecasts)."""
    rows = sales_rows(product.ProductID, before_day=start_day)
    series = daily_series(rows, start_day - timedelta(days=1))
    total, method = forecast_total(series, days)
    f = Forecast(ProductID=product.ProductID, UserID=user_id, PeriodStart=start_day, PeriodDays=days,
                 PredictedQty=round(total, 2), GeneratedAt=generated_at)
    db.session.add(f)
    return f, method


@bp.post("/api/forecasts")                  # FR15 Owner generates a forecast
@owner_only
def generate():
    d = request.get_json(silent=True) or {}
    days = whole_number(d.get("period_days"), "Period", 1)
    if days not in (7, 30):
        raise ApiError("Period must be 7 or 30 days.")
    if d.get("product_id"):
        p = db.session.get(Product, d["product_id"])
        if not p or not p.IsActive:
            raise ApiError("Product not found.", 404)
        products = [p]
    else:
        products = Product.query.filter_by(IsActive=True).all()
    now, start = datetime.now(), date.today() + timedelta(days=1)
    methods = {}
    for p in products:
        f, m = make_forecast(p, days, start, g.user.UserID, now)
        methods[m] = methods.get(m, 0) + 1
    db.session.commit()
    return jsonify({"products": len(products), "period_days": days, "start": start.isoformat(),
                    "methods": methods}), 201


@bp.get("/api/forecasts/latest")            # FR17 Owner and FR18 Attendant (read-only)
@login_required
def latest():
    days = request.args.get("period_days", type=int)
    out = []
    for p in Product.query.filter_by(IsActive=True).order_by(Product.ProductName):
        q = Forecast.query.filter_by(ProductID=p.ProductID)
        if days:
            q = q.filter_by(PeriodDays=days)
        f = q.order_by(Forecast.GeneratedAt.desc(), Forecast.ForecastID.desc()).first()
        if not f:
            continue
        rows = sales_rows(p.ProductID)
        recent = daily_series(rows, date.today() - timedelta(days=1)).tail(28)   # finished days only
        out.append({"product_id": p.ProductID, "product": p.ProductName, "stock": p.StockQty,
                    "predicted": float(f.PredictedQty), "period_days": f.PeriodDays,
                    "period_start": f.PeriodStart.isoformat(),
                    "generated_at": f.GeneratedAt.isoformat(timespec="minutes"),
                    "history": [float(x) for x in recent.values],
                    "enough_stock": p.StockQty >= float(f.PredictedQty)})
    return jsonify(out)
