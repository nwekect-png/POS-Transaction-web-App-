from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from datetime import datetime
from functools import wraps

import os
import secrets
import string
import csv
import io


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32)
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

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

    # Local SQLite database
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///pos_transaction.db"
    )


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# LOGIN MANAGER
# ============================================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message = (
    "Please login to continue."
)

login_manager.login_message_category = "warning"


# ============================================================
# USER MODEL
# ============================================================

class User(UserMixin, db.Model):

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
        db.String(100),
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


# ============================================================
# LOGIN USER LOADER
# ============================================================

@login_manager.user_loader
def load_user(user_id):

    try:
        return db.session.get(
            User,
            int(user_id)
        )

    except (ValueError, TypeError):

        return None


# ============================================================
# ADMIN DECORATOR
# ============================================================

def admin_required(view_function):

    @wraps(view_function)
    @login_required
    def wrapped_view(*args, **kwargs):

        if current_user.role != "Admin":

            flash(
                "Administrator access required.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view


# ============================================================
# HELPER - GENERATE TRANSACTION REFERENCE
# ============================================================

def generate_reference():

    timestamp = datetime.utcnow().strftime(
        "%Y%m%d%H%M%S"
    )

    random_part = "".join(
        secrets.choice(
            string.ascii_uppercase +
            string.digits
        )
        for _ in range(6)
    )

    return (
        f"TXN-{timestamp}-{random_part}"
    )


# ============================================================
# HELPER - GENERATE RECEIPT NUMBER
# ============================================================

def generate_receipt():

    timestamp = datetime.utcnow().strftime(
        "%Y%m%d%H%M%S"
    )

    random_part = "".join(
        secrets.choice(
            string.digits
        )
        for _ in range(5)
    )

    return (
        f"RCP-{timestamp}-{random_part}"
    )


# ============================================================
# HELPER - CREATE TRANSACTION
# ============================================================

def create_transaction(
    transaction_type,
    amount,
    sender_name=None,
    receiver_name=None,
    account_number=None,
    bank_name=None,
    description=None
):

    transaction = Transaction(
        transaction_reference=generate_reference(),
        sender_name=sender_name,
        receiver_name=receiver_name,
        account_number=account_number,
        bank_name=bank_name,
        transaction_type=transaction_type,
        amount=amount,
        description=description,
        status="Success",
        user_id=current_user.id
    )

    db.session.add(transaction)

    return transaction


# ============================================================
# HELPER - CREATE RECEIPT
# ============================================================

def create_receipt(
    transaction,
    customer=None
):

    receipt = Receipt(
        receipt_number=generate_receipt(),
        transaction_reference=(
            transaction.transaction_reference
        ),
        customer=customer,
        amount=transaction.amount,
        transaction_type=(
            transaction.transaction_type
        )
    )

    db.session.add(receipt)

    return receipt


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    if current_user.is_authenticated:

        if current_user.role == "Admin":

            return redirect(
                url_for("admin_dashboard")
            )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "index.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )

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
        ).strip()

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

        transaction_pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not full_name:

            flash(
                "Full name is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if not username:

            flash(
                "Username is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if not email:

            flash(
                "Email is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if not password:

            flash(
                "Password is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        # ----------------------------------------------------
        # CHECK USERNAME
        # ----------------------------------------------------

        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:

            flash(
                "Username already exists.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        # ----------------------------------------------------
        # CHECK EMAIL
        # ----------------------------------------------------

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:

            flash(
                "Email already exists.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        # ----------------------------------------------------
        # HASH PASSWORD
        # ----------------------------------------------------

        hashed_password = (
            generate_password_hash(password)
        )

        hashed_pin = None

        if transaction_pin:

            if (
                not transaction_pin.isdigit()
                or len(transaction_pin) != 4
            ):

                flash(
                    "Transaction PIN must contain exactly 4 digits.",
                    "danger"
                )

                return render_template(
                    "register.html"
                )

            hashed_pin = (
                generate_password_hash(
                    transaction_pin
                )
            )

        # ----------------------------------------------------
        # CREATE USER
        # ----------------------------------------------------

        user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            password=hashed_password,
            transaction_pin=hashed_pin,
            role="Agent",
            status="Active",
            wallet_balance=0.00
        )

        db.session.add(user)

        db.session.commit()

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        if current_user.role == "Admin":

            return redirect(
                url_for("admin_dashboard")
            )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:

            flash(
                "Username and password are required.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        user = User.query.filter_by(
            username=username
        ).first()

        if not user:

            flash(
                "Invalid username or password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        if user.status != "Active":

            flash(
                "Your account is not active.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        if not check_password_hash(
            user.password,
            password
        ):

            flash(
                "Invalid username or password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        login_user(user)

        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role

        flash(
            f"Welcome back, {user.full_name}!",
            "success"
        )

        if user.role == "Admin":

            return redirect(
                url_for("admin_dashboard")
            )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "login.html"
    )


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

    return redirect(
        url_for("login")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    balance = (
        current_user.wallet_balance or 0.00
    )

    transactions = (
        Transaction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .limit(10)
        .all()
    )

    total_transactions = (
        Transaction.query
        .filter_by(
            user_id=current_user.id
        )
        .count()
    )

    total_deposits = (
        db.session.query(
            db.func.sum(
                Transaction.amount
            )
        )
        .filter_by(
            user_id=current_user.id,
            transaction_type="Deposit",
            status="Success"
        )
        .scalar()
        or 0
    )

    total_withdrawals = (
        db.session.query(
            db.func.sum(
                Transaction.amount
            )
        )
        .filter_by(
            user_id=current_user.id,
            transaction_type="Withdrawal",
            status="Success"
        )
        .scalar()
        or 0
    )

    total_sent = (
        db.session.query(
            db.func.sum(
                Transaction.amount
            )
        )
        .filter_by(
            user_id=current_user.id,
            transaction_type="Send Money",
            status="Success"
        )
        .scalar()
        or 0
    )

    total_received = (
        db.session.query(
            db.func.sum(
                Transaction.amount
            )
        )
        .filter_by(
            user_id=current_user.id,
            transaction_type="Receive Money",
            status="Success"
        )
        .scalar()
        or 0
    )

    return render_template(
        "dashboard.html",
        balance=balance,
        wallet_balance=balance,
        user=current_user,
        transactions=transactions,
        total_transactions=total_transactions,
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals,
        total_sent=total_sent,
        total_received=total_received
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    users = (
        User.query
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    transactions = (
        Transaction.query
        .order_by(
            Transaction.created_at.desc()
        )
        .limit(20)
        .all()
    )

    total_users = User.query.count()

    total_transactions = (
        Transaction.query.count()
    )

    total_money = (
        db.session.query(
            db.func.sum(
                Transaction.amount
            )
        )
        .filter_by(
            status="Success"
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
        total_money=total_money
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

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        if not full_name or not email:

            flash(
                "Name and email are required.",
                "danger"
            )

            return redirect(
                url_for("profile")
            )

        email_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if email_user:

            flash(
                "Email is already being used.",
                "danger"
            )

            return redirect(
                url_for("profile")
            )

        current_user.full_name = full_name
        current_user.email = email
        current_user.phone = phone

        db.session.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(
            url_for("profile")
        )

    return render_template(
        "profile.html"
    )


# ============================================================
# SETTINGS
# ============================================================

@app.route("/settings")
@login_required
def settings():

    return render_template(
        "settings.html"
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

            return redirect(
                url_for("change_password")
            )

        if not new_password:

            flash(
                "New password is required.",
                "danger"
            )

            return redirect(
                url_for("change_password")
            )

        if new_password != confirm_password:

            flash(
                "New passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("change_password")
            )

        current_user.password = (
            generate_password_hash(
                new_password
            )
        )

        db.session.commit()

        flash(
            "Password changed successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "change_password.html"
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        user = None

        if username:

            user = User.query.filter_by(
                username=username
            ).first()

        if not user and email:

            user = User.query.filter_by(
                email=email
            ).first()

        if not user:

            flash(
                "No account was found with those details.",
                "danger"
            )

            return render_template(
                "forgot_password.html"
            )

        session["reset_user_id"] = user.id

        return redirect(
            url_for("reset_password")
        )

    return render_template(
        "forgot_password.html"
    )


# ============================================================
# RESET PASSWORD
# ============================================================

@app.route(
    "/reset-password",
    methods=["GET", "POST"]
)
def reset_password():

    user_id = session.get(
        "reset_user_id"
    )

    if not user_id:

        flash(
            "Password reset session expired.",
            "danger"
        )

        return redirect(
            url_for("forgot_password")
        )

    user = db.session.get(
        User,
        user_id
    )

    if not user:

        session.pop(
            "reset_user_id",
            None
        )

        flash(
            "User not found.",
            "danger"
        )

        return redirect(
            url_for("forgot_password")
        )

    if request.method == "POST":

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not new_password:

            flash(
                "Enter a new password.",
                "danger"
            )

            return render_template(
                "reset_password.html"
            )

        if new_password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "reset_password.html"
            )

        user.password = (
            generate_password_hash(
                new_password
            )
        )

        db.session.commit()

        session.pop(
            "reset_user_id",
            None
        )

        flash(
            "Password reset successfully. Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "reset_password.html"
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

        current_pin = request.form.get(
            "current_pin",
            ""
        ).strip()

        new_pin = request.form.get(
            "new_pin",
            ""
        ).strip()

        confirm_pin = request.form.get(
            "confirm_pin",
            ""
        ).strip()

        if current_user.transaction_pin:

            if not check_password_hash(
                current_user.transaction_pin,
                current_pin
            ):

                flash(
                    "Current transaction PIN is incorrect.",
                    "danger"
                )

                return redirect(
                    url_for("change_pin")
                )

        if (
            not new_pin.isdigit()
            or len(new_pin) != 4
        ):

            flash(
                "Transaction PIN must contain exactly 4 digits.",
                "danger"
            )

            return redirect(
                url_for("change_pin")
            )

        if new_pin != confirm_pin:

            flash(
                "PINs do not match.",
                "danger"
            )

            return redirect(
                url_for("change_pin")
            )

        current_user.transaction_pin = (
            generate_password_hash(
                new_pin
            )
        )

        db.session.commit()

        flash(
            "Transaction PIN changed successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "change_pin.html"
    )


# ============================================================
# WALLET
# ============================================================

@app.route("/wallet")
@login_required
def wallet():

    balance = (
        current_user.wallet_balance or 0.00
    )

    return render_template(
        "balance.html",
        balance=balance,
        wallet_balance=balance
    )


# ============================================================
# BALANCE
# ============================================================

@app.route("/balance")
@login_required
def balance():

    current_balance = (
        current_user.wallet_balance or 0.00
    )

    return render_template(
        "balance.html",
        balance=current_balance,
        wallet_balance=current_balance
    )


# ============================================================
# DEPOSIT
# ============================================================

@app.route(
    "/deposit",
    methods=["GET", "POST"]
)
@login_required
def deposit():

    if request.method == "POST":

        try:

            amount = float(
                request.form.get(
                    "amount",
                    0
                )
            )

        except (ValueError, TypeError):

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return redirect(
                url_for("deposit")
            )

        if amount <= 0:

            flash(
                "Amount must be greater than zero.",
                "danger"
            )

            return redirect(
                url_for("deposit")
            )

        description = request.form.get(
            "description",
            "Wallet deposit"
        ).strip()

        if current_user.wallet_balance is None:

            current_user.wallet_balance = 0.00

        current_user.wallet_balance += amount

        transaction = create_transaction(
            transaction_type="Deposit",
            amount=amount,
            receiver_name=current_user.full_name,
            description=description
        )

        create_receipt(
            transaction,
            current_user.full_name
        )

        db.session.commit()

        flash(
            f"Deposit of ₦{amount:,.2f} successful.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=(
                    transaction.transaction_reference
                )
            )
        )

    return render_template(
        "deposit.html"
    )


# ============================================================
# WITHDRAWAL
# ============================================================

@app.route(
    "/withdrawal",
    methods=["GET", "POST"]
)
@app.route(
    "/withdraw",
    methods=["GET", "POST"]
)
@login_required
def withdrawal():

    if request.method == "POST":

        try:

            amount = float(
                request.form.get(
                    "amount",
                    0
                )
            )

        except (ValueError, TypeError):

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return redirect(
                url_for("withdrawal")
            )

        if amount <= 0:

            flash(
                "Amount must be greater than zero.",
                "danger"
            )

            return redirect(
                url_for("withdrawal")
            )

        wallet_balance = (
            current_user.wallet_balance or 0.00
        )

        if amount > wallet_balance:

            flash(
                "Insufficient wallet balance.",
                "danger"
            )

            return redirect(
                url_for("withdrawal")
            )

        pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        if current_user.transaction_pin:

            if not check_password_hash(
                current_user.transaction_pin,
                pin
            ):

                flash(
                    "Invalid transaction PIN.",
                    "danger"
                )

                return redirect(
                    url_for("withdrawal")
                )

        current_user.wallet_balance = (
            wallet_balance - amount
        )

        transaction = create_transaction(
            transaction_type="Withdrawal",
            amount=amount,
            sender_name=current_user.full_name,
            description="Wallet withdrawal"
        )

        create_receipt(
            transaction,
            current_user.full_name
        )

        db.session.commit()

        flash(
            f"Withdrawal of ₦{amount:,.2f} successful.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=(
                    transaction.transaction_reference
                )
            )
        )

    return render_template(
        "cash-withdrawal.html"
    )


# ============================================================
# SEND MONEY
# ============================================================

@app.route(
    "/send-money",
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

        description = request.form.get(
            "description",
            ""
        ).strip()

        try:

            amount = float(
                request.form.get(
                    "amount",
                    0
                )
            )

        except (ValueError, TypeError):

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return redirect(
                url_for("send_money")
            )

        pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        if amount <= 0:

            flash(
                "Amount must be greater than zero.",
                "danger"
            )

            return redirect(
                url_for("send_money")
            )

        wallet_balance = (
            current_user.wallet_balance or 0.00
        )

        if amount > wallet_balance:

            flash(
                "Insufficient wallet balance.",
                "danger"
            )

            return redirect(
                url_for("send_money")
            )

        if current_user.transaction_pin:

            if not check_password_hash(
                current_user.transaction_pin,
                pin
            ):

                flash(
                    "Invalid transaction PIN.",
                    "danger"
                )

                return redirect(
                    url_for("send_money")
                )

        current_user.wallet_balance = (
            wallet_balance - amount
        )

        transaction = create_transaction(
            transaction_type="Send Money",
            amount=amount,
            sender_name=current_user.full_name,
            receiver_name=receiver_name,
            account_number=account_number,
            bank_name=bank_name,
            description=description
        )

        create_receipt(
            transaction,
            current_user.full_name
        )

        db.session.commit()

        flash(
            f"₦{amount:,.2f} sent successfully.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=(
                    transaction.transaction_reference
                )
            )
        )

    return render_template(
        "sending-money.html"
    )


# ============================================================
# RECEIVE MONEY
# ============================================================

@app.route(
    "/receive-money",
    methods=["GET", "POST"]
)
@login_required
def receive_money():

    if request.method == "POST":

        sender_name = request.form.get(
            "sender_name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        try:

            amount = float(
                request.form.get(
                    "amount",
                    0
                )
            )

        except (ValueError, TypeError):

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return redirect(
                url_for("receive_money")
            )

        if amount <= 0:

            flash(
                "Amount must be greater than zero.",
                "danger"
            )

            return redirect(
                url_for("receive_money")
            )

        wallet_balance = (
            current_user.wallet_balance or 0.00
        )

        current_user.wallet_balance = (
            wallet_balance + amount
        )

        transaction = create_transaction(
            transaction_type="Receive Money",
            amount=amount,
            sender_name=sender_name,
            receiver_name=current_user.full_name,
            description=description
        )

        create_receipt(
            transaction,
            current_user.full_name
        )

        db.session.commit()

        flash(
            f"₦{amount:,.2f} received successfully.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=(
                    transaction.transaction_reference
                )
            )
        )

    return render_template(
        "receiving-money.html"
    )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.route("/transactions")
@login_required
def transaction_history():

    transactions = (
        Transaction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .all()
    )

    return render_template(
        "transactions.html",
        transactions=transactions
    )


# ============================================================
# TRANSFER SUCCESS HISTORY
# ============================================================

@app.route(
    "/transfer-success-history"
)
@login_required
def transfer_success_history():

    transactions = (
        Transaction.query
        .filter_by(
            user_id=current_user.id,
            status="Success"
        )
        .filter(
            Transaction.transaction_type.in_([
                "Send Money",
                "Receive Money"
            ])
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .all()
    )

    return render_template(
        "transactions.html",
        transactions=transactions
    )


# ============================================================
# REPORTS
# ============================================================

@app.route("/reports")
@login_required
def reports():

    transactions = (
        Transaction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .all()
    )

    total = sum(
        transaction.amount
        for transaction in transactions
        if transaction.status == "Success"
    )

    return render_template(
        "reports.html",
        transactions=transactions,
        total=total
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
        .filter(
            Transaction.user_id == current_user.id,
            db.func.date(
                Transaction.created_at
            ) == today
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .all()
    )

    total = sum(
        transaction.amount
        for transaction in transactions
        if transaction.status == "Success"
    )

    return render_template(
        "reports.html",
        transactions=transactions,
        total=total,
        report_date=today
    )


# ============================================================
# SEARCH TRANSACTIONS
# ============================================================

@app.route(
    "/search-transactions"
)
@login_required
def search_transactions():

    search = request.args.get(
        "q",
        ""
    ).strip()

    query = Transaction.query.filter_by(
        user_id=current_user.id
    )

    if search:

        query = query.filter(
            db.or_(
                Transaction.transaction_reference.ilike(
                    f"%{search}%"
                ),
                Transaction.sender_name.ilike(
                    f"%{search}%"
                ),
                Transaction.receiver_name.ilike(
                    f"%{search}%"
                ),
                Transaction.account_number.ilike(
                    f"%{search}%"
                ),
                Transaction.bank_name.ilike(
                    f"%{search}%"
                )
            )
        )

    transactions = (
        query
        .order_by(
            Transaction.created_at.desc()
        )
        .all()
    )

    return render_template(
        "transactions.html",
        transactions=transactions,
        search=search
    )


# ============================================================
# RECEIPT
# ============================================================

@app.route("/receipt")
@login_required
def receipt():

    reference = request.args.get(
        "reference"
    )

    if not reference:

        flash(
            "Transaction reference is required.",
            "danger"
        )

        return redirect(
            url_for("transaction_history")
        )

    transaction = (
        Transaction.query
        .filter_by(
            transaction_reference=reference,
            user_id=current_user.id
        )
        .first()
    )

    if not transaction:

        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transaction_history")
        )

    receipt_record = (
        Receipt.query
        .filter_by(
            transaction_reference=reference
        )
        .first()
    )

    return render_template(
        "receipt.html",
        transaction=transaction,
        receipt=receipt_record
    )


# ============================================================
# PRINT RECEIPT
# ============================================================

@app.route(
    "/print-receipt/<reference>"
)
@login_required
def print_receipt(reference):

    transaction = (
        Transaction.query
        .filter_by(
            transaction_reference=reference,
            user_id=current_user.id
        )
        .first()
    )

    if not transaction:

        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transaction_history")
        )

    receipt_record = (
        Receipt.query
        .filter_by(
            transaction_reference=reference
        )
        .first()
    )

    return render_template(
        "receipt.html",
        transaction=transaction,
        receipt=receipt_record,
        print_mode=True
    )


# ============================================================
# EXPORT REPORT
# ============================================================

@app.route("/export-report")
@login_required
def export_report():

    transactions = (
        Transaction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .all()
    )

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Reference",
        "Type",
        "Amount",
        "Sender",
        "Receiver",
        "Account Number",
        "Bank",
        "Status",
        "Date"
    ])

    for transaction in transactions:

        writer.writerow([
            transaction.transaction_reference,
            transaction.transaction_type,
            transaction.amount,
            transaction.sender_name or "",
            transaction.receiver_name or "",
            transaction.account_number or "",
            transaction.bank_name or "",
            transaction.status,
            transaction.created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ])

    output.seek(0)

    return send_file(
        io.BytesIO(
            output.getvalue().encode(
                "utf-8"
            )
        ),
        mimetype="text/csv",
        as_attachment=True,
        download_name="transaction_report.csv"
    )


# ============================================================
# ADMIN - USERS
# ============================================================

@app.route("/admin/users")
@admin_required
def admin_users():

    users = (
        User.query
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    return render_template(
        "admin.html",
        users=users
    )


# ============================================================
# ADMIN - TRANSACTIONS
# ============================================================

@app.route("/admin/transactions")
@admin_required
def admin_transactions():

    transactions = (
        Transaction.query
        .order_by(
            Transaction.created_at.desc()
        )
        .all()
    )

    return render_template(
        "transactions.html",
        transactions=transactions
    )


# ============================================================
# ERROR HANDLER - 404
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


# ============================================================
# ERROR HANDLER - 500
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    db.session.rollback()

    return render_template(
        "500.html"
    ), 500


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

with app.app_context():

    db.create_all()


# ============================================================
# DEVELOPMENT SERVER
# ============================================================

if __name__ == "__main__":

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