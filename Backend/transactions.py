"""Module 3 - Stock and sales recording (FR12 to FR14)."""
from datetime import datetime, date
from flask import Blueprint, request, jsonify, g
from models import db, Product, Sale, SaleItem, StockMovement
from common import ApiError, login_required, owner_only, attendant_only, whole_number, text

bp = Blueprint("transactions", __name__)


@bp.post("/api/stock-in")                   # FR12 Owner records stock-in
@owner_only
def stock_in():
    d = request.get_json(silent=True) or {}
    p = db.session.get(Product, d.get("product_id") or 0)
    if not p or not p.IsActive:
        raise ApiError("Choose a product.")
    qty = whole_number(d.get("quantity"), "Quantity", 1)
    when = datetime.now()
    if d.get("date"):
        try:
            day = date.fromisoformat(d["date"])
        except ValueError:
            raise ApiError("Date is not valid.")
        if day > date.today():
            raise ApiError("Date cannot be in the future.")
        when = datetime.combine(day, datetime.now().time())
    # stock level and stock movement are saved together, or not at all (NFR06)
    p.StockQty += qty
    db.session.add(StockMovement(ProductID=p.ProductID, UserID=g.user.UserID, MovementType="StockIn",
                                 Quantity=qty, SupplierName=(d.get("supplier") or "").strip()[:100] or None,
                                 MovementDate=when))
    db.session.commit()
    return jsonify({"product": p.ProductName, "stock": p.StockQty}), 201


def sale_json(s):
    return {"id": s.SaleID, "date": s.SaleDate.isoformat(timespec="minutes"), "status": s.Status,
            "total": float(s.TotalAmount), "attendant": s.user.FullName,
            "items": [{"product": i.product.ProductName, "quantity": i.Quantity, "price": float(i.UnitPrice)}
                      for i in s.items]}


@bp.post("/api/sales")                      # FR13 Attendant records a sale
@attendant_only
def record_sale():
    items = (request.get_json(silent=True) or {}).get("items")
    if not isinstance(items, list) or not items:
        raise ApiError("Add at least one item.")
    wanted = {}                              # join repeated products into one quantity
    for it in items:
        pid = whole_number(it.get("product_id"), "Product", 1)
        wanted[pid] = wanted.get(pid, 0) + whole_number(it.get("quantity"), "Quantity", 1)
    products = {}
    for pid, qty in wanted.items():
        p = db.session.get(Product, pid)
        if not p or not p.IsActive:
            raise ApiError("A product on the sale is not available.")
        if qty > p.StockQty:                 # never sell more than the stock held
            raise ApiError(f"Only {p.StockQty} of {p.ProductName} in stock.")
        products[pid] = p
    now = datetime.now()
    sale = Sale(UserID=g.user.UserID, SaleDate=now, Status="Completed", TotalAmount=0)
    db.session.add(sale)
    db.session.flush()
    total = 0
    for pid, qty in wanted.items():
        p = products[pid]
        total += float(p.UnitPrice) * qty
        db.session.add(SaleItem(SaleID=sale.SaleID, ProductID=pid, Quantity=qty, UnitPrice=p.UnitPrice))
        db.session.add(StockMovement(ProductID=pid, UserID=g.user.UserID, SaleID=sale.SaleID,
                                     MovementType="StockOut", Quantity=qty, MovementDate=now))
        p.StockQty -= qty
    sale.TotalAmount = round(total, 2)
    db.session.commit()                      # sale, items, stock and movements: all or nothing
    return jsonify(sale_json(sale)), 201


@bp.get("/api/sales")
@login_required
def list_sales():
    q = Sale.query.order_by(Sale.SaleDate.desc())
    if g.user.Role == "Attendant":           # an attendant sees only their own recent sales
        q = q.filter_by(UserID=g.user.UserID)
    return jsonify([sale_json(s) for s in q.limit(30)])


@bp.post("/api/sales/<int:sid>/cancel")     # FR14 Owner cancels a sale
@owner_only
def cancel_sale(sid):
    s = db.session.get(Sale, sid)
    if not s:
        raise ApiError("Sale not found.", 404)
    if s.Status == "Cancelled":
        raise ApiError("This sale is already cancelled.")
    s.Status = "Cancelled"
    now = datetime.now()
    for i in s.items:
        i.product.StockQty += i.Quantity     # quantities go back to stock
        db.session.add(StockMovement(ProductID=i.ProductID, UserID=g.user.UserID, SaleID=s.SaleID,
                                     MovementType="StockReturn", Quantity=i.Quantity, MovementDate=now))
    db.session.commit()
    return jsonify(sale_json(s))
