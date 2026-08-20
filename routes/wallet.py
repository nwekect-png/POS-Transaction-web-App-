"""
wallets.py
Wallet Blueprint for POS Transaction Web App
"""

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required, current_user
from werkzeug.security import check_password_hash

wallet_bp = Blueprint(
    "wallet",
    __name__,
    url_prefix="/wallet"
)


# ==========================================================
# Generate Transaction Reference
# ==========================================================

def generate_reference():
    import uuid
    return "WAL-" + uuid.uuid4().hex[:12].upper()


# ==========================================================
# WALLET DASHBOARD
# ==========================================================

@wallet_bp.route("/")
@login_required
def wallet_dashboard():

    return render_template(
        "wallet.html",
        balance=current_user.wallet_balance,
        user=current_user
    )


# ==========================================================
# BALANCE ENQUIRY
# ==========================================================

@wallet_bp.route("/balance")
@login_required
def balance():

    return render_template(
        "balance.html",
        balance=current_user.wallet_balance
    )


# ==========================================================
# DEPOSIT
# ==========================================================

@wallet_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():

    from app import db, Transaction

    if request.method == "POST":

        amount = float(request.form["amount"])
        pin = request.form["transaction_pin"]

        if amount <= 0:
            flash("Invalid amount.", "danger")
            return redirect(url_for("wallet.deposit"))

        if not check_password_hash(current_user.transaction_pin, pin):
            flash("Invalid transaction PIN.", "danger")
            return redirect(url_for("wallet.deposit"))

        current_user.wallet_balance += amount

        transaction = Transaction(
            transaction_reference=generate_reference(),
            sender_name=current_user.full_name,
            receiver_name=current_user.full_name,
            account_number=current_user.username,
            bank_name="Wallet",
            transaction_type="Deposit",
            amount=amount,
            description="Wallet Deposit",
            status="Success",
            created_at=datetime.utcnow()
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Wallet funded successfully.", "success")

        return redirect(url_for("wallet.wallet_dashboard"))

    return render_template("deposit.html")


# ==========================================================
# WITHDRAW
# ==========================================================

@wallet_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():

    from app import db, Transaction

    if request.method == "POST":

        amount = float(request.form["amount"])
        pin = request.form["transaction_pin"]

        if amount <= 0:
            flash("Invalid amount.", "danger")
            return redirect(url_for("wallet.withdraw"))

        if amount > current_user.wallet_balance:
            flash("Insufficient wallet balance.", "danger")
            return redirect(url_for("wallet.withdraw"))

        if not check_password_hash(current_user.transaction_pin, pin):
            flash("Invalid transaction PIN.", "danger")
            return redirect(url_for("wallet.withdraw"))

        current_user.wallet_balance -= amount

        transaction = Transaction(
            transaction_reference=generate_reference(),
            sender_name=current_user.full_name,
            receiver_name=current_user.full_name,
            account_number=current_user.username,
            bank_name="Wallet",
            transaction_type="Withdrawal",
            amount=amount,
            description="Wallet Withdrawal",
            status="Success",
            created_at=datetime.utcnow()
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Withdrawal completed successfully.", "success")

        return redirect(url_for("wallet.wallet_dashboard"))

    return render_template("withdrawal.html")


# ==========================================================
# TRANSFER BETWEEN WALLETS
# ==========================================================

@wallet_bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():

    from app import db, User, Transaction

    if request.method == "POST":

        username = request.form["username"]
        amount = float(request.form["amount"])
        pin = request.form["transaction_pin"]

        receiver = User.query.filter_by(username=username).first()

        if receiver is None:
            flash("Recipient not found.", "danger")
            return redirect(url_for("wallet.transfer"))

        if receiver.id == current_user.id:
            flash("You cannot transfer to yourself.", "warning")
            return redirect(url_for("wallet.transfer"))

        if amount <= 0:
            flash("Invalid amount.", "danger")
            return redirect(url_for("wallet.transfer"))

        if amount > current_user.wallet_balance:
            flash("Insufficient wallet balance.", "danger")
            return redirect(url_for("wallet.transfer"))

        if not check_password_hash(current_user.transaction_pin, pin):
            flash("Invalid transaction PIN.", "danger")
            return redirect(url_for("wallet.transfer"))

        current_user.wallet_balance -= amount
        receiver.wallet_balance += amount

        transaction = Transaction(
            transaction_reference=generate_reference(),
            sender_name=current_user.full_name,
            receiver_name=receiver.full_name,
            account_number=receiver.username,
            bank_name="Internal Wallet",
            transaction_type="Wallet Transfer",
            amount=amount,
            description="Wallet to Wallet Transfer",
            status="Success",
            created_at=datetime.utcnow()
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Transfer completed successfully.", "success")

        return redirect(url_for("wallet.wallet_dashboard"))

    return render_template("wallet_transfer.html")


# ==========================================================
# WALLET HISTORY
# ==========================================================

@wallet_bp.route("/history")
@login_required
def history():

    from app import Transaction

    transactions = (
        Transaction.query
        .filter(
            (Transaction.sender_name == current_user.full_name) |
            (Transaction.receiver_name == current_user.full_name)
        )
        .order_by(Transaction.created_at.desc())
        .all()
    )

    return render_template(
        "wallet_history.html",
        transactions=transactions
    )
    <img
    src="{{ url_for('static', filename='images/wallet.png') }}"
    alt="Wallet"
    class="wallet-image"
