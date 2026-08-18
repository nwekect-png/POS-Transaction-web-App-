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
    jsonify,
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


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "pos-development-secret-key-change-this"
)

# ============================================================
# DATABASE
# PostgreSQL on Render
# SQLite when running locally
# ============================================================

database_url = os.environ.get("DATABASE_URL")

if database_url:
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = (
    database_url or "sqlite:///pos_transaction.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# LOGIN MANAGER
# ============================================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please login to continue."


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
# LOGIN LOADER
# ============================================================

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


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


def admin_required(function):
    @wraps(function)
    @login_required
    def wrapper(*args, **kwargs):

        if current_user.role != "Admin":
            flash("Administrator access required.", "danger")
            return redirect(url_for("dashboard"))

        return function(*args, **kwargs)

    return wrapper


def get_amount():
    try:
        amount = float(request.form.get("amount", 0))
        return amount
    except (TypeError, ValueError):
        return 0


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    if current_user.is_authenticated:

        if current_user.role == "Admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("index.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

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
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )
            return redirect(url_for("register"))

        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:
            flash("Email already exists.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

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

        return redirect(url_for("login"))

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

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

            return redirect(url_for("login"))

        if user.status != "Active":

            flash(
                "Your account is not active.",
                "danger"
            )

            return redirect(url_for("login"))

        if not check_password_hash(
            user.password,
            password
        ):

            flash(
                "Invalid username or password.",
                "danger"
            )

            return redirect(url_for("login"))

        login_user(user)

        session["username"] = user.username
        session["user_id"] = user.id

        if user.role == "Admin":
            return redirect(
                url_for("admin_dashboard")
            )

        return redirect(
            url_for("dashboard")
        )

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

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.created_at.desc()
    ).limit(10).all()

    balance = current_user.wallet_balance or 0.00

    return render_template(
        "dashboard.html",
        balance=balance,
        transactions=transactions
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():

    total_users = User.query.count()

    total_transactions = Transaction.query.count()

    total_amount = db.session.query(
        db.func.sum(Transaction.amount)
    ).scalar() or 0

    users = User.query.order_by(
        User.created_at.desc()
    ).limit(20).all()

    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).limit(20).all()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_transactions=total_transactions,
        total_amount=total_amount,
        users=users,
        transactions=transactions
    )


# ============================================================
# BALANCE
# ============================================================

@app.route("/balance")
@login_required
def balance():

    current_balance = current_user.wallet_balance or 0.00

    return render_template(
        "balance.html",
        balance=current_balance
    )


# ============================================================
# WALLET
# ============================================================

@app.route("/wallet")
@login_required
def wallet():

    current_balance = current_user.wallet_balance or 0.00

    return render_template(
        "wallet.html",
        balance=current_balance
    )


# ============================================================
# DEPOSIT
# ============================================================

@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():

    if request.method == "POST":

        amount = get_amount()

        description = request.form.get(
            "description",
            "Wallet Deposit"
        )

        if amount <= 0:

            flash(
                "Enter a valid deposit amount.",
                "danger"
            )

            return redirect(url_for("deposit"))

        current_user.wallet_balance += amount

        reference = generate_reference()

        transaction = Transaction(
            transaction_reference=reference,
            sender_name="Deposit",
            receiver_name=current_user.full_name,
            transaction_type="Deposit",
            amount=amount,
            description=description,
            status="Success",
            user_id=current_user.id
        )

        receipt = Receipt(
            receipt_number=generate_receipt(),
            transaction_reference=reference,
            customer=current_user.full_name,
            amount=amount,
            transaction_type="Deposit"
        )

        db.session.add(transaction)
        db.session.add(receipt)

        db.session.commit()

        flash(
            f"Deposit of ₦{amount:,.2f} successful.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=reference
            )
        )

    return render_template("deposit.html")


# ============================================================
# WITHDRAWAL
# ============================================================

@app.route("/withdrawal", methods=["GET", "POST"])
@app.route("/cash-withdrawal", methods=["GET", "POST"])
@login_required
def withdrawal():

    if request.method == "POST":

        amount = get_amount()

        transaction_pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        description = request.form.get(
            "description",
            "Cash Withdrawal"
        )

        if amount <= 0:

            flash(
                "Enter a valid withdrawal amount.",
                "danger"
            )

            return redirect(url_for("withdrawal"))

        if amount > current_user.wallet_balance:

            flash(
                "Insufficient wallet balance.",
                "danger"
            )

            return redirect(url_for("withdrawal"))

        if not current_user.transaction_pin:

            flash(
                "Please set your transaction PIN first.",
                "danger"
            )

            return redirect(
                url_for("change_pin")
            )

        if not check_password_hash(
            current_user.transaction_pin,
            transaction_pin
        ):

            flash(
                "Invalid transaction PIN.",
                "danger"
            )

            return redirect(url_for("withdrawal"))

        current_user.wallet_balance -= amount

        reference = generate_reference()

        transaction = Transaction(
            transaction_reference=reference,
            sender_name=current_user.full_name,
            receiver_name="Cash Withdrawal",
            transaction_type="Withdrawal",
            amount=amount,
            description=description,
            status="Success",
            user_id=current_user.id
        )

        receipt = Receipt(
            receipt_number=generate_receipt(),
            transaction_reference=reference,
            customer=current_user.full_name,
            amount=amount,
            transaction_type="Withdrawal"
        )

        db.session.add(transaction)
        db.session.add(receipt)

        db.session.commit()

        flash(
            f"Withdrawal of ₦{amount:,.2f} successful.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=reference
            )
        )

    return render_template("cash-withdrawal.html")


# ============================================================
# SEND MONEY
# ============================================================

