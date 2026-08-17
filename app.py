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
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from io import BytesIO
import secrets
import csv


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "pos-transaction-secret-key-change-this"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pos_transaction.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ============================================================
# DATABASE MODELS
# ============================================================

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(150), nullable=False)

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
        db.String(50),
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
        db.String(150)
    )

    receiver_name = db.Column(
        db.String(150)
    )

    account_number = db.Column(
        db.String(100)
    )

    bank_name = db.Column(
        db.String(150)
    )

    transaction_type = db.Column(
        db.String(100)
    )

    amount = db.Column(
        db.Float,
        default=0.00
    )

    description = db.Column(
        db.String(255)
    )

    status = db.Column(
        db.String(50),
        default="Success"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )


class Receipt(db.Model):

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
        db.String(150)
    )

    amount = db.Column(
        db.Float,
        default=0.00
    )

    transaction_type = db.Column(
        db.String(100)
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
    return db.session.get(User, int(user_id))


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_reference():

    while True:

        reference = (
            "POS"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + secrets.token_hex(3).upper()
        )

        existing = Transaction.query.filter_by(
            transaction_reference=reference
        ).first()

        if not existing:
            return reference


def generate_receipt():

    while True:

        number = (
            "RCT"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + secrets.token_hex(3).upper()
        )

        existing = Receipt.query.filter_by(
            receipt_number=number
        ).first()

        if not existing:
            return number


def admin_required(function):

    @wraps(function)
    @login_required
    def decorated_function(*args, **kwargs):

        if current_user.role != "Admin":

            flash(
                "Administrator access required.",
                "danger"
            )

            return redirect(url_for("dashboard"))

        return function(*args, **kwargs)

    return decorated_function


def get_amount():

    try:

        amount = float(
            request.form.get("amount", "0")
        )

        return amount

    except (ValueError, TypeError):

        return 0.0


def verify_pin(pin):

    if not current_user.transaction_pin:

        return False

    return check_password_hash(
        current_user.transaction_pin,
        pin
    )


def create_transaction(
    transaction_type,
    amount,
    sender_name="",
    receiver_name="",
    account_number="",
    bank_name="",
    description=""
):

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

        status="Success",

        user_id=current_user.id

    )

    db.session.add(transaction)

    return transaction


# ============================================================
# INITIALIZE DATABASE
# ============================================================

with app.app_context():

    db.create_all()

    # Create default admin if none exists
    admin = User.query.filter_by(
        username="admin"
    ).first()

    if not admin:

        admin = User(

            full_name="System Administrator",

            username="admin",

            email="admin@pos.com",

            phone="08000000000",

            password=generate_password_hash(
                "admin123"
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


# ============================================================
# HOME / INDEX
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

@app.route(
    "/register",
    methods=["GET", "POST"]
)
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
                "danger"
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
                "danger"
            )

            return redirect(
                url_for("register")
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

@app.route(
    "/login",
    methods=["GET", "POST"]
)
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

            # Also allow email login
            user = User.query.filter_by(
                email=username
            ).first()

        if not user:

            flash(
                "Invalid username/email or password.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        if user.status != "Active":

            flash(
                "Your account is not active.",
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
                "Invalid username/email or password.",
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

    balance = current_user.wallet_balance or 0.00

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.created_at.desc()
    ).limit(10).all()

    total_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).count()

    total_sent = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type.in_(
            ["Send Money", "Transfer", "Withdrawal"]
        )
    ).scalar() or 0.00

    total_received = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type.in_(
            ["Receive Money", "Deposit"]
        )
    ).scalar() or 0.00

    return render_template(

        "dashboard.html",

        balance=balance,

        wallet_balance=balance,

        transactions=transactions,

        total_transactions=total_transactions,

        total_sent=total_sent,

        total_received=total_received,

        user=current_user

    )


# ============================================================
# BALANCE
# ============================================================

@app.route("/balance")
@login_required
def balance():

    balance = current_user.wallet_balance or 0.00

    return render_template(

        "balance.html",

        balance=balance,

        wallet_balance=balance,

        user=current_user

    )


