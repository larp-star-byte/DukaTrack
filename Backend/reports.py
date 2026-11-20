"""Module 5 - Reporting (FR22 to FR24)."""
import csv, io
from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify, Response
from sqlalchemy import func
from models import db, Product, Sale, SaleItem, Forecast
from common import ApiError, owner_only

bp = Blueprint("reports", __name__)
PERIODS = {"day": 1, "week": 7, "month": 30}      # days counted back from today


def period_range():
    name = request.args.get("period", "week")
    if name not in PERIODS:
        raise ApiError("Period must be day, week or month.")
    end = date.today()
    start = end - timedelta(days=PERIODS[name] - 1)
    return name, start, end


def sales_by_product(start, end):
    rows = db.session.query(Product.ProductName, func.sum(SaleItem.Quantity),
                            func.sum(SaleItem.Quantity * SaleItem.UnitPrice)) \
        .join(SaleItem, SaleItem.ProductID == Product.ProductID) \
        .join(Sale, Sale.SaleID == SaleItem.SaleID) \
        .filter(Sale.Status == "Completed",
                Sale.SaleDate >= datetime.combine(start, datetime.min.time()),
                Sale.SaleDate < datetime.combine(end + timedelta(days=1), datetime.min.time())) \
        .group_by(Product.ProductID, Product.ProductName).order_by(func.sum(SaleItem.Quantity).desc()).all()
    return [{"product": n, "units": int(u), "revenue": round(float(r), 2)} for n, u, r in rows]


@bp.get("/api/reports/sales")                # FR22
@owner_only
def sales_report():
    name, start, end = period_range()
    rows = sales_by_product(start, end)
    return jsonify({"period": name, "from": start.isoformat(), "to": end.isoformat(), "rows": rows,
                    "total_units": sum(r["units"] for r in rows),
                    "total_revenue": round(sum(r["revenue"] for r in rows), 2)})


@bp.get("/api/reports/sales.csv")            # FR23
@owner_only
def sales_csv():
    name, start, end = period_range()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Product", "Units sold", "Sales (Ksh)"])
    for r in sales_by_product(start, end):
        w.writerow([r["product"], r["units"], r["revenue"]])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=sales-{name}-{end}.csv"})


@bp.get("/api/reports/accuracy")             # FR24 only forecasts whose period has finished
@owner_only
def accuracy():
    today, detail, by_product = date.today(), [], {}
    for f in Forecast.query.order_by(Forecast.PeriodStart).all():
        last_day = f.PeriodStart + timedelta(days=f.PeriodDays - 1)
        if last_day >= today:
            continue                          # period not finished yet
        actual = db.session.query(func.coalesce(func.sum(SaleItem.Quantity), 0)) \
            .join(Sale, Sale.SaleID == SaleItem.SaleID) \
            .filter(Sale.Status == "Completed", SaleItem.ProductID == f.ProductID,
                    Sale.SaleDate >= datetime.combine(f.PeriodStart, datetime.min.time()),
                    Sale.SaleDate < datetime.combine(last_day + timedelta(days=1), datetime.min.time())).scalar()
        err = abs(float(f.PredictedQty) - float(actual))
        detail.append({"product": f.product.ProductName, "start": f.PeriodStart.isoformat(),
                       "days": f.PeriodDays, "predicted": float(f.PredictedQty),
                       "actual": int(actual), "error": round(err, 2)})
        by_product.setdefault(f.product.ProductName, []).append((float(f.PredictedQty), float(actual), err))
    rows = [{"product": n, "forecasts": len(v), "predicted": round(sum(x[0] for x in v) / len(v), 1),
             "actual": round(sum(x[1] for x in v) / len(v), 1),
             "mae": round(sum(x[2] for x in v) / len(v), 2)} for n, v in sorted(by_product.items())]
    return jsonify({"rows": rows, "detail": detail})
