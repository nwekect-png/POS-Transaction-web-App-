from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

app = Flask(__name__)

pp.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pos_transaction.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# =========================
# USER TABLE
# =========================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30))
    password = db.Column(db.String(255), nullable=False)
    transaction_pin = db.Column(db.String(255))
    role = db.Column(db.String(30), default="Agent")
    status = db.Column(db.String(30), default="Active")
    wallet_balance = db.Column(db.Float, default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"


# =========================
# TRANSACTION TABLE
# =========================
class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_reference = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    sender_name = db.Column(db.String(150))
    receiver_name = db.Column(db.String(150))
    account_number = db.Column(db.String(50))
    bank_name = db.Column(db.String(150))

    transaction_type = db.Column(
        db.String(50),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False,
        default=0.00
    )

    description = db.Column(db.String(255))

    status = db.Column(
        db.String(30),
        default="Success"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Transaction {self.transaction_reference}>"


# =========================
# RECEIPT TABLE
# =========================
class Receipt(db.Model):
    __tablename__ = "receipts"

    id = db.Column(db.Integer, primary_key=True)

    receipt_number = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    transaction_reference = db.Column(
        db.String(100),
        nullable=False
    )

    customer = db.Column(
        db.String(150),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    transaction_type = db.Column(
        db.String(50),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Receipt {self.receipt_number}>"


# =========================
# CREATE DATABASE
# =========================
with app.app_context():

    db.create_all()

    print("====================================")
    print("POS TRANSACTION DATABASE CREATED")
    print("====================================")
    print("Database: pos_transaction.db")
    print("Tables created:")
    print(" - users")
    print(" - transactions")
    print(" - receipts")
    print("====================================")


if __name__ == "__main__":
    app.run(debug=True)