# ============================================================
# WALLET
# ============================================================

@app.route("/wallet")
@login_required
def wallet():

    balance = current_user.wallet_balance or 0.00

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(

        "wallet.html",

        balance=balance,

        wallet_balance=balance,

        transactions=transactions,

        user=current_user

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

        amount = get_amount()

        description = request.form.get(
            "description",
            "Wallet Deposit"
        ).strip()

        if amount <= 0:

            flash(
                "Please enter a valid deposit amount.",
                "danger"
            )

            return redirect(
                url_for("deposit")
            )

        current_user.wallet_balance = (
            current_user.wallet_balance or 0.00
        ) + amount

        transaction = create_transaction(

            transaction_type="Deposit",

            amount=amount,

            sender_name="Cash Deposit",

            receiver_name=current_user.full_name,

            description=description

        )

        receipt = Receipt(

            receipt_number=generate_receipt(),

            transaction_reference=(
                transaction.transaction_reference
            ),

            customer=current_user.full_name,

            amount=amount,

            transaction_type="Deposit"

        )

        db.session.add(receipt)

        db.session.commit()

        flash(
            f"Deposit of ₦{amount:,.2f} successful.",
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
        balance=current_user.wallet_balance or 0.00
    )


# ============================================================
# WITHDRAWAL
# ============================================================

@app.route(
    "/withdrawal",
    methods=["GET", "POST"]
)
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
        ).strip()

        if amount <= 0:

            flash(
                "Please enter a valid withdrawal amount.",
                "danger"
            )

            return redirect(
                url_for("withdrawal")
            )

        if amount > (
            current_user.wallet_balance or 0.00
        ):

            flash(
                "Insufficient wallet balance.",
                "danger"
            )

            return redirect(
                url_for("withdrawal")
            )

        if not verify_pin(transaction_pin):

            flash(
                "Invalid transaction PIN.",
                "danger"
            )

            return redirect(
                url_for("withdrawal")
            )

        current_user.wallet_balance -= amount

        transaction = create_transaction(

            transaction_type="Withdrawal",

            amount=amount,

            sender_name=current_user.full_name,

            receiver_name="Cash Withdrawal",

            description=description

        )

        receipt = Receipt(

            receipt_number=generate_receipt(),

            transaction_reference=(
                transaction.transaction_reference
            ),

            customer=current_user.full_name,

            amount=amount,

            transaction_type="Withdrawal"

        )

        db.session.add(receipt)

        db.session.commit()

        flash(
            f"Withdrawal of ₦{amount:,.2f} successful.",
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

        balance=current_user.wallet_balance or 0.00

    )


# ============================================================
# SEND MONEY
# ============================================================

