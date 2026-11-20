"""Database tables. They match the schema in Figure 4.4 (8 tables)."""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):                       # table Users  (FR01-FR06)
    __tablename__ = "Users"
    UserID = db.Column(db.Integer, primary_key=True)
    FullName = db.Column(db.String(100), nullable=False)
    Phone = db.Column(db.String(15))
    Username = db.Column(db.String(50), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    Role = db.Column(db.Enum("Owner", "Attendant"), nullable=False)
    IsActive = db.Column(db.Boolean, default=True, nullable=False)
    FailedAttempts = db.Column(db.Integer, default=0, nullable=False)
    LockedUntil = db.Column(db.DateTime)
    CreatedAt = db.Column(db.DateTime, default=datetime.now, nullable=False)


class Category(db.Model):                   # table Categories (FR07)
    __tablename__ = "Categories"
    CategoryID = db.Column(db.Integer, primary_key=True)
    CategoryName = db.Column(db.String(60), unique=True, nullable=False)


class Product(db.Model):                    # table Products (FR08-FR11)
    __tablename__ = "Products"
    ProductID = db.Column(db.Integer, primary_key=True)
    CategoryID = db.Column(db.Integer, db.ForeignKey("Categories.CategoryID"), nullable=False)
    ProductName = db.Column(db.String(100), nullable=False)
    UnitPrice = db.Column(db.Numeric(10, 2), nullable=False)
    StockQty = db.Column(db.Integer, default=0, nullable=False)
    ReorderLevel = db.Column(db.Integer, default=0, nullable=False)
    IsActive = db.Column(db.Boolean, default=True, nullable=False)
    category = db.relationship("Category")


class Sale(db.Model):                       # table Sales (FR13, FR14)
    __tablename__ = "Sales"
    SaleID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey("Users.UserID"), nullable=False)
    SaleDate = db.Column(db.DateTime, default=datetime.now, nullable=False)
    Status = db.Column(db.Enum("Completed", "Cancelled"), default="Completed", nullable=False)
    TotalAmount = db.Column(db.Numeric(10, 2), nullable=False)
    items = db.relationship("SaleItem", backref="sale")
    user = db.relationship("User")


class SaleItem(db.Model):                   # table SaleItems (FR13)
    __tablename__ = "SaleItems"
    SaleItemID = db.Column(db.Integer, primary_key=True)
    SaleID = db.Column(db.Integer, db.ForeignKey("Sales.SaleID"), nullable=False)
    ProductID = db.Column(db.Integer, db.ForeignKey("Products.ProductID"), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)
    UnitPrice = db.Column(db.Numeric(10, 2), nullable=False)   # price at the time of sale
    product = db.relationship("Product")


class StockMovement(db.Model):              # table StockMovements (FR12-FR14)
    __tablename__ = "StockMovements"
    MovementID = db.Column(db.Integer, primary_key=True)
    ProductID = db.Column(db.Integer, db.ForeignKey("Products.ProductID"), nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey("Users.UserID"), nullable=False)
    SaleID = db.Column(db.Integer, db.ForeignKey("Sales.SaleID"))
    MovementType = db.Column(db.Enum("StockIn", "StockOut", "StockReturn"), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)
    SupplierName = db.Column(db.String(100))
    MovementDate = db.Column(db.DateTime, default=datetime.now, nullable=False)


class Forecast(db.Model):                   # table Forecasts (FR15, FR17, FR18, FR24)
    __tablename__ = "Forecasts"
    ForecastID = db.Column(db.Integer, primary_key=True)
    ProductID = db.Column(db.Integer, db.ForeignKey("Products.ProductID"), nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey("Users.UserID"), nullable=False)
    PeriodStart = db.Column(db.Date, nullable=False)
    PeriodDays = db.Column(db.Integer, nullable=False)
    PredictedQty = db.Column(db.Numeric(10, 2), nullable=False)
    GeneratedAt = db.Column(db.DateTime, default=datetime.now, nullable=False)
    product = db.relationship("Product")


class BackupLog(db.Model):                  # table BackupLogs (FR16)
    __tablename__ = "BackupLogs"
    BackupID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey("Users.UserID"), nullable=False)
    FileName = db.Column(db.String(150))
    BackupDate = db.Column(db.DateTime, default=datetime.now, nullable=False)
    Status = db.Column(db.Enum("Success", "Failed"), nullable=False)