@app.route("/send-money", methods=["GET", "POST"])
@app.route("/sending-money", methods=["GET", "POST"])
@login_required
def send_money():

    if request.method == "POST":

        amount = get_amount()

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

        transaction_pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        description = request.form.get(
            "description",
            "Money Transfer"
        )

        if amount <= 0:

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return redirect(url_for("send_money"))

        if not receiver_name:

            flash(
                "Enter receiver name.",
                "danger"
            )

            return redirect(url_for("send_money"))

        if amount > current_user.wallet_balance:

            flash(
                "Insufficient wallet balance.",
                "danger"
            )

            return redirect(url_for("send_money"))

        if not current_user.transaction_pin:

            flash(
                "Please set your transaction PIN first.",
                "danger"
            )

            return redirect(
                url_for("change_pin")
            )

        if not check_password_hash(
            current_user.transaction_pin,
            transaction_pin
        ):

            flash(
                "Invalid transaction PIN.",
                "danger"
            )

            return redirect(url_for("send_money"))

        current_user.wallet_balance -= amount

        reference = generate_reference()

        transaction = Transaction(
            transaction_reference=reference,
            sender_name=current_user.full_name,
            receiver_name=receiver_name,
            account_number=account_number,
            bank_name=bank_name,
            transaction_type="Transfer",
            amount=amount,
            description=description,
            status="Success",
            user_id=current_user.id
        )

        receipt = Receipt(
            receipt_number=generate_receipt(),
            transaction_reference=reference,
            customer=current_user.full_name,
            amount=amount,
            transaction_type="Transfer"
        )

        db.session.add(transaction)
        db.session.add(receipt)

        db.session.commit()

        flash(
            f"Transfer of ₦{amount:,.2f} successful.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=reference
            )
        )

    return render_template("sending-money.html")


# ============================================================
# RECEIVE MONEY
# ============================================================

@app.route("/receive-money", methods=["GET", "POST"])
@app.route("/receiving-money", methods=["GET", "POST"])
@login_required
def receive_money():

    if request.method == "POST":

        amount = get_amount()

        sender_name = request.form.get(
            "sender_name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            "Money Received"
        )

        if amount <= 0:

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return redirect(url_for("receive_money"))

        if not sender_name:

            flash(
                "Enter sender name.",
                "danger"
            )

            return redirect(url_for("receive_money"))

        current_user.wallet_balance += amount

        reference = generate_reference()

        transaction = Transaction(
            transaction_reference=reference,
            sender_name=sender_name,
            receiver_name=current_user.full_name,
            transaction_type="Received",
            amount=amount,
            description=description,
            status="Success",
            user_id=current_user.id
        )

        receipt = Receipt(
            receipt_number=generate_receipt(),
            transaction_reference=reference,
            customer=current_user.full_name,
            amount=amount,
            transaction_type="Received"
        )

        db.session.add(transaction)
        db.session.add(receipt)

        db.session.commit()

        flash(
            f"₦{amount:,.2f} received successfully.",
            "success"
        )

        return redirect(
            url_for(
                "receipt",
                reference=reference
            )
        )

    return render_template("receiving-money.html")


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.route("/transactions")
@app.route("/transaction-history")
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
# PROFILE
# ============================================================

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "POST":

        current_user.full_name = request.form.get(
            "full_name",
            current_user.full_name
        ).strip()

        current_user.phone = request.form.get(
            "phone",
            current_user.phone or ""
        ).strip()

        current_user.email = request.form.get(
            "email",
            current_user.email
        ).strip().lower()

        db.session.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(url_for("profile"))

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

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == "POST":

        old_password = request.form.get(
            "old_password",
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
            old_password
        ):

            flash(
                "Current password is incorrect.",
                "danger"
            )

            return redirect(
                url_for("change_password")
            )

        if len(new_password) < 6:

            flash(
                "New password must contain at least 6 characters.",
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

        current_user.password = generate_password_hash(
            new_password
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
        "change-password.html"
    )


# ============================================================
# CHANGE TRANSACTION PIN
# ============================================================

@app.route("/change-pin", methods=["GET", "POST"])
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

        if not new_pin.isdigit() or len(new_pin) != 4:

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

        current_user.transaction_pin = generate_password_hash(
            new_pin
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

    receipt = Receipt.query.filter_by(
        transaction_reference=reference
    ).first()

    return render_template(
        "receipt.html",
        transaction=transaction,
        receipt=receipt
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

    receipt = Receipt.query.filter_by(
        transaction_reference=reference
    ).first()

    return render_template(
        "print_receipt.html",
        transaction=transaction,
        receipt=receipt
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

    total_amount = sum(
        transaction.amount
        for transaction in transactions
    )

    return render_template(
        "reports.html",
        transactions=transactions,
        total_amount=total_amount
    )


# ============================================================
# DAILY REPORT
# ============================================================

@app.route("/daily-report")
@login_required
def daily_report():

    today = datetime.utcnow().date()

    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        db.func.date(Transaction.created_at) == today
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
        total_amount=total,
        report_date=today
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

    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        db.or_(
            Transaction.transaction_reference.ilike(
                f"%{query}%"
            ),
            Transaction.receiver_name.ilike(
                f"%{query}%"
            ),
            Transaction.sender_name.ilike(
                f"%{query}%"
            )
        )
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(
        "transactions.html",
        transactions=transactions,
        search=query
    )


# ============================================================
# ADMIN USERS
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
# ADMIN TRANSACTIONS
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
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "healthy",
        "application": "POS Transaction Web App"
    })


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
        return "404 - Page Not Found", 404


@app.errorhandler(500)
def internal_server_error(error):

    db.session.rollback()

    try:
        return render_template(
            "500.html"
        ), 500

    except Exception:
        return "500 - Internal Server Error", 500


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

with app.app_context():
    db.create_all()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )