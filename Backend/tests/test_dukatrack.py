"""Tests: one or more per functional requirement. Run with: pytest -q Backend/tests"""
import os, sys, tempfile
from datetime import datetime, timedelta
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models import db, User, Product, Sale, StockMovement, Forecast
from werkzeug.security import generate_password_hash

H = {"X-Requested-With": "DukaTrack"}


@pytest.fixture()
def app(tmp_path):
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "t.db"),
                      "BACKUP_DIR": str(tmp_path / "bk"), "TESTING": True})
    with app.app_context():
        from models import Category
        db.session.add_all([User(FullName="Own", Username="owner", Role="Owner", PasswordHash=generate_password_hash("Owner@123")),
                            User(FullName="Att", Username="att", Role="Attendant", PasswordHash=generate_password_hash("Attendant@123"))])
        c = Category(CategoryName="Staples"); db.session.add(c); db.session.flush()
        db.session.add(Product(ProductName="Sugar", CategoryID=c.CategoryID, UnitPrice=170, StockQty=10, ReorderLevel=5))
        db.session.commit()
    return app


def login(app, who):
    c = app.test_client()
    pw = "Owner@123" if who == "owner" else "Attendant@123"
    assert c.post("/api/login", json={"username": who, "password": pw}, headers=H).status_code == 200
    return c


def post(c, url, body=None):
    return c.post(url, json=body or {}, headers=H)


def test_fr01_fr02_login_and_wrong_password(app):
    login(app, "owner"); login(app, "att")
    assert post(app.test_client(), "/api/login", {"username": "owner", "password": "bad"}).status_code == 401


def test_lockout_after_five_failures(app):
    c = app.test_client()
    for _ in range(5):
        post(c, "/api/login", {"username": "owner", "password": "bad"})
    r = post(c, "/api/login", {"username": "owner", "password": "Owner@123"})
    assert r.status_code == 423


def test_fr05_fr06_logout_ends_session(app):
    c = login(app, "att")
    assert post(c, "/api/logout").status_code == 200
    assert c.get("/api/products").status_code == 401


def test_idle_session_expires(app):
    c = login(app, "owner")
    with c.session_transaction() as s:
        s["last_seen"] = (datetime.now() - timedelta(minutes=16)).isoformat()
    assert c.get("/api/products").status_code == 401


def test_fr03_fr04_attendant_accounts(app):
    o = login(app, "owner")
    r = post(o, "/api/attendants", {"name": "New", "username": "new1", "password": "Temp1234", "phone": "0700"})
    assert r.status_code == 201
    with app.app_context():
        assert User.query.filter_by(Username="new1").first().PasswordHash != "Temp1234"   # hashed
    assert post(o, "/api/attendants", {"name": "X", "username": "new1", "password": "Temp1234"}).status_code == 400
    assert post(o, "/api/attendants", {"name": "X", "username": "z", "password": "short"}).status_code == 400
    uid = r.get_json()["id"]
    new = app.test_client()
    assert post(new, "/api/login", {"username": "new1", "password": "Temp1234"}).status_code == 200
    assert post(o, f"/api/attendants/{uid}/deactivate").status_code == 200
    assert new.get("/api/products").status_code == 401            # access stops at once
    assert post(app.test_client(), "/api/login", {"username": "new1", "password": "Temp1234"}).status_code == 401


def test_fr07_to_fr11_catalog(app):
    o = login(app, "owner")
    cat = post(o, "/api/categories", {"name": "Drinks"}).get_json()
    assert post(o, "/api/categories", {"name": "drinks"}).status_code == 400          # duplicate
    p = post(o, "/api/products", {"name": "Soda", "category_id": cat["id"], "price": 60, "stock": 5, "reorder_level": 2}).get_json()
    assert post(o, "/api/products", {"name": "Bad", "category_id": cat["id"], "price": -1}).status_code == 400
    assert o.put(f"/api/products/{p['id']}", json={"price": 65}, headers=H).get_json()["price"] == 65
    assert o.put(f"/api/products/{p['id']}/reorder-level", json={"reorder_level": 9}, headers=H).get_json()["reorder_level"] == 9
    post(o, f"/api/products/{p['id']}/deactivate")
    assert all(x["id"] != p["id"] for x in o.get("/api/products").get_json())


def test_fr12_stock_in(app):
    o = login(app, "owner")
    r = post(o, "/api/stock-in", {"product_id": 1, "quantity": 20, "supplier": "Wholesaler"})
    assert r.status_code == 201 and r.get_json()["stock"] == 30
    assert post(o, "/api/stock-in", {"product_id": 1, "quantity": 0}).status_code == 400
    with app.app_context():
        m = StockMovement.query.one()
        assert m.MovementType == "StockIn" and m.UserID and m.MovementDate


def test_fr13_sale_reduces_stock_and_refuses_too_much(app):
    a = login(app, "att")
    r = post(a, "/api/sales", {"items": [{"product_id": 1, "quantity": 3}]})
    assert r.status_code == 201 and r.get_json()["total"] == 510
    assert post(a, "/api/sales", {"items": [{"product_id": 1, "quantity": 8}]}).status_code == 400   # only 7 left
    with app.app_context():
        assert db.session.get(Product, 1).StockQty == 7
        assert StockMovement.query.filter_by(MovementType="StockOut").count() == 1


def test_fr13_owner_cannot_record_sale(app):
    assert post(login(app, "owner"), "/api/sales", {"items": [{"product_id": 1, "quantity": 1}]}).status_code == 403