@app.route(
    "/send-money",
    methods=["GET", "POST"]
)
def send_money():

    if not current_user.is_authenticated:

        return redirect(
            url_for("login")
        )

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

        amount = get_amount()

        transaction_pin = request.form.get(
            "transaction_pin",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not receiver_name:

            flash(
                "Receiver name is required.",
                "danger"
            )

            return redirect(
                url_for("send_money")
            )

        if not account_number:

            flash(
                "Account number is required.",
                "danger"
            )

            return redirect(
                url_for("send_money")
            )

        if amount <= 0:

            flash(
                "Please enter a valid amount.",
                "danger"
            )

            return redirect(
                url_for("send_money")
            )

        if amount > (
            current_user.wallet_balance or 0.00
        ):

            flash(
                "Insufficient wallet balance.",
                "danger"
            )

            return redirect(
                url_for("send_money")
            )

        if not verify_pin(transaction_pin):

            flash(
                "Invalid transaction PIN.",
                "danger"
            )

            return redirect(
                url_for("send_money")
            )

        current_user.wallet_balance -= amount

        transaction = create_transaction(

            transaction_type="Send Money",

            amount=amount,

            sender_name=current_user.full_name,

            receiver_name=receiver_name,

            account_number=account_number,

            bank_name=bank_name,

            description=description

        )

        receipt = Receipt(

            receipt_number=generate_receipt(),

            transaction_reference=(
                transaction.transaction_reference
            ),

            customer=current_user.full_name,

            amount=amount,

            transaction_type="Send Money"

        )

        db.session.add(receipt)

        db.session.commit()

        flash(
            f"₦{amount:,.2f} sent successfully.",
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

        balance=current_user.wallet_balance or 0.00

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

        amount = get_amount()

        description = request.form.get(
            "description",
            "Money Received"
        ).strip()

        if not sender_name:

            flash(
                "Sender name is required.",
                "danger"
            )

            return redirect(
                url_for("receive_money")
            )

        if amount <= 0:

            flash(
                "Please enter a valid amount.",
                "danger"
            )

            return redirect(
                url_for("receive_money")
            )

        current_user.wallet_balance = (
            current_user.wallet_balance or 0.00
        ) + amount

        transaction = create_transaction(

            transaction_type="Receive Money",

            amount=amount,

            sender_name=sender_name,

            receiver_name=current_user.full_name,

            description=description

        )

        receipt = Receipt(

            receipt_number=generate_receipt(),

            transaction_reference=(
                transaction.transaction_reference
            ),

            customer=current_user.full_name,

            amount=amount,

            transaction_type="Receive Money"

        )

        db.session.add(receipt)

        db.session.commit()

        flash(
            f"₦{amount:,.2f} received successfully.",
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

        balance=current_user.wallet_balance or 0.00

    )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.route("/transactions")
@login_required
def transaction_history():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(

        "transactions.html",

        transactions=transactions,

        balance=current_user.wallet_balance or 0.00

    )


# ============================================================
# TRANSFER SUCCESS HISTORY
# ============================================================

@app.route("/transfer-success-history")
@login_required
def transfer_success_history():

    transactions = Transaction.query.filter(

        Transaction.user_id == current_user.id,

        Transaction.status == "Success"

    ).order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(

        "transactions.html",

        transactions=transactions,

        balance=current_user.wallet_balance or 0.00

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

        receipt=receipt,

        balance=current_user.wallet_balance or 0.00

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

        "receipt.html",

        transaction=transaction,

        receipt=receipt,

        print_mode=True

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

    if query:

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
                ),

                Transaction.account_number.ilike(
                    f"%{query}%"
                )

            )

        ).order_by(
            Transaction.created_at.desc()
        ).all()

    else:

        transactions = Transaction.query.filter_by(
            user_id=current_user.id
        ).order_by(
            Transaction.created_at.desc()
        ).all()

    return render_template(

        "transactions.html",

        transactions=transactions,

        balance=current_user.wallet_balance or 0.00,

        search_query=query

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

        current_user.full_name = request.form.get(
            "full_name",
            current_user.full_name
        ).strip()

        current_user.email = request.form.get(
            "email",
            current_user.email
        ).strip()

        current_user.phone = request.form.get(
            "phone",
            current_user.phone
        ).strip()

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

        user=current_user,

        balance=current_user.wallet_balance or 0.00

    )


# ============================================================
# SETTINGS
# ============================================================

