"""Module 2 - Product and category management (FR07 to FR11) and stock views (FR19 to FR21)."""
from flask import Blueprint, request, jsonify, g
from models import db, Category, Product
from common import ApiError, login_required, owner_only, text, money, whole_number

bp = Blueprint("catalog", __name__)


def product_json(p):
    return {"id": p.ProductID, "name": p.ProductName, "category_id": p.CategoryID,
            "category": p.category.CategoryName, "price": float(p.UnitPrice),
            "stock": p.StockQty, "reorder_level": p.ReorderLevel, "active": p.IsActive,
            "low": p.StockQty <= p.ReorderLevel}


@bp.get("/api/categories")
@login_required
def list_categories():
    return jsonify([{"id": c.CategoryID, "name": c.CategoryName}
                    for c in Category.query.order_by(Category.CategoryName)])


@bp.post("/api/categories")                 # FR07
@owner_only
def add_category():
    name = text((request.get_json(silent=True) or {}).get("name"), "Category name", 60)
    if Category.query.filter(db.func.lower(Category.CategoryName) == name.lower()).first():
        raise ApiError("That category already exists.")
    c = Category(CategoryName=name)
    db.session.add(c)
    db.session.commit()
    return jsonify({"id": c.CategoryID, "name": c.CategoryName}), 201


@bp.get("/api/products")
@login_required
def list_products():
    q = Product.query
    if not (g.user.Role == "Owner" and request.args.get("all") == "1"):
        q = q.filter_by(IsActive=True)      # inactive products are hidden from forms
    return jsonify([product_json(p) for p in q.order_by(Product.ProductName)])


@bp.post("/api/products")                   # FR08
@owner_only
def add_product():
    d = request.get_json(silent=True) or {}
    name = text(d.get("name"), "Product name", 100)
    if not db.session.get(Category, d.get("category_id") or 0):
        raise ApiError("Choose a category.")
    p = Product(ProductName=name, CategoryID=d["category_id"], UnitPrice=money(d.get("price"), "Unit price"),
                StockQty=whole_number(d.get("stock", 0), "Opening stock"),
                ReorderLevel=whole_number(d.get("reorder_level", 0), "Reorder level"))
    db.session.add(p)
    db.session.commit()
    return jsonify(product_json(p)), 201


def get_product(pid):
    p = db.session.get(Product, pid)
    if not p:
        raise ApiError("Product not found.", 404)
    return p


@bp.put("/api/products/<int:pid>")          # FR09 (past sales keep their own price)
@owner_only
def edit_product(pid):
    p, d = get_product(pid), request.get_json(silent=True) or {}
    if "name" in d:
        p.ProductName = text(d["name"], "Product name", 100)
    if "category_id" in d:
        if not db.session.get(Category, d["category_id"] or 0):
            raise ApiError("Choose a category.")
        p.CategoryID = d["category_id"]
    if "price" in d:
        p.UnitPrice = money(d["price"], "Unit price")
    db.session.commit()
    return jsonify(product_json(p))


@bp.post("/api/products/<int:pid>/deactivate")   # FR10
@owner_only
def deactivate_product(pid):
    p = get_product(pid)
    p.IsActive = False
    db.session.commit()
    return jsonify(product_json(p))


@bp.put("/api/products/<int:pid>/reorder-level")  # FR11
@owner_only
def set_reorder_level(pid):
    p = get_product(pid)
    p.ReorderLevel = whole_number((request.get_json(silent=True) or {}).get("reorder_level"), "Reorder level")
    db.session.commit()
    return jsonify(product_json(p))


@bp.get("/api/stock")                       # FR19 Owner, FR20 Attendant (read-only)
@login_required
def stock_levels():
    ps = Product.query.filter_by(IsActive=True).order_by(Product.ProductName).all()
    return jsonify([product_json(p) for p in ps])


@bp.get("/api/stock/low")                   # FR21 Owner
@owner_only
def low_stock():
    ps = Product.query.filter(Product.IsActive == True, Product.StockQty <= Product.ReorderLevel) \
        .order_by(Product.StockQty).all()
    return jsonify([product_json(p) for p in ps])