def test_fr14_cancel_returns_stock(app):
    a, o = login(app, "att"), login(app, "owner")
    sid = post(a, "/api/sales", {"items": [{"product_id": 1, "quantity": 4}]}).get_json()["id"]
    assert post(a, f"/api/sales/{sid}/cancel").status_code == 403
    assert post(o, f"/api/sales/{sid}/cancel").status_code == 200
    assert post(o, f"/api/sales/{sid}/cancel").status_code == 400
    with app.app_context():
        assert db.session.get(Product, 1).StockQty == 10
        assert StockMovement.query.filter_by(MovementType="StockReturn").count() == 1


def test_attendant_blocked_from_owner_functions(app):
    a = login(app, "att")
    for url in ["/api/attendants", "/api/categories", "/api/products", "/api/stock-in", "/api/forecasts", "/api/backups"]:
        assert post(a, url, {}).status_code in (403, 405), url
    for url in ["/api/stock/low", "/api/reports/sales", "/api/reports/sales.csv", "/api/reports/accuracy", "/api/backups"]:
        assert a.get(url).status_code == 403, url


def test_request_without_header_is_refused(app):
    c = login(app, "owner")
    assert c.post("/api/categories", json={"name": "X"}).status_code == 403


def test_fr19_fr20_fr21_stock_views(app):
    a, o = login(app, "att"), login(app, "owner")
    assert a.get("/api/stock").get_json()[0]["stock"] == 10
    post(a, "/api/sales", {"items": [{"product_id": 1, "quantity": 6}]})
    low = o.get("/api/stock/low").get_json()
    assert [p["name"] for p in low] == ["Sugar"]


def seed_sales(app, days=60):
    """Put a simple weekly pattern into the database for forecasting tests."""
    from models import Sale, SaleItem
    with app.app_context():
        u = User.query.filter_by(Role="Attendant").first()
        for t in range(days, 0, -1):
            day = datetime.now() - timedelta(days=t)
            qty = 10 + (day.weekday() == 5) * 6
            s = Sale(UserID=u.UserID, SaleDate=day, Status="Completed", TotalAmount=qty * 170)
            db.session.add(s); db.session.flush()
            db.session.add(SaleItem(SaleID=s.SaleID, ProductID=1, Quantity=qty, UnitPrice=170))
        db.session.commit()


def test_fr15_fr17_fr18_forecast(app):
    seed_sales(app)
    o, a = login(app, "owner"), login(app, "att")
    assert post(a, "/api/forecasts", {"period_days": 7}).status_code == 403
    assert post(o, "/api/forecasts", {"period_days": 5}).status_code == 400
    r = post(o, "/api/forecasts", {"period_days": 7})
    assert r.status_code == 201
    for who in (o, a):
        row = who.get("/api/forecasts/latest?period_days=7").get_json()[0]
        assert 55 < row["predicted"] < 100          # about 7 days x ~11 units
    with app.app_context():
        f = Forecast.query.one()
        assert f.UserID and f.GeneratedAt and f.PeriodDays == 7


def test_fr22_fr23_sales_report_and_csv(app):
    seed_sales(app, 10)
    o = login(app, "owner")
    rep = o.get("/api/reports/sales?period=week").get_json()
    assert rep["rows"][0]["product"] == "Sugar" and rep["total_units"] > 0
    csv_text = o.get("/api/reports/sales.csv?period=month").get_data(as_text=True)
    assert csv_text.startswith("Product,Units sold,Sales (Ksh)")
    assert o.get("/api/reports/sales?period=year").status_code == 400


def test_fr24_forecast_accuracy_only_for_finished_periods(app):
    seed_sales(app, 40)
    o = login(app, "owner")
    from forecast_api import make_forecast
    with app.app_context():
        owner = User.query.filter_by(Role="Owner").first()
        p = db.session.get(Product, 1)
        make_forecast(p, 7, (datetime.now() - timedelta(days=14)).date(), owner.UserID, datetime.now())   # finished
        make_forecast(p, 7, (datetime.now() + timedelta(days=1)).date(), owner.UserID, datetime.now())    # not finished
        db.session.commit()
    acc = o.get("/api/reports/accuracy").get_json()
    assert len(acc["detail"]) == 1 and acc["rows"][0]["mae"] >= 0


def test_fr16_backup_and_restore_file(app, tmp_path):
    o = login(app, "owner")
    r = post(o, "/api/backups").get_json()
    assert r["status"] == "Success"
    assert os.path.exists(os.path.join(app.config["BACKUP_DIR"], r["file"]))
    assert o.get("/api/backups").get_json()[0]["status"] == "Success"
    assert o.get("/" + r["file"]).status_code == 404                  # cannot be downloaded from the web


def test_nfr_performance_forecast_200_products(app):
    """NFR04: forecast for up to 200 products must finish in 60 seconds or less."""
    import time
    from models import Category, Sale, SaleItem
    with app.app_context():
        cat = Category.query.first()
        for i in range(199):
            db.session.add(Product(ProductName=f"P{i}", CategoryID=cat.CategoryID, UnitPrice=50, StockQty=100, ReorderLevel=5))
        db.session.commit()
        u = User.query.filter_by(Role="Attendant").first()
        for t in range(35, 0, -1):
            s = Sale(UserID=u.UserID, SaleDate=datetime.now() - timedelta(days=t), Status="Completed", TotalAmount=0)
            db.session.add(s); db.session.flush()
            for pid in range(1, 201):
                db.session.add(SaleItem(SaleID=s.SaleID, ProductID=pid, Quantity=3 + pid % 4, UnitPrice=50))
        db.session.commit()
    o = login(app, "owner")
    t0 = time.time()
    assert post(o, "/api/forecasts", {"period_days": 30}).status_code == 201
    assert time.time() - t0 < 60