@app.route("/settings")
@login_required
def settings():

    return render_template(

        "settings.html",

        user=current_user,

        balance=current_user.wallet_balance or 0.00

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
            url_for("login")
        )

    return render_template(
        "change-password.html"
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        user = User.query.filter(
            db.or_(
                User.username == username,
                User.email == username
            )
        ).first()

        if not user:

            flash(
                "No account was found.",
                "danger"
            )

            return redirect(
                url_for("forgot_password")
            )

        session["reset_user_id"] = user.id

        return redirect(
            url_for("reset_password")
        )

    return render_template(
        "forgot-password.html"
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

        if len(new_password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return redirect(
                url_for("reset_password")
            )

        if new_password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("reset_password")
            )

        user.password = generate_password_hash(
            new_password
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
        "reset-password.html"
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

        if not new_pin.isdigit():

            flash(
                "PIN must contain numbers only.",
                "danger"
            )

            return redirect(
                url_for("change_pin")
            )

        if len(new_pin) != 4:

            flash(
                "Transaction PIN must be exactly 4 digits.",
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
            url_for("settings")
        )

    return render_template(
        "change-pin.html"
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

        total=total,

        report_title="Daily Report",

        balance=current_user.wallet_balance or 0.00

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

    total_transactions = len(
        transactions
    )

    total_amount = sum(
        transaction.amount
        for transaction in transactions
    )

    return render_template(

        "reports.html",

        transactions=transactions,

        total_transactions=total_transactions,

        total_amount=total_amount,

        total=total_amount,

        balance=current_user.wallet_balance or 0.00

    )


# ============================================================
# EXPORT REPORT
# ============================================================

@app.route("/export-report")
@login_required
def export_report():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    output = BytesIO()

    text_output = []

    text_output.append(
        "Reference,Type,Amount,Sender,Receiver,Bank,Status,Date\n"
    )

    for transaction in transactions:

        row = [

            transaction.transaction_reference,

            transaction.transaction_type,

            f"{transaction.amount:.2f}",

            transaction.sender_name or "",

            transaction.receiver_name or "",

            transaction.bank_name or "",

            transaction.status,

            transaction.created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        ]

        text_output.append(
            ",".join(
                '"' + str(value).replace('"', '""') + '"'
                for value in row
            ) + "\n"
        )

    data = "".join(
        text_output
    ).encode("utf-8")

    output.write(data)

    output.seek(0)

    return send_file(

        output,

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

    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).limit(50).all()

    total_users = User.query.count()

    total_transactions = Transaction.query.count()

    total_transaction_amount = db.session.query(
        db.func.sum(Transaction.amount)
    ).scalar() or 0.00

    return render_template(

        "admin_dashboard.html",

        users=users,

        transactions=transactions,

        total_users=total_users,

        total_transactions=total_transactions,

        total_transaction_amount=total_transaction_amount,

        balance=current_user.wallet_balance or 0.00

    )


# ============================================================
# ADMIN USER MANAGEMENT
# ============================================================

@app.route(
    "/admin/users"
)
@admin_required
def admin_users():

    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    return render_template(

        "admin.html",

        users=users,

        balance=current_user.wallet_balance or 0.00

    )


# ============================================================
# ADMIN ACTIVATE / DEACTIVATE USER
# ============================================================

@app.route(
    "/admin/user/<int:user_id>/toggle",
    methods=["POST"]
)
@admin_required
def toggle_user(user_id):

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

    if user.status == "Active":

        user.status = "Inactive"

    else:

        user.status = "Active"

    db.session.commit()

    flash(
        f"User {user.username} status changed.",
        "success"
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# ADMIN TRANSACTIONS
# ============================================================

@app.route(
    "/admin/transactions"
)
@admin_required
def admin_transactions():

    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(

        "transactions.html",

        transactions=transactions,

        balance=current_user.wallet_balance or 0.00,

        admin_view=True

    )


# ============================================================
# ADMIN REPORTS
# ============================================================

@app.route(
    "/admin/reports"
)
@admin_required
def admin_reports():

    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).all()

    total = sum(
        transaction.amount
        for transaction in transactions
    )

    return render_template(

        "reports.html",

        transactions=transactions,

        total=total,

        total_amount=total,

        total_transactions=len(
            transactions
        ),

        balance=current_user.wallet_balance or 0.00

    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "application": "POS Transaction Web App"
    }


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

        return """
        <h1>404 - Page Not Found</h1>
        <p>The page you requested does not exist.</p>
        """, 404


@app.errorhandler(500)
def internal_server_error(error):

    db.session.rollback()

    try:

        return render_template(
            "500.html"
        ), 500

    except Exception:

        return """
        <h1>500 - Internal Server Error</h1>
        <p>An unexpected error occurred.</p>
        """, 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )