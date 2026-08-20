from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
from functools import wraps
import os
import secrets
import uuid
import csv
import io


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "pos-transaction-web-app-secret-key-2026"
)

# ------------------------------------------------------------
# Database configuration
# ------------------------------------------------------------

database_url = os.environ.get("DATABASE_URL")

if database_url:
    # Render/PostgreSQL compatibility
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # Local development database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pos_transaction.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# FLASK LOGIN CONFIGURATION
# ============================================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "warning"


# ============================================================
# DATABASE MODELS
# ============================================================

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(
        db.String(150),
        nullable=False
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(30),
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
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<User {self.username}>"


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    transaction_reference = db.Column(
        db.String(100),
        unique=True,
        nullable=False
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
        nullable=False,
        default=0.00
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.String(50),
        default="Success",
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Transaction {self.transaction_reference}>"


class Receipt(db.Model):
    __tablename__ = "receipts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

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
        nullable=True
    )

    amount = db.Column(
        db.Float,
        nullable=False,
        default=0.00
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


# ============================================================
# LOGIN USER LOADER
# ============================================================

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_reference():
    """
    Generate a unique transaction reference.
    Example:
    POS-20260819-A1B2C3D4
    """
    return (
        "POS-"
        + datetime.utcnow().strftime("%Y%m%d")
        + "-"
        + secrets.token_hex(4).upper()
    )


def generate_receipt():
    """
    Generate a unique receipt number.
    """
    return (
        "RCT-"
        + datetime.utcnow().strftime("%Y%m%d")
        + "-"
        + secrets.token_hex(4).upper()
    )


def get_amount(form_value):
    """
    Safely convert an amount from a form into a float.
    """
    try:
        amount = float(form_value)

        if amount <= 0:
            return None

        return round(amount, 2)

    except (TypeError, ValueError):
        return None


def verify_transaction_pin(pin):
    """
    Verify the logged-in user's transaction PIN.
    """
    if not current_user.transaction_pin:
        return False

    return check_password_hash(
        current_user.transaction_pin,
        pin
    )


def create_transaction(
    transaction_type,
    amount,
    sender_name=None,
    receiver_name=None,
    account_number=None,
    bank_name=None,
    description=None,
    status="Success",
):
    """
    Create a transaction record.
    """

    reference = generate_reference()

    transaction = Transaction(
        transaction_reference=reference,
        sender_name=sender_name,
        receiver_name=receiver_name,
        account_number=account_number,
        bank_name=bank_name,
        transaction_type=transaction_type,
        amount=amount,
        description=description,
        status=status,
        user_id=current_user.id if current_user.is_authenticated else None,
    )

    db.session.add(transaction)

    return transaction


def create_receipt(transaction):
    """
    Create a receipt for a transaction.
    """

    receipt = Receipt(
        receipt_number=generate_receipt(),
        transaction_reference=transaction.transaction_reference,
        customer=(
            transaction.receiver_name
            or transaction.sender_name
            or current_user.full_name
        ),
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
    )

    db.session.add(receipt)

    return receipt


def admin_required(function):
    """
    Restrict a route to administrators.
    """

    @wraps(function)
    @login_required
    def decorated_function(*args, **kwargs):

        if current_user.role.lower() != "admin":
            flash(
                "Administrator access is required.",
                "danger"
            )
            return redirect(url_for("dashboard"))

        return function(*args, **kwargs)

    return decorated_function


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

with app.app_context():
    db.create_all()


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    if current_user.is_authenticated:
        if current_user.role.lower() == "admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("index.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        if not full_name:
            flash(
                "Full name is required.",
                "danger"
            )
            return render_template("register.html")

        if not username:
            flash(
                "Username is required.",
                "danger"
            )
            return render_template("register.html")

        if not email:
            flash(
                "Email is required.",
                "danger"
            )
            return render_template("register.html")

        if not password:
            flash(
                "Password is required.",
                "danger"
            )
            return render_template("register.html")

        if password != confirm_password:
            flash(
                "Passwords do not match.",
                "danger"
            )
            return render_template("register.html")

        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:
            flash(
                "Username already exists.",
                "danger"
            )
            return render_template("register.html")

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:
            flash(
                "Email already exists.",
                "danger"
            )
            return render_template("register.html")

        hashed_password = generate_password_hash(
            password
        )

        hashed_pin = None

        if pin:
            hashed_pin = generate_password_hash(pin)

        # First registered user becomes Admin.
        if User.query.count() == 0:
            role = "Admin"
        else:
            role = "Agent"

        user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            password=hashed_password,
            transaction_pin=hashed_pin,
            role=role,
            status="Active",
            wallet_balance=0.00,
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "Registration successful. Please log in.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if not user:
            user = User.query.filter_by(
                email=username.lower()
            ).first()

        if not user:
            flash(
                "Invalid username/email or password.",
                "danger"
            )
            return render_template("login.html")

        if user.status.lower() != "active":
            flash(
                "Your account is not active.",
                "danger"
            )
            return render_template("login.html")

        if not check_password_hash(
            user.password,
            password
        ):
            flash(
                "Invalid username/email or password.",
                "danger"
            )
            return render_template("login.html")

        login_user(user)

        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role

        flash(
            "Login successful.",
            "success"
        )

        next_page = request.args.get("next")

        if next_page:
            return redirect(next_page)

        if user.role.lower() == "admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("login"))


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    transactions = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    total_transactions = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .count()
    )

    return render_template(
        "dashboard.html",
        transactions=transactions,
        total_transactions=total_transactions,
        balance=current_user.wallet_balance,
    )


# ============================================================
# WALLET
# ============================================================

@app.route("/wallet")
@login_required
def wallet():

    transactions = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )

    return render_template(
        "wallet.html",
        balance=current_user.wallet_balance,
        transactions=transactions,
    )


# ============================================================
# BALANCE
# ============================================================

@app.route("/balance")
@login_required
def balance():

    transactions = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )

    return render_template(
        "balance.html",
        balance=current_user.wallet_balance,
        transactions=transactions,
    )


# ============================================================
# DEPOSIT
# ============================================================

@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():

    if request.method == "POST":

        amount = get_amount(
            request.form.get("amount")
        )

        description = request.form.get(
            "description",
            "Wallet deposit"
        ).strip()

        if amount is None:
            flash(
                "Enter a valid amount.",
                "danger"
            )
            return render_template("deposit.html")

        current_user.wallet_balance += amount

        transaction = create_transaction(
            transaction_type="Deposit",
            amount=amount,
            receiver_name=current_user.full_name,
            description=description,
        )

        create_receipt(transaction)

        db.session.commit()

        flash(
            f"Deposit of ?{amount:,.2f} successful.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=transaction.transaction_reference
            )
        )

    return render_template(
        "deposit.html",
        balance=current_user.wallet_balance
    )


# ============================================================
# CASH WITHDRAWAL
# ============================================================

@app.route(
    "/cash-withdrawal",
    methods=["GET", "POST"]
)
@login_required
def cash_withdrawal():

    if request.method == "POST":

        amount = get_amount(
            request.form.get("amount")
        )

        pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        description = request.form.get(
            "description",
            "Cash withdrawal"
        ).strip()

        if amount is None:
            flash(
                "Enter a valid amount.",
                "danger"
            )
            return render_template("cash-withdrawal.html")

        if amount > current_user.wallet_balance:
            flash(
                "Insufficient wallet balance.",
                "danger"
            )
            return render_template(
                "cash-withdrawal.html",
                balance=current_user.wallet_balance
            )

        if not current_user.transaction_pin:
            flash(
                "Please set your transaction PIN first.",
                "danger"
            )
            return redirect(
                url_for("change_pin")
            )

        if not verify_transaction_pin(pin):
            flash(
                "Invalid transaction PIN.",
                "danger"
            )
            return render_template(
                "cash-withdrawal.html",
                balance=current_user.wallet_balance
            )

        current_user.wallet_balance -= amount

        transaction = create_transaction(
            transaction_type="Cash Withdrawal",
            amount=amount,
            sender_name=current_user.full_name,
            description=description,
        )

        create_receipt(transaction)

        db.session.commit()

        flash(
            f"Withdrawal of ?{amount:,.2f} successful.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=transaction.transaction_reference
            )
        )

    return render_template(
        "cash-withdrawal.html",
        balance=current_user.wallet_balance
    )


# ============================================================
# SEND MONEY
# ============================================================

@app.route(
    "/sending-money",
    methods=["GET", "POST"]
)
@login_required
def send_money():

    if request.method == "POST":

        receiver_name = request.form.get(
            "receiver_name",
            ""
        ).strip()

        account_number = request.form.get(
            "account_number",
            ""
        ).strip()

        bank_name = request.form.get(
            "bank_name",
            ""
        ).strip()

        amount = get_amount(
            request.form.get("amount")
        )

        pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        description = request.form.get(
            "description",
            "Money transfer"
        ).strip()

        if not receiver_name:
            flash(
                "Receiver name is required.",
                "danger"
            )
            return render_template("sending-money.html")

        if amount is None:
            flash(
                "Enter a valid amount.",
                "danger"
            )
            return render_template("sending-money.html")

        if amount > current_user.wallet_balance:
            flash(
                "Insufficient wallet balance.",
                "danger"
            )
            return render_template(
                "sending-money.html",
                balance=current_user.wallet_balance
            )

        if not current_user.transaction_pin:
            flash(
                "Please set your transaction PIN first.",
                "danger"
            )
            return redirect(
                url_for("change_pin")
            )

        if not verify_transaction_pin(pin):
            flash(
                "Invalid transaction PIN.",
                "danger"
            )
            return render_template(
                "sending-money.html",
                balance=current_user.wallet_balance
            )

        current_user.wallet_balance -= amount

        transaction = create_transaction(
            transaction_type="Send Money",
            amount=amount,
            sender_name=current_user.full_name,
            receiver_name=receiver_name,
            account_number=account_number,
            bank_name=bank_name,
            description=description,
        )

        create_receipt(transaction)

        db.session.commit()

        flash(
            f"?{amount:,.2f} sent successfully.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=transaction.transaction_reference
            )
        )

    return render_template(
        "sending-money.html",
        balance=current_user.wallet_balance
    )


# ============================================================
# RECEIVE MONEY
# ============================================================

@app.route(
    "/receiving-money",
    methods=["GET", "POST"]
)
@login_required
def receive_money():

    if request.method == "POST":

        sender_name = request.form.get(
            "sender_name",
            ""
        ).strip()

        account_number = request.form.get(
            "account_number",
            ""
        ).strip()

        amount = get_amount(
            request.form.get("amount")
        )

        description = request.form.get(
            "description",
            "Money received"
        ).strip()

        if not sender_name:
            flash(
                "Sender name is required.",
                "danger"
            )
            return render_template(
                "receiving-money.html"
            )

        if amount is None:
            flash(
                "Enter a valid amount.",
                "danger"
            )
            return render_template(
                "receiving-money.html"
            )

        current_user.wallet_balance += amount

        transaction = create_transaction(
            transaction_type="Receive Money",
            amount=amount,
            sender_name=sender_name,
            receiver_name=current_user.full_name,
            account_number=account_number,
            description=description,
        )

        create_receipt(transaction)

        db.session.commit()

        flash(
            f"?{amount:,.2f} received successfully.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=transaction.transaction_reference
            )
        )

    return render_template(
        "receiving-money.html",
        balance=current_user.wallet_balance
    )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.route("/transactions")
@login_required
def transaction_history():

    transactions = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    return render_template(
        "transactions.html",
        transactions=transactions
    )


# ============================================================
# TRANSFER SUCCESS HISTORY
# ============================================================

@app.route("/transfer-success-history")
@login_required
def transfer_success_history():

    transactions = (
        Transaction.query
        .filter_by(
            user_id=current_user.id,
            status="Success"
        )
        .filter(
            Transaction.transaction_type.in_(
                [
                    "Send Money",
                    "Receive Money"
                ]
            )
        )
        .order_by(Transaction.created_at.desc())
        .all()
    )

    return render_template(
        "transfer-success-history.html",
        transactions=transactions
    )


# ============================================================
# PROFILE
# ============================================================

@app.route(
    "/profile",
    methods=["GET", "POST"]
)
@login_required
def profile():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        if not full_name or not email:
            flash(
                "Full name and email are required.",
                "danger"
            )
            return render_template(
                "profile.html"
            )

        existing_email = (
            User.query
            .filter(
                User.email == email,
                User.id != current_user.id
            )
            .first()
        )

        if existing_email:
            flash(
                "That email address is already in use.",
                "danger"
            )
            return render_template(
                "profile.html"
            )

        current_user.full_name = full_name
        current_user.phone = phone
        current_user.email = email

        db.session.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(
            url_for("profile")
        )

    return render_template(
        "profile.html",
        user=current_user
    )


# ============================================================
# SETTINGS
# ============================================================

@app.route("/settings")
@login_required
def settings():

    return render_template(
        "settings.html",
        user=current_user
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

@app.route(
    "/change-password",
    methods=["GET", "POST"]
)
@login_required
def change_password():

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not check_password_hash(
            current_user.password,
            current_password
        ):
            flash(
                "Current password is incorrect.",
                "danger"
            )
            return render_template(
                "change-password.html"
            )

        if not new_password:
            flash(
                "Enter a new password.",
                "danger"
            )
            return render_template(
                "change-password.html"
            )

        if new_password != confirm_password:
            flash(
                "New passwords do not match.",
                "danger"
            )
            return render_template(
                "change-password.html"
            )

        current_user.password = generate_password_hash(
            new_password
        )

        db.session.commit()

        flash(
            "Password changed successfully.",
            "success"
        )

        return redirect(
            url_for("settings")
        )

    return render_template(
        "change-password.html"
    )


# ============================================================
# CHANGE TRANSACTION PIN
# ============================================================

@app.route(
    "/change-pin",
    methods=["GET", "POST"]
)
@login_required
def change_pin():

    if request.method == "POST":

        new_pin = request.form.get(
            "new_pin",
            ""
        ).strip()

        confirm_pin = request.form.get(
            "confirm_pin",
            ""
        ).strip()

        if not new_pin:
            flash(
                "Enter a transaction PIN.",
                "danger"
            )
            return render_template(
                "change-pin.html"
            )

        if not new_pin.isdigit():
            flash(
                "Transaction PIN must contain numbers only.",
                "danger"
            )
            return render_template(
                "change-pin.html"
            )

        if len(new_pin) != 4:
            flash(
                "Transaction PIN must contain exactly 4 digits.",
                "danger"
            )
            return render_template(
                "change-pin.html"
            )

        if new_pin != confirm_pin:
            flash(
                "Transaction PINs do not match.",
                "danger"
            )
            return render_template(
                "change-pin.html"
            )

        current_user.transaction_pin = generate_password_hash(
            new_pin
        )

        db.session.commit()

        flash(
            "Transaction PIN changed successfully.",
            "success"
        )

        return redirect(
            url_for("settings")
        )

    return render_template(
        "change-pin.html"
    )


# ============================================================
# RECEIPT
# ============================================================

@app.route("/receipt/<reference>")
@login_required
def receipt(reference):

    transaction = Transaction.query.filter_by(
        transaction_reference=reference
    ).first_or_404()

    if (
        transaction.user_id != current_user.id
        and current_user.role.lower() != "admin"
    ):
        flash(
            "You are not authorized to view this receipt.",
            "danger"
        )
        return redirect(
            url_for("dashboard")
        )

    receipt_record = Receipt.query.filter_by(
        transaction_reference=reference
    ).first()

    return render_template(
        "receipt.html",
        transaction=transaction,
        receipt=receipt_record
    )


# ============================================================
# PRINT RECEIPT
# ============================================================

@app.route("/print-receipt/<reference>")
@login_required
def print_receipt(reference):

    transaction = Transaction.query.filter_by(
        transaction_reference=reference
    ).first_or_404()

    if (
        transaction.user_id != current_user.id
        and current_user.role.lower() != "admin"
    ):
        flash(
            "You are not authorized to print this receipt.",
            "danger"
        )
        return redirect(
            url_for("dashboard")
        )

    receipt_record = Receipt.query.filter_by(
        transaction_reference=reference
    ).first()

    return render_template(
        "print_receipt.html",
        transaction=transaction,
        receipt=receipt_record
    )


# ============================================================
# SEARCH TRANSACTIONS
# ============================================================

@app.route("/search-transactions")
@login_required
def search_transactions():

    query = request.args.get(
        "q",
        ""
    ).strip()

    transactions_query = Transaction.query.filter_by(
        user_id=current_user.id
    )

    if query:

        transactions_query = transactions_query.filter(
            db.or_(
                Transaction.transaction_reference.ilike(
                    f"%{query}%"
                ),
                Transaction.sender_name.ilike(
                    f"%{query}%"
                ),
                Transaction.receiver_name.ilike(
                    f"%{query}%"
                ),
                Transaction.account_number.ilike(
                    f"%{query}%"
                ),
                Transaction.transaction_type.ilike(
                    f"%{query}%"
                )
            )
        )

    transactions = (
        transactions_query
        .order_by(Transaction.created_at.desc())
        .all()
    )

    return render_template(
        "transactions.html",
        transactions=transactions,
        search_query=query
    )


# ============================================================
# REPORTS
# ============================================================

@app.route("/reports")
@login_required
def reports():

    transactions = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    total_amount = sum(
        transaction.amount
        for transaction in transactions
        if transaction.status == "Success"
    )

    total_transactions = len(transactions)

    return render_template(
        "reports.html",
        transactions=transactions,
        total_amount=total_amount,
        total_transactions=total_transactions
    )


# ============================================================
# DAILY REPORT
# ============================================================

@app.route("/daily-report")
@login_required
def daily_report():

    today = datetime.utcnow().date()

    transactions = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    daily_transactions = [
        transaction
        for transaction in transactions
        if transaction.created_at.date() == today
    ]

    total_amount = sum(
        transaction.amount
        for transaction in daily_transactions
        if transaction.status == "Success"
    )

    return render_template(
        "daily-report.html",
        transactions=daily_transactions,
        total_amount=total_amount,
        date=today
    )


# ============================================================
# EXPORT REPORT
# ============================================================

@app.route("/export-report")
@login_required
def export_report():

    transactions = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        [
            "Transaction Reference",
            "Type",
            "Sender",
            "Receiver",
            "Account Number",
            "Bank",
            "Amount",
            "Status",
            "Description",
            "Date",
        ]
    )

    for transaction in transactions:

        writer.writerow(
            [
                transaction.transaction_reference,
                transaction.transaction_type,
                transaction.sender_name or "",
                transaction.receiver_name or "",
                transaction.account_number or "",
                transaction.bank_name or "",
                f"{transaction.amount:.2f}",
                transaction.status,
                transaction.description or "",
                transaction.created_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            ]
        )

    output.seek(0)

    return send_file(
        io.BytesIO(
            output.getvalue().encode("utf-8")
        ),
        mimetype="text/csv",
        as_attachment=True,
        download_name="pos_transaction_report.csv"
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    users = (
        User.query
        .order_by(User.created_at.desc())
        .all()
    )

    transactions = (
        Transaction.query
        .order_by(Transaction.created_at.desc())
        .limit(50)
        .all()
    )

    total_users = User.query.count()

    total_transactions = Transaction.query.count()

    total_transaction_amount = (
        db.session.query(
            db.func.sum(Transaction.amount)
        )
        .filter(
            Transaction.status == "Success"
        )
        .scalar()
        or 0
    )

    return render_template(
        "admin.html",
        users=users,
        transactions=transactions,
        total_users=total_users,
        total_transactions=total_transactions,
        total_transaction_amount=total_transaction_amount,
    )


# ============================================================
# ADMIN USER STATUS
# ============================================================

@app.route(
    "/admin/user/<int:user_id>/status",
    methods=["POST"]
)
@admin_required
def admin_user_status(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if not user:
        flash(
            "User not found.",
            "danger"
        )
        return redirect(
            url_for("admin_dashboard")
        )

    if user.id == current_user.id:
        flash(
            "You cannot deactivate your own account.",
            "warning"
        )
        return redirect(
            url_for("admin_dashboard")
        )

    if user.status.lower() == "active":
        user.status = "Inactive"
    else:
        user.status = "Active"

    db.session.commit()

    flash(
        f"User status changed to {user.status}.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# ADMIN DELETE USER
# ============================================================

@app.route(
    "/admin/user/<int:user_id>/delete",
    methods=["POST"]
)
@admin_required
def admin_delete_user(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if not user:
        flash(
            "User not found.",
            "danger"
        )
        return redirect(
            url_for("admin_dashboard")
        )

    if user.id == current_user.id:
        flash(
            "You cannot delete your own account.",
            "danger"
        )
        return redirect(
            url_for("admin_dashboard")
        )

    # Keep transactions but remove user relationship.
    Transaction.query.filter_by(
        user_id=user.id
    ).update(
        {
            "user_id": None
        }
    )

    db.session.delete(user)

    db.session.commit()

    flash(
        "User deleted successfully.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# COMPATIBILITY ROUTES
# ============================================================
#
# These aliases help prevent BuildError if one of your existing
# HTML files uses a slightly different endpoint URL.
# ============================================================

@app.route("/withdrawal", methods=["GET", "POST"])
@login_required
def withdrawal():

    return cash_withdrawal()


@app.route("/send-money", methods=["GET", "POST"])
@login_required
def send_money_alias():

    return send_money()


@app.route("/receive-money", methods=["GET", "POST"])
@login_required
def receive_money_alias():

    return receive_money()


@app.route("/receiving-money", methods=["GET", "POST"])
@login_required
def receiving_money():

    return receive_money()


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    try:
        return render_template(
            "404.html"
        ), 404

    except Exception:
        return (
            """
            <h1>404 - Page Not Found</h1>
            <p>The page you requested does not exist.</p>
            """,
            404
        )


@app.errorhandler(500)
def internal_server_error(error):

    db.session.rollback()

    try:
        return render_template(
            "500.html"
        ), 500

    except Exception:
        return (
            """
            <h1>500 - Internal Server Error</h1>
            <p>An unexpected error occurred.</p>
            """,
            500
        )


# ============================================================
# CONTEXT PROCESSOR
# ============================================================

@app.context_processor
def inject_app_information():

    return {
        "app_name": "POS Transaction Web App",
        "current_year": datetime.utcnow().year,
    }


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )
