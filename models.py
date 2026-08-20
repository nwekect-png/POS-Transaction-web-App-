from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ============================================================
# USER MODEL
# ============================================================

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(150), nullable=False)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False,
        index=True
    )

    phone = db.Column(
        db.String(30),
        unique=True,
        nullable=True
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    transaction_pin = db.Column(
        db.String(255),
        nullable=True
    )

    role = db.Column(
        db.String(30),
        default="Agent",
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Active",
        nullable=False
    )

    wallet_balance = db.Column(
        db.Float,
        default=0.00,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # --------------------------------------------------------
    # Password methods
    # --------------------------------------------------------

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    # --------------------------------------------------------
    # Transaction PIN methods
    # --------------------------------------------------------

    def set_transaction_pin(self, pin):
        self.transaction_pin = generate_password_hash(str(pin))

    def check_transaction_pin(self, pin):
        if not self.transaction_pin:
            return False

        return check_password_hash(
            self.transaction_pin,
            str(pin)
        )

    # --------------------------------------------------------
    # User representation
    # --------------------------------------------------------

    def __repr__(self):
        return f"<User {self.username}>"


# ============================================================
# TRANSACTION MODEL
# ============================================================

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    transaction_reference = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    sender_name = db.Column(
        db.String(150),
        nullable=True
    )

    receiver_name = db.Column(
        db.String(150),
        nullable=True
    )

    account_number = db.Column(
        db.String(50),
        nullable=True
    )

    bank_name = db.Column(
        db.String(150),
        nullable=True
    )

    transaction_type = db.Column(
        db.String(50),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="Success",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    sender = db.relationship(
        "User",
        foreign_keys=[sender_id],
        backref="sent_transactions"
    )

    receiver = db.relationship(
        "User",
        foreign_keys=[receiver_id],
        backref="received_transactions"
    )

    def __repr__(self):
        return (
            f"<Transaction "
            f"{self.transaction_reference}>"
        )


# ============================================================
# RECEIPT MODEL
# ============================================================

class Receipt(db.Model):
    __tablename__ = "receipts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    receipt_number = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
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
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<Receipt {self.receipt_number}>"


# ============================================================
# NOTIFICATION MODEL
# ============================================================

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    notification_type = db.Column(
        db.String(50),
        default="info"
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        backref="notifications"
    )

    def __repr__(self):
        return f"<Notification {self.title}>"


# ============================================================
# WALLET MODEL
# ============================================================

class Wallet(db.Model):
    __tablename__ = "wallets"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    balance = db.Column(
        db.Float,
        default=0.00,
        nullable=False
    )

    currency = db.Column(
        db.String(10),
        default="NGN",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "wallet",
            uselist=False
        )
    )

    def __repr__(self):
        return f"<Wallet {self.user_id}>"


# ============================================================
# LOGIN ACTIVITY MODEL
# ============================================================

class LoginActivity(db.Model):
    __tablename__ = "login_activities"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    ip_address = db.Column(
        db.String(100),
        nullable=True
    )

    user_agent = db.Column(
        db.String(500),
        nullable=True
    )

    login_time = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        backref="login_activities"
    )

    def __repr__(self):
        return f"<LoginActivity {self.user_id}>"


# ============================================================
# PASSWORD RESET MODEL
# ============================================================

class PasswordReset(db.Model):
    __tablename__ = "password_resets"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    token = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    used = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        backref="password_resets"
    )

    def __repr__(self):
        return f"<PasswordReset {self.user_id}>"
    
    from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    full_name = db.Column(
        db.String(150),
        nullable=False
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    phone = db.Column(
        db.String(30)
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    transaction_pin = db.Column(
        db.String(255)
    )

    role = db.Column(
        db.String(30),
        default="Agent",
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Active",
        nullable=False
    )

    wallet_balance = db.Column(
        db.Numeric(15, 2),
        default=0.00,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    transactions = db.relationship(
        "Transaction",
        backref="user",
        lazy=True
    )


class Transaction(db.Model):

    __tablename__ = "transactions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    transaction_reference = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    sender_name = db.Column(
        db.String(150)
    )

    receiver_name = db.Column(
        db.String(150)
    )

    account_number = db.Column(
        db.String(50)
    )

    bank_name = db.Column(
        db.String(100)
    )

    transaction_type = db.Column(
        db.String(50),
        nullable=False
    )

    amount = db.Column(
        db.Numeric(15, 2),
        nullable=False
    )

    description = db.Column(
        db.String(255)
    )

    status = db.Column(
        db.String(30),
        default="Success",
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )


class Receipt(db.Model):

    __tablename__ = "receipts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    receipt_number = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    transaction_reference = db.Column(
        db.String(100),
        nullable=False
    )

    customer = db.Column(
        db.String(150)
    )

    amount = db.Column(
        db.Numeric(15, 2),
        nullable=False
    )

    transaction_type = db.Column(
        db.String(50),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
