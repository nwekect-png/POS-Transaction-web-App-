# ============================================================
# POS TRANSACTION WEB APP
# Complete Flask Application
# ============================================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    Response
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

from sqlalchemy import or_

from datetime import datetime, date
import secrets
import csv
import io


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = secrets.token_hex(32)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///pos_transaction.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ============================================================
# DATABASE
# ============================================================

db = SQLAlchemy(app)


# ============================================================
# LOGIN MANAGER
# ============================================================

login_manager = LoginManager()

login_manager.login_view = "login"

login_manager.login_message = "Please login to continue."

login_manager.init_app(app)


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
        db.String(120),
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
        db.String(20),
        default="Agent"
    )

    status = db.Column(
        db.String(20),
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
        db.String(50),
        unique=True,
        nullable=False
    )

    sender_name = db.Column(
        db.String(120),
        nullable=True
    )

    receiver_name = db.Column(
        db.String(120),
        nullable=True
    )

    account_number = db.Column(
        db.String(30),
        nullable=True
    )

    bank_name = db.Column(
        db.String(120),
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
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="Success"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
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
        db.String(50),
        unique=True,
        nullable=False
    )

    transaction_reference = db.Column(
        db.String(50),
        nullable=False
    )

    customer = db.Column(
        db.String(120),
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
# USER LOADER
# ============================================================

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_reference():

    return (
        "POS"
        + secrets.token_hex(6).upper()
    )


def generate_receipt():

    return (
        "RCPT"
        + secrets.token_hex(5).upper()
    )


def get_amount(value):

    try:

        amount = float(value)

        return amount

    except (TypeError, ValueError):

        return None


def verify_pin(pin):

    if not current_user.transaction_pin:

        flash(
            "Please create a transaction PIN first.",
            "warning"
        )

        return False

    if not check_password_hash(
        current_user.transaction_pin,
        pin
    ):

        flash(
            "Invalid transaction PIN.",
            "danger"
        )

        return False

    return True


def create_receipt(transaction):

    receipt = Receipt(
        receipt_number=generate_receipt(),
        transaction_reference=(
            transaction.transaction_reference
        ),
        customer=(
            transaction.receiver_name
            or transaction.sender_name
            or current_user.full_name
        ),
        amount=transaction.amount,
        transaction_type=transaction.transaction_type
    )

    db.session.add(receipt)

    return receipt


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

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

        role = request.form.get(
            "role",
            "Agent"
        )

        transaction_pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        if not full_name:

            flash(
                "Full name is required.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if not username:

            flash(
                "Username is required.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if not email:

            flash(
                "Email is required.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if not password:

            flash(
                "Password is required.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:

            flash(
                "Username already exists.",
                "warning"
            )

            return redirect(
                url_for("register")
            )

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:

            flash(
                "Email already exists.",
                "warning"
            )

            return redirect(
                url_for("register")
            )

        if role not in ["Agent", "Admin"]:

            role = "Agent"

        password_hash = generate_password_hash(
            password
        )

        pin_hash = None

        if transaction_pin:

            pin_hash = generate_password_hash(
                transaction_pin
            )

        user = User(

            full_name=full_name,

            username=username,

            email=email,

            phone=phone,

            password=password_hash,

            transaction_pin=pin_hash,

            role=role,

            status="Active",

            wallet_balance=0.00
        )

        try:

            db.session.add(user)

            db.session.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Registration failed. Please try again.",
                "danger"
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

        user = User.query.filter_by(
            username=username
        ).first()

        if not user:

            flash(
                "Invalid username or password.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        if user.status != "Active":

            flash(
                "Your account is disabled.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        if not check_password_hash(
            user.password,
            password
        ):

            flash(
                "Invalid username or password.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        login_user(user)

        session["user_id"] = user.id

        session["username"] = user.username

        session["role"] = user.role

        flash(
            "Login successful.",
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
        "You have logged out successfully.",
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

    transactions = (
        Transaction.query
        .filter(
            or_(
                Transaction.sender_name
                == current_user.full_name,

                Transaction.receiver_name
                == current_user.full_name
            )
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .limit(10)
        .all()
    )

    return render_template(
        "dashboard.html",
        user=current_user,
        transactions=transactions
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin_dashboard")
@login_required
def admin_dashboard():

    if current_user.role != "Admin":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    total_users = User.query.count()

    total_transactions = Transaction.query.count()

    total_deposit = (
        db.session.query(
            db.func.sum(Transaction.amount)
        )
        .filter_by(
            transaction_type="Deposit"
        )
        .scalar()
        or 0
    )

    total_withdrawal = (
        db.session.query(
            db.func.sum(Transaction.amount)
        )
        .filter_by(
            transaction_type="Withdrawal"
        )
        .scalar()
        or 0
    )

    total_sent = (
        db.session.query(
            db.func.sum(Transaction.amount)
        )
        .filter_by(
            transaction_type="Send Money"
        )
        .scalar()
        or 0
    )

    total_received = (
        db.session.query(
            db.func.sum(Transaction.amount)
        )
        .filter_by(
            transaction_type="Receive Money"
        )
        .scalar()
        or 0
    )

    transactions = (
        Transaction.query
        .order_by(
            Transaction.created_at.desc()
        )
        .limit(10)
        .all()
    )

    return render_template(
        "admin_dashboard.html",

        total_users=total_users,

        total_transactions=total_transactions,

        total_deposit=total_deposit,

        total_withdrawal=total_withdrawal,

        total_sent=total_sent,

        total_received=total_received,

        transactions=transactions
    )


# ============================================================
# PROFILE
# ============================================================

@app.route("/profile")
@login_required
def profile():

    return render_template(
        "profile.html",
        user=current_user
    )


# ============================================================
# SETTINGS
# ============================================================

@app.route(
    "/settings",
    methods=["GET", "POST"]
)
@login_required
def settings():

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
                url_for("settings")
            )

        existing_email = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if existing_email:

            flash(
                "Email already belongs to another user.",
                "danger"
            )

            return redirect(
                url_for("settings")
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
            url_for("settings")
        )

    return render_template(
        "settings.html",
        user=current_user
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

@app.route(
    "/change_password",
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

        if len(new_password) < 6:

            flash(
                "New password must be at least 6 characters.",
                "danger"
            )

            return redirect(
                url_for("change_password")
            )

        if new_password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("change_password")
            )

        current_user.password = (
            generate_password_hash(new_password)
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
# CHANGE TRANSACTION PIN
# ============================================================

@app.route(
    "/change_pin",
    methods=["GET", "POST"]
)
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
                    "Old PIN is incorrect.",
                    "danger"
                )

                return redirect(
                    url_for("change_pin")
                )

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

        current_user.transaction_pin = (
            generate_password_hash(new_pin)
        )

        db.session.commit()

        flash(
            "Transaction PIN updated successfully.",
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

    transactions = (
        Transaction.query
        .filter(
            or_(
                Transaction.sender_name
                == current_user.full_name,

                Transaction.receiver_name
                == current_user.full_name
            )
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .limit(20)
        .all()
    )

    total_deposits = (
        db.session.query(
            db.func.sum(Transaction.amount)
        )
        .filter(
            Transaction.transaction_type == "Deposit",
            Transaction.receiver_name
            == current_user.full_name
        )
        .scalar()
        or 0
    )

    total_withdrawals = (
        db.session.query(
            db.func.sum(Transaction.amount)
        )
        .filter(
            Transaction.transaction_type == "Withdrawal",
            Transaction.sender_name
            == current_user.full_name
        )
        .scalar()
        or 0
    )

    total_sent = (
        db.session.query(
            db.func.sum(Transaction.amount)
        )
        .filter(
            Transaction.transaction_type == "Send Money",
            Transaction.sender_name
            == current_user.full_name
        )
        .scalar()
        or 0
    )

    total_received = (
        db.session.query(
            db.func.sum(Transaction.amount)
        )
        .filter(
            Transaction.transaction_type == "Receive Money",
            Transaction.receiver_name
            == current_user.full_name
        )
        .scalar()
        or 0
    )

    wallet_data = {
        "balance": current_user.wallet_balance,

        "total_deposits": total_deposits,

        "total_withdrawals": total_withdrawals,

        "total_sent": total_sent,

        "total_received": total_received
    }

    return render_template(
        "wallet.html",
        wallet=wallet_data,
        transactions=transactions
    )


# ============================================================
# BALANCE
# ============================================================

@app.route("/balance")
@login_required
def balance():

    return render_template(
        "balance.html",
        balance=current_user.wallet_balance
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

        customer = request.form.get(
            "customer",
            current_user.full_name
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

        if amount is None or amount <= 0:

            flash(
                "Enter a valid deposit amount.",
                "danger"
            )

            return redirect(
                url_for("deposit")
            )

        if not verify_pin(pin):

            return redirect(
                url_for("deposit")
            )

        current_user.wallet_balance += amount

        transaction = Transaction(

            transaction_reference=generate_reference(),

            sender_name=customer,

            receiver_name=current_user.full_name,

            account_number=account_number,

            bank_name=bank_name,

            transaction_type="Deposit",

            amount=amount,

            description="Cash Deposit",

            status="Success"
        )

        db.session.add(transaction)

        db.session.flush()

        create_receipt(transaction)

        db.session.commit()

        flash(
            "Deposit completed successfully.",
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
# CASH WITHDRAWAL
# ============================================================

@app.route(
    "/withdrawal",
    methods=["GET", "POST"]
)
@login_required
def withdrawal():

    if request.method == "POST":

        customer = request.form.get(
            "customer",
            current_user.full_name
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

        if amount is None or amount <= 0:

            flash(
                "Enter a valid withdrawal amount.",
                "danger"
            )

            return redirect(
                url_for("withdrawal")
            )

        if amount > current_user.wallet_balance:

            flash(
                "Insufficient wallet balance.",
                "danger"
            )

            return redirect(
                url_for("withdrawal")
            )

        if not verify_pin(pin):

            return redirect(
                url_for("withdrawal")
            )

        current_user.wallet_balance -= amount

        transaction = Transaction(

            transaction_reference=generate_reference(),

            sender_name=current_user.full_name,

            receiver_name=customer,

            account_number=account_number,

            bank_name=bank_name,

            transaction_type="Withdrawal",

            amount=amount,

            description="Cash Withdrawal",

            status="Success"
        )

        db.session.add(transaction)

        db.session.flush()

        create_receipt(transaction)

        db.session.commit()

        flash(
            "Cash withdrawal successful.",
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
        "withdrawal.html"
    )


# ============================================================
# SEND MONEY
# ============================================================

@app.route(
    "/send_money",
    methods=["GET", "POST"]
)
@login_required
def send_money():

    if request.method == "POST":

        sender_name = request.form.get(
            "sender_name",
            current_user.full_name
        ).strip()

        recipient_name = request.form.get(
            "recipient_name",
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

        narration = request.form.get(
            "narration",
            ""
        ).strip()

        if not recipient_name:

            flash(
                "Recipient name is required.",
                "danger"
            )

            return redirect(
                url_for("send_money")
            )

        if amount is None or amount <= 0:

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return redirect(
                url_for("send_money")
            )

        if amount > current_user.wallet_balance:

            flash(
                "Insufficient wallet balance.",
                "danger"
            )

            return redirect(
                url_for("send_money")
            )

        if not verify_pin(pin):

            return redirect(
                url_for("send_money")
            )

        current_user.wallet_balance -= amount

        transaction = Transaction(

            transaction_reference=generate_reference(),

            sender_name=sender_name,

            receiver_name=recipient_name,

            account_number=account_number,

            bank_name=bank_name,

            transaction_type="Send Money",

            amount=amount,

            description=narration,

            status="Success"
        )

        db.session.add(transaction)

        db.session.flush()

        create_receipt(transaction)

        db.session.commit()

        flash(
            "Money sent successfully.",
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
        "send_money.html"
    )


# ============================================================
# RECEIVE MONEY
# ============================================================

@app.route(
    "/receive_money",
    methods=["GET", "POST"]
)
@login_required
def receive_money():

    if request.method == "POST":

        sender_name = request.form.get(
            "sender_name",
            ""
        ).strip()

        receiver_name = request.form.get(
            "receiver_name",
            current_user.full_name
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

        description = request.form.get(
            "description",
            ""
        ).strip()

        if amount is None or amount <= 0:

            flash(
                "Enter a valid amount.",
                "danger"
            )

            return redirect(
                url_for("receive_money")
            )

        current_user.wallet_balance += amount

        transaction = Transaction(

            transaction_reference=generate_reference(),

            sender_name=sender_name,

            receiver_name=receiver_name,

            account_number=account_number,

            bank_name=bank_name,

            transaction_type="Receive Money",

            amount=amount,

            description=description,

            status="Success"
        )

        db.session.add(transaction)

        db.session.flush()

        create_receipt(transaction)

        db.session.commit()

        flash(
            "Money received successfully.",
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
        "receive_money.html"
    )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.route("/transaction_history")
@login_required
def transaction_history():

    search = request.args.get(
        "search",
        ""
    ).strip()

    query = Transaction.query

    if search:

        query = query.filter(

            or_(

                Transaction.sender_name.contains(
                    search
                ),

                Transaction.receiver_name.contains(
                    search
                ),

                Transaction.account_number.contains(
                    search
                ),

                Transaction.bank_name.contains(
                    search
                ),

                Transaction.transaction_reference.contains(
                    search
                ),

                Transaction.transaction_type.contains(
                    search
                )
            )
        )

    transactions = query.order_by(
        Transaction.created_at.desc()
    ).all()

    total_transactions = len(
        transactions
    )

    total_amount = sum(
        transaction.amount
        for transaction in transactions
    )

    return render_template(

        "transaction_history.html",

        transactions=transactions,

        total_transactions=total_transactions,

        total_amount=total_amount,

        search=search
    )


# ============================================================
# TRANSFER SUCCESS HISTORY
# ============================================================

@app.route("/transfer_success_history")
@login_required
def transfer_success_history():

    transfers = (
        Transaction.query
        .filter_by(status="Success")
        .order_by(
            Transaction.created_at.desc()
        )
        .all()
    )

    total_success = len(
        transfers
    )

    total_amount = sum(
        transaction.amount
        for transaction in transfers
    )

    return render_template(

        "transfer_success_history.html",

        transfers=transfers,

        total_success=total_success,

        total_amount=total_amount
    )


# ============================================================
# REPORTS
# ============================================================

@app.route("/reports")
@login_required
def reports():

    deposits = Transaction.query.filter_by(
        transaction_type="Deposit"
    ).count()

    withdrawals = Transaction.query.filter_by(
        transaction_type="Withdrawal"
    ).count()

    sent = Transaction.query.filter_by(
        transaction_type="Send Money"
    ).count()

    received = Transaction.query.filter_by(
        transaction_type="Receive Money"
    ).count()

    total_transactions = Transaction.query.count()

    total_amount = (
        db.session.query(
            db.func.sum(Transaction.amount)
        ).scalar()
        or 0
    )

    return render_template(

        "reports.html",

        deposits=deposits,

        withdrawals=withdrawals,

        sent=sent,

        received=received,

        total_transactions=total_transactions,

        total_amount=total_amount
    )


# ============================================================
# DAILY REPORT
# ============================================================

@app.route("/daily_report")
@login_required
def daily_report():

    today = date.today()

    transactions = (
        Transaction.query
        .filter(
            db.func.date(
                Transaction.created_at
            ) == today
        )
        .order_by(
            Transaction.created_at.desc()
        )
        .all()
    )

    total_amount = sum(
        transaction.amount
        for transaction in transactions
    )

    return render_template(

        "daily_report.html",

        transactions=transactions,

        total_amount=total_amount,

        report_date=today
    )


# ============================================================
# SEARCH TRANSACTIONS
# ============================================================

@app.route("/search_transactions")
@login_required
def search_transactions():

    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    transactions = Transaction.query.filter(

        or_(

            Transaction.sender_name.contains(
                keyword
            ),

            Transaction.receiver_name.contains(
                keyword
            ),

            Transaction.account_number.contains(
                keyword
            ),

            Transaction.bank_name.contains(
                keyword
            ),

            Transaction.transaction_reference.contains(
                keyword
            ),

            Transaction.transaction_type.contains(
                keyword
            )
        )

    ).order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(

        "transaction_history.html",

        transactions=transactions,

        total_transactions=len(
            transactions
        ),

        total_amount=sum(
            transaction.amount
            for transaction in transactions
        ),

        search=keyword
    )


# ============================================================
# RECEIPT
# ============================================================

@app.route("/receipt/<reference>")
@login_required
def receipt(reference):

    transaction = (
        Transaction.query
        .filter_by(
            transaction_reference=reference
        )
        .first_or_404()
    )

    receipt = (
        Receipt.query
        .filter_by(
            transaction_reference=reference
        )
        .first()
    )

    return render_template(

        "receipt.html",

        transaction=transaction,

        receipt=receipt
    )


# ============================================================
# PRINT RECEIPT
# ============================================================

@app.route("/print_receipt/<reference>")
@login_required
def print_receipt(reference):

    transaction = (
        Transaction.query
        .filter_by(
            transaction_reference=reference
        )
        .first_or_404()
    )

    receipt = (
        Receipt.query
        .filter_by(
            transaction_reference=reference
        )
        .first()
    )

    return render_template(

        "print_receipt.html",

        transaction=transaction,

        receipt=receipt
    )


# ============================================================
# EXPORT REPORT
# ============================================================

@app.route("/export_report")
@login_required
def export_report():

    transactions = (
        Transaction.query
        .order_by(
            Transaction.created_at.desc()
        )
        .all()
    )

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([

        "Reference",

        "Sender",

        "Receiver",

        "Account Number",

        "Bank",

        "Transaction Type",

        "Amount",

        "Description",

        "Status",

        "Date"
    ])

    for transaction in transactions:

        writer.writerow([

            transaction.transaction_reference,

            transaction.sender_name,

            transaction.receiver_name,

            transaction.account_number,

            transaction.bank_name,

            transaction.transaction_type,

            transaction.amount,

            transaction.description,

            transaction.status,

            transaction.created_at
        ])

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers[
        "Content-Disposition"
    ] = (
        "attachment; "
        "filename=pos_transaction_report.csv"
    )

    return response


# ============================================================
# ADMIN - USER MANAGEMENT
# ============================================================

@app.route("/users")
@login_required
def users():

    if current_user.role != "Admin":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    users_list = (
        User.query
        .order_by(
            User.created_at.desc()
        )
        .all()
    )

    return render_template(

        "user.html",

        users=users_list
    )


# ============================================================
# ADMIN - EDIT USER
# ============================================================

@app.route(
    "/edit_user/<int:user_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_user(user_id):

    if current_user.role != "Admin":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    user = User.query.get_or_404(
        user_id
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

        role = request.form.get(
            "role",
            "Agent"
        )

        if role not in ["Admin", "Agent"]:

            role = "Agent"

        existing_username = User.query.filter(
            User.username == username,
            User.id != user.id
        ).first()

        if existing_username:

            flash(
                "Username already exists.",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_user",
                    user_id=user.id
                )
            )

        existing_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_email:

            flash(
                "Email already exists.",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_user",
                    user_id=user.id
                )
            )

        user.full_name = full_name

        user.username = username

        user.email = email

        user.phone = phone

        user.role = role

        db.session.commit()

        flash(
            "User updated successfully.",
            "success"
        )

        return redirect(
            url_for("users")
        )

    return render_template(

        "edit_user.html",

        user=user
    )


# ============================================================
# ADMIN - ACTIVATE USER
# ============================================================

@app.route(
    "/activate_user/<int:user_id>"
)
@login_required
def activate_user(user_id):

    if current_user.role != "Admin":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    user = User.query.get_or_404(
        user_id
    )

    user.status = "Active"

    db.session.commit()

    flash(
        "User activated successfully.",
        "success"
    )

    return redirect(
        url_for("users")
    )


# ============================================================
# ADMIN - DEACTIVATE USER
# ============================================================

@app.route(
    "/deactivate_user/<int:user_id>"
)
@login_required
def deactivate_user(user_id):

    if current_user.role != "Admin":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    user = User.query.get_or_404(
        user_id
    )

    if user.id == current_user.id:

        flash(
            "You cannot deactivate yourself.",
            "warning"
        )

        return redirect(
            url_for("users")
        )

    user.status = "Inactive"

    db.session.commit()

    flash(
        "User deactivated successfully.",
        "success"
    )

    return redirect(
        url_for("users")
    )


# ============================================================
# ADMIN - DELETE USER
# ============================================================

@app.route(
    "/delete_user/<int:user_id>"
)
@login_required
def delete_user(user_id):

    if current_user.role != "Admin":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    user = User.query.get_or_404(
        user_id
    )

    if user.id == current_user.id:

        flash(
            "You cannot delete your own account.",
            "warning"
        )

        return redirect(
            url_for("users")
        )

    db.session.delete(user)

    db.session.commit()

    flash(
        "User deleted successfully.",
        "success"
    )

    return redirect(
        url_for("users")
    )


# ============================================================
# ADMIN - VIEW USER
# ============================================================

@app.route(
    "/view_user/<int:user_id>"
)
@login_required
def view_user(user_id):

    if current_user.role != "Admin":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    user = User.query.get_or_404(
        user_id
    )

    return render_template(

        "profile.html",

        user=user
    )


# ============================================================
# 404 ERROR
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


# ============================================================
# 500 ERROR
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    db.session.rollback()

    return render_template(
        "500.html"
    ), 500


# ============================================================
# GLOBAL TEMPLATE VARIABLES
# ============================================================

@app.context_processor
def inject_globals():

    return {
        "current_year": datetime.now().year
    }
# ============================================================
# CREATE DATABASE TABLES
# ============================================================

with app.app_context():

    db.create_all()


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
    
    import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg"
}

def allowed_file(filename):

    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


@app.route("/photo", methods=["GET", "POST"])
@login_required
def photo():

    if request.method == "POST":

        if "photo" not in request.files:

            flash(
                "No file selected.",
                "danger"
            )

            return redirect(url_for("photo"))

        file = request.files["photo"]

        if file.filename == "":

            flash(
                "Please choose a photo.",
                "danger"
            )

            return redirect(url_for("photo"))

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)

            # Make filename unique
            filename = (
                str(current_user.id)
                + "_"
                + filename
            )

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            file.save(filepath)

            current_user.photo = filename

            db.session.commit()

            flash(
                "Profile photo uploaded successfully.",
                "success"
            )

            return redirect(url_for("profile"))

        flash(
            "Only JPG, JPEG and PNG files are allowed.",
            "danger"
        )

    return render_template("photo.html")

@app.route('/editing', methods=['GET', 'POST'])
@login_required
def editing():

    if request.method == 'POST':

        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        if not full_name or not username or not email or not phone:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('editing'))

        # Check if another user already has this username
        existing_username = User.query.filter(
            User.username == username,
            User.id != current_user.id
        ).first()

        if existing_username:
            flash('Username is already in use.', 'danger')
            return redirect(url_for('editing'))

        # Check if another user already has this email
        existing_email = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if existing_email:
            flash('Email address is already in use.', 'danger')
            return redirect(url_for('editing'))

        # Update user information
        current_user.full_name = full_name
        current_user.username = username
        current_user.email = email
        current_user.phone = phone

        db.session.commit()

        # Update session username if your app uses it
        session['username'] = current_user.username

        flash('Profile updated successfully.', 'success')

        return redirect(url_for('profile'))

    return render_template('editing.html')