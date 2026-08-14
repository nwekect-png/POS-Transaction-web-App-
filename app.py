rom models import db, User, Transaction, Receipt

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

import os
import secrets
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify
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

from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32)
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///pos_transaction.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ============================================================
# EXTENSIONS
# ============================================================

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please login to access this page."


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
        db.String(120),
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
        default="Agent"
    )

    status = db.Column(
        db.String(30),
        default="Active"
    )

    wallet_balance = db.Column(
        db.Float,
        default=0.00
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
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
        db.String(100),
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
        default="Success"
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


# ============================================================
# LOGIN MANAGER
# ============================================================

@login_manager.user_loader
def load_user(user_id):

    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_reference():

    return (
        "TXN-"
        + datetime.utcnow().strftime("%Y%m%d%H%M%S")
        + "-"
        + secrets.token_hex(3).upper()
    )


def generate_receipt():

    return (
        "RCT-"
        + datetime.utcnow().strftime("%Y%m%d%H%M%S")
        + "-"
        + secrets.token_hex(3).upper()
    )


def get_amount():

    try:
        amount = float(request.form.get("amount", 0))
        return amount

    except (ValueError, TypeError):
        return 0


def admin_required(function):

    @wraps(function)
    @login_required
    def decorated_function(*args, **kwargs):

        if current_user.role != "Admin":

            flash(
                "Administrator access required.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        return function(*args, **kwargs)

    return decorated_function


def create_transaction(
    transaction_type,
    amount,
    sender_name=None,
    receiver_name=None,
    account_number=None,
    bank_name=None,
    description=None,
    user_id=None
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

        user_id=user_id
    )

    db.session.add(transaction)

    return transaction


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

    return render_template("index.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
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

        transaction_pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        if not full_name or not username or not email:

            flash(
                "Please fill in all required fields.",
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

        if len(password) < 6:

            flash(
                "Password must be at least 6 characters.",
                "danger"
            )

            return render_template(
                "register.html"
            )

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

        hashed_password = generate_password_hash(
            password
        )

        hashed_pin = None

        if transaction_pin:

            hashed_pin = generate_password_hash(
                transaction_pin
            )

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

@app.route("/login", methods=["GET", "POST"])
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
# USER DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.created_at.desc()
    ).limit(10).all()

    total_sent = db.session.query(
        db.func.coalesce(
            db.func.sum(Transaction.amount),
            0
        )
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type.in_(
            ["Send", "Transfer", "Withdrawal"]
        )
    ).scalar()

    total_received = db.session.query(
        db.func.coalesce(
            db.func.sum(Transaction.amount),
            0
        )
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type.in_(
            ["Receive", "Deposit"]
        )
    ).scalar()

    transaction_count = Transaction.query.filter_by(
        user_id=current_user.id
    ).count()

    return render_template(
        "dashboard.html",

        transactions=transactions,

        total_sent=total_sent or 0,

        total_received=total_received or 0,

        transaction_count=transaction_count,

        current_year=datetime.utcnow().year
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin_dashboard")
@admin_required
def admin_dashboard():

    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).limit(20).all()

    total_users = User.query.count()

    total_transactions = Transaction.query.count()

    total_money = db.session.query(
        db.func.coalesce(
            db.func.sum(Transaction.amount),
            0
        )
    ).scalar()

    return render_template(
        "admin_dashboard.html",

        users=users,

        transactions=transactions,

        total_users=total_users,

        total_transactions=total_transactions,

        total_money=total_money or 0,

        current_year=datetime.utcnow().year
    )


# ============================================================
# BALANCE
# ============================================================

@app.route("/balance")
@login_required
def balance():

    return render_template(
        "balance.html",
        balance=current_user.wallet_balance or 0
    )


# ============================================================
# DEPOSIT
# ============================================================

@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():

    if request.method == "POST":

        amount = get_amount()

        if amount <= 0:

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return render_template(
                "deposit.html"
            )

        current_user.wallet_balance += amount

        transaction = create_transaction(

            transaction_type="Deposit",

            amount=amount,

            sender_name="Cash Deposit",

            receiver_name=current_user.full_name,

            description="Wallet deposit",

            user_id=current_user.id
        )

        db.session.commit()

        flash(
            f"₦{amount:,.2f} deposited successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "deposit.html"
    )


# ============================================================
# WITHDRAWAL
# ============================================================

@app.route("/withdrawal", methods=["GET", "POST"])
@login_required
def withdrawal():

    if request.method == "POST":

        amount = get_amount()

        if amount <= 0:

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return render_template(
                "withdrawal.html"
            )

        if amount > current_user.wallet_balance:

            flash(
                "Insufficient wallet balance.",
                "danger"
            )

            return render_template(
                "withdrawal.html"
            )

        current_user.wallet_balance -= amount

        transaction = create_transaction(

            transaction_type="Withdrawal",

            amount=amount,

            sender_name=current_user.full_name,

            receiver_name="Cash Withdrawal",

            description="Wallet withdrawal",

            user_id=current_user.id
        )

        db.session.commit()

        flash(
            f"₦{amount:,.2f} withdrawn successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "withdrawal.html"
    )


# ============================================================
# SEND MONEY
# ============================================================

@app.route("/send_money", methods=["GET", "POST"])
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

        amount = get_amount()

        pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        if not receiver_name:

            flash(
                "Receiver name is required.",
                "danger"
            )

            return render_template(
                "sending-money.html"
            )

        if amount <= 0:

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return render_template(
                "sending-money.html"
            )

        if amount > current_user.wallet_balance:

            flash(
                "Insufficient wallet balance.",
                "danger"
            )

            return render_template(
                "sending-money.html"
            )

        if current_user.transaction_pin:

            if not pin or not check_password_hash(
                current_user.transaction_pin,
                pin
            ):

                flash(
                    "Invalid transaction PIN.",
                    "danger"
                )

                return render_template(
                    "sending-money.html"
                )

        current_user.wallet_balance -= amount

        transaction = create_transaction(

            transaction_type="Send",

            amount=amount,

            sender_name=current_user.full_name,

            receiver_name=receiver_name,

            account_number=account_number,

            bank_name=bank_name,

            description=description,

            user_id=current_user.id
        )

        db.session.commit()

        flash(
            f"₦{amount:,.2f} sent successfully.",
            "success"
        )

        return redirect(
            url_for("transfer_success_history")
        )

    return render_template(
        "sending-money.html"
    )


# ============================================================
# RECEIVE MONEY
# ============================================================

@app.route("/receive_money", methods=["GET", "POST"])
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

        amount = get_amount()

        if not sender_name:

            flash(
                "Sender name is required.",
                "danger"
            )

            return render_template(
                "receiving-money.html"
            )

        if amount <= 0:

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return render_template(
                "receiving-money.html"
            )

        current_user.wallet_balance += amount

        transaction = create_transaction(

            transaction_type="Receive",

            amount=amount,

            sender_name=sender_name,

            receiver_name=current_user.full_name,

            description=description,

            user_id=current_user.id
        )

        db.session.commit()

        flash(
            f"₦{amount:,.2f} received successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "receiving-money.html"
    )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.route("/transaction_history")
@login_required
def transaction_history():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(
        "transactions.html",
        transactions=transactions
    )


# ============================================================
# TRANSFER SUCCESS HISTORY
# ============================================================

@app.route("/transfer_success_history")
@login_required
def transfer_success_history():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id,
        status="Success"
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(
        "transactions.html",
        transactions=transactions
    )


# ============================================================
# PROFILE
# ============================================================

@app.route("/profile", methods=["GET", "POST"])
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
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        if full_name:

            current_user.full_name = full_name

        if email:

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

@app.route("/change_password", methods=["GET", "POST"])
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
                "change_password.html"
            )

        if len(new_password) < 6:

            flash(
                "New password must be at least 6 characters.",
                "danger"
            )

            return render_template(
                "change_password.html"
            )

        if new_password != confirm_password:

            flash(
                "New passwords do not match.",
                "danger"
            )

            return render_template(
                "change_password.html"
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
        "change_password.html"
    )


# ============================================================
# CHANGE TRANSACTION PIN
# ============================================================

@app.route("/change_pin", methods=["GET", "POST"])
@login_required
def change_pin():

    if request.method == "POST":

        old_pin = request.form.get(
            "old_pin",
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
                old_pin
            ):

                flash(
                    "Current transaction PIN is incorrect.",
                    "danger"
                )

                return render_template(
                    "change_pin.html"
                )

        if not new_pin.isdigit() or len(new_pin) != 4:

            flash(
                "Transaction PIN must contain exactly 4 digits.",
                "danger"
            )

            return render_template(
                "change_pin.html"
            )

        if new_pin != confirm_pin:

            flash(
                "Transaction PINs do not match.",
                "danger"
            )

            return render_template(
                "change_pin.html"
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
        "change_pin.html"
    )


# ============================================================
# REPORTS
# ============================================================

@app.route("/reports")
@login_required
def reports():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    total_transactions = len(transactions)

    total_amount = sum(
        transaction.amount
        for transaction in transactions
    )

    return render_template(
        "reports.html",

        transactions=transactions,

        total_transactions=total_transactions,

        total_amount=total_amount
    )


# ============================================================
# DAILY REPORT
# ============================================================

@app.route("/daily_report")
@login_required
def daily_report():

    today = datetime.utcnow().date()

    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        db.func.date(
            Transaction.created_at
        ) == today
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    total = sum(
        transaction.amount
        for transaction in transactions
    )

    return render_template(
        "reports.html",
        transactions=transactions,
        total_transactions=len(transactions),
        total_amount=total
    )


# ============================================================
# SEARCH TRANSACTIONS
# ============================================================

@app.route("/search_transactions")
@login_required
def search_transactions():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if query:

        transactions = Transaction.query.filter(

            Transaction.user_id == current_user.id,

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

                Transaction.transaction_type.ilike(
                    f"%{query}%"
                )

            )

        ).order_by(
            Transaction.created_at.desc()
        ).all()

    else:

        transactions = []

    return render_template(
        "transactions.html",
        transactions=transactions,
        search_query=query
    )


# ============================================================
# RECEIPT
# ============================================================

@app.route("/receipt/<int:transaction_id>")
@login_required
def receipt(transaction_id):

    transaction = db.session.get(
        Transaction,
        transaction_id
    )

    if not transaction:

        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transaction_history")
        )

    if (
        transaction.user_id != current_user.id
        and current_user.role != "Admin"
    ):

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("transaction_history")
        )

    receipt = Receipt.query.filter_by(
        transaction_reference=
        transaction.transaction_reference
    ).first()

    if not receipt:

        receipt = Receipt(

            receipt_number=generate_receipt(),

            transaction_reference=
            transaction.transaction_reference,

            customer=(
                transaction.receiver_name
                or transaction.sender_name
                or current_user.full_name
            ),

            amount=transaction.amount,

            transaction_type=
            transaction.transaction_type
        )

        db.session.add(receipt)

        db.session.commit()

    return render_template(
        "receipt.html",
        transaction=transaction,
        receipt=receipt
    )


# ============================================================
# PRINT RECEIPT
# ============================================================

@app.route("/print_receipt/<int:transaction_id>")
@login_required
def print_receipt(transaction_id):

    transaction = db.session.get(
        Transaction,
        transaction_id
    )

    if not transaction:

        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transaction_history")
        )

    return render_template(
        "receipt.html",
        transaction=transaction,
        print_mode=True
    )


# ============================================================
# ADMIN - USERS
# ============================================================

@app.route("/admin/users")
@admin_required
def admin_users():

    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    return render_template(
        "admin_dashboard.html",
        users=users
    )


# ============================================================
# ADMIN - ACTIVATE USER
# ============================================================

@app.route("/admin/activate/<int:user_id>")
@admin_required
def activate_user(user_id):

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

    user.status = "Active"

    db.session.commit()

    flash(
        "User activated successfully.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# ADMIN - DEACTIVATE USER
# ============================================================

@app.route("/admin/deactivate/<int:user_id>")
@admin_required
def deactivate_user(user_id):

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
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    user.status = "Inactive"

    db.session.commit()

    flash(
        "User deactivated successfully.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# ADMIN - ALL TRANSACTIONS
# ============================================================

@app.route("/admin/transactions")
@admin_required
def admin_transactions():

    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(
        "transactions.html",
        transactions=transactions
    )


# ============================================================
# EXPORT REPORT
# ============================================================

@app.route("/export_report")
@login_required
def export_report():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    lines = []

    lines.append(
        "Reference,Type,Sender,Receiver,Amount,Status,Date"
    )

    for transaction in transactions:

        lines.append(

            f'"{transaction.transaction_reference}",'
            f'"{transaction.transaction_type}",'
            f'"{transaction.sender_name or ""}",'
            f'"{transaction.receiver_name or ""}",'
            f'"{transaction.amount}",'
            f'"{transaction.status}",'
            f'"{transaction.created_at}"'

        )

    csv_data = "\n".join(lines)

    response = app.response_class(
        csv_data,
        mimetype="text/csv"
    )

    response.headers[
        "Content-Disposition"
    ] = "attachment; filename=transaction_report.csv"

    return response


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
            "<h1>404 - Page Not Found</h1>",
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
            "<h1>500 - Internal Server Error</h1>",
            500
        )


# ============================================================
# CREATE DATABASE
# ============================================================

with app.app_context():

    db.create_all()

    # --------------------------------------------------------
    # CREATE DEFAULT ADMIN IF ONE DOES NOT EXIST
    # --------------------------------------------------------

    admin = User.query.filter_by(
        username="admin"
    ).first()

    if not admin:

        admin = User(

            full_name="System Administrator",

            username="admin",

            email="admin@example.com",

            phone="",

            password=generate_password_hash(
                "Admin@123"
            ),

            transaction_pin=generate_password_hash(
                "1234"
            ),

            role="Admin",

            status="Active",

            wallet_balance=0.00
        )

        db.session.add(admin)

        db.session.commit()

        print("==========================================")
        print("DEFAULT ADMIN ACCOUNT CREATED")
        print("Username: admin")
        print("Password: Admin@123")
        print("PIN: 1234")
        print("CHANGE THESE CREDENTIALS AFTER LOGIN")
        print("==========================================")


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000,
        debug=True,
        use_reloader=False
    )