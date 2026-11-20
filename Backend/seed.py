"""Creates a demo shop with 120 days of realistic sales so the forecast has something to learn from.
Run:  python seed.py      (this RESETS the database)"""
import os, random
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash
from app import create_app, BASE
from models import db, User, Category, Product, Sale, SaleItem, StockMovement

HISTORY_DAYS = 120
RUN_LOW = {"Maize flour 2kg", "Eggs (each)", "Bread 400g"}
WEEK = [0.80, 0.85, 0.90, 1.00, 1.20, 1.45, 1.05]        # Mon..Sun, Saturday is busiest
CATS = ["Staples", "Dairy and bakery", "Drinks", "Household"]
# name, category, price (Ksh), average units per day, reorder level
PRODUCTS = [
    ("Maize flour 2kg", "Staples", 155, 18, 22), ("Sugar 1kg", "Staples", 170, 12, 14),
    ("Cooking oil 1L", "Staples", 330, 6, 7), ("Rice 1kg", "Staples", 190, 5, 6),
    ("Wheat flour 2kg", "Staples", 190, 4, 5), ("Fresh milk 500ml", "Dairy and bakery", 65, 20, 24),
    ("Bread 400g", "Dairy and bakery", 65, 15, 18), ("Eggs (each)", "Dairy and bakery", 18, 30, 36),
    ("Soda 500ml", "Drinks", 60, 14, 17), ("Tea leaves 250g", "Drinks", 120, 4, 5),
    ("Bar soap", "Household", 55, 7, 8), ("Toilet paper", "Household", 45, 5, 6)]


def run():
    db_file = os.path.join(BASE, "dukatrack.db")
    if os.path.exists(db_file) and "DATABASE_URL" not in os.environ:
        os.remove(db_file)
    app = create_app()
    with app.app_context():
        db.drop_all(); db.create_all()
        rnd = random.Random(7)
        owner = User(FullName="Wanjiru Kamau", Phone="0712345678", Username="owner", Role="Owner",
                     PasswordHash=generate_password_hash("Owner@123"))
        amina = User(FullName="Amina Hassan", Phone="0722000111", Username="amina", Role="Attendant",
                     PasswordHash=generate_password_hash("Attendant@123"))
        brian = User(FullName="Brian Otieno", Phone="0733000222", Username="brian", Role="Attendant",
                     PasswordHash=generate_password_hash("Attendant@123"))
        db.session.add_all([owner, amina, brian])
        cats = {n: Category(CategoryName=n) for n in CATS}
        db.session.add_all(cats.values()); db.session.flush()
        prods = []
        for name, cat, price, base, reorder in PRODUCTS:
            p = Product(ProductName=name, CategoryID=cats[cat].CategoryID, UnitPrice=price, StockQty=0,
                        ReorderLevel=reorder)
            db.session.add(p); prods.append((p, base))
        db.session.flush()

        today = date.today()
        first = today - timedelta(days=HISTORY_DAYS)
        for t in range(HISTORY_DAYS):
            day = first + timedelta(days=t)
            # the owner restocks on Monday and Thursday; three items are given a smaller top-up so they end the history low
            if day.weekday() in (0, 3):
                for p, base in prods:
                    target = int(base * (6.5 if p.ProductName in RUN_LOW else 8.5))
                    if p.StockQty < target:
                        qty = target - p.StockQty
                        p.StockQty += qty
                        db.session.add(StockMovement(ProductID=p.ProductID, UserID=owner.UserID, MovementType="StockIn",
                                                     Quantity=qty, SupplierName="Wholesaler",
                                                     MovementDate=datetime.combine(day, datetime.min.time()) + timedelta(hours=6, minutes=30)))
            n_sales = rnd.randint(14, 22)
            baskets = [dict() for _ in range(n_sales)]
            for p, base in prods:
                mean = base * WEEK[day.weekday()] * (1 + 0.003 * t)
                demand = max(0, int(rnd.gauss(mean, mean * 0.18)))
                while demand > 0:
                    chunk = min(demand, rnd.choice([1, 1, 2, 2, 3]))
                    b = baskets[rnd.randrange(n_sales)]
                    b[p] = b.get(p, 0) + chunk
                    demand -= chunk
            times = sorted(rnd.randint(7 * 60, 20 * 60) for _ in range(n_sales))
            for b, minute in zip(baskets, times):
                items = {p: min(q, p.StockQty) for p, q in b.items() if p.StockQty > 0}
                items = {p: q for p, q in items.items() if q > 0}
                if not items:
                    continue
                when = datetime.combine(day, datetime.min.time()) + timedelta(minutes=minute)
                clerk = amina if rnd.random() < 0.55 else brian
                sale = Sale(UserID=clerk.UserID, SaleDate=when, Status="Completed", TotalAmount=0)
                db.session.add(sale); db.session.flush()
                total = 0
                for p, q in items.items():
                    total += float(p.UnitPrice) * q
                    p.StockQty -= q
                    db.session.add(SaleItem(SaleID=sale.SaleID, ProductID=p.ProductID, Quantity=q, UnitPrice=p.UnitPrice))
                    db.session.add(StockMovement(ProductID=p.ProductID, UserID=clerk.UserID, SaleID=sale.SaleID,
                                                 MovementType="StockOut", Quantity=q, MovementDate=when))
                sale.TotalAmount = total
            db.session.flush()
        db.session.commit()

        # Past forecasts (made earlier, using only the sales known on that day) so FR24 has finished periods to check.
        from forecast_api import make_forecast
        for start_ago, days in ((14, 7), (7, 7), (30, 30)):
            start = today - timedelta(days=start_ago)
            made_at = datetime.combine(start, datetime.min.time()) + timedelta(hours=8)
            for p, _ in prods:
                make_forecast(p, days, start, owner.UserID, made_at)
        # This morning's forecasts, so the Forecast screen is not empty when the demo opens.
        this_morning = datetime.combine(today, datetime.min.time()) + timedelta(hours=7)
        for p, _ in prods:
            for days in (7, 30):
                make_forecast(p, days, today + timedelta(days=1), owner.UserID, this_morning)
        db.session.commit()
        print("Demo data ready:", Sale.query.count(), "sales,", Product.query.count(), "products.")
        print("Owner login: owner / Owner@123   Attendant login: amina / Attendant@123")


if __name__ == "__main__":
    run()
