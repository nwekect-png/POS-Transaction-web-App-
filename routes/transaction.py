"""
transaction.py
Transaction Blueprint for POS Transaction Web App
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash

transaction_bp = Blueprint(
    "transaction",
    __name__,
    url_prefix="/transaction"
)


# ==========================================================
# Helper Function
# ==========================================================

def generate_reference():
    import uuid
    return "POS-" + uuid.uuid4().hex[:12].upper()


# ==========================================================
# DEPOSIT
# ==========================================================

@transaction_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():

    from app import db, Transaction

    if request.method == "POST":

        amount = float(request.form["amount"])
        account_number = request.form["account_number"]
        bank_name = request.form["bank_name"]
        pin = request.form["transaction_pin"]

        if amount <= 0:
            flash("Invalid amount.", "danger")
            return redirect(url_for("transaction.deposit"))

        if not check_password_hash(current_user.transaction_pin, pin):
            flash("Invalid transaction PIN.", "danger")
            return redirect(url_for("transaction.deposit"))

        current_user.wallet_balance += amount

        transaction = Transaction(
            transaction_reference=generate_reference(),
            sender_name=current_user.full_name,
            receiver_name=current_user.full_name,
            account_number=account_number,
            bank_name=bank_name,
            transaction_type="Deposit",
            amount=amount,
            description="Wallet Deposit",
            status="Success",
            created_at=datetime.utcnow()
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Deposit completed successfully.", "success")

        return redirect(url_for("transaction.history"))

    return render_template("deposit.html")


# ==========================================================
# CASH WITHDRAWAL
# ==========================================================

@transaction_bp.route("/withdrawal", methods=["GET", "POST"])
@login_required
def withdrawal():

    from app import db, Transaction

    if request.method == "POST":

        amount = float(request.form["amount"])
        account_number = request.form["account_number"]
        bank_name = request.form["bank_name"]
        pin = request.form["transaction_pin"]

        if amount > current_user.wallet_balance:
            flash("Insufficient wallet balance.", "danger")
            return redirect(url_for("transaction.withdrawal"))

        if not check_password_hash(current_user.transaction_pin, pin):
            flash("Invalid transaction PIN.", "danger")
            return redirect(url_for("transaction.withdrawal"))

        current_user.wallet_balance -= amount

        transaction = Transaction(
            transaction_reference=generate_reference(),
            sender_name=current_user.full_name,
            receiver_name=current_user.full_name,
            account_number=account_number,
            bank_name=bank_name,
            transaction_type="Withdrawal",
            amount=amount,
            description="Cash Withdrawal",
            status="Success",
            created_at=datetime.utcnow()
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Withdrawal completed successfully.", "success")

        return redirect(url_for("transaction.history"))

    return render_template("withdrawal.html")


# ==========================================================
# SEND MONEY
# ==========================================================

@transaction_bp.route("/send-money", methods=["GET", "POST"])
@login_required
def send_money():

    from app import db, Transaction

    if request.method == "POST":

        receiver = request.form["receiver_name"]
        account_number = request.form["account_number"]
        bank_name = request.form["bank_name"]
        amount = float(request.form["amount"])
        narration = request.form.get("narration", "")
        pin = request.form["transaction_pin"]

        if amount > current_user.wallet_balance:
            flash("Insufficient wallet balance.", "danger")
            return redirect(url_for("transaction.send_money"))

        if not check_password_hash(current_user.transaction_pin, pin):
            flash("Invalid transaction PIN.", "danger")
            return redirect(url_for("transaction.send_money"))

        current_user.wallet_balance -= amount

        transaction = Transaction(
            transaction_reference=generate_reference(),
            sender_name=current_user.full_name,
            receiver_name=receiver,
            account_number=account_number,
            bank_name=bank_name,
            transaction_type="Send Money",
            amount=amount,
            description=narration,
            status="Success",
            created_at=datetime.utcnow()
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Transfer completed successfully.", "success")

        return redirect(url_for("transaction.transfer_success"))

    return render_template("send_money.html")


# ==========================================================
# RECEIVE MONEY
# ==========================================================

@transaction_bp.route("/receive-money", methods=["GET", "POST"])
@login_required
def receive_money():

    from app import db, Transaction

    if request.method == "POST":

        sender = request.form["sender_name"]
        amount = float(request.form["amount"])
        account_number = request.form["account_number"]
        bank_name = request.form["bank_name"]
        description = request.form.get("description", "")

        current_user.wallet_balance += amount

        transaction = Transaction(
            transaction_reference=generate_reference(),
            sender_name=sender,
            receiver_name=current_user.full_name,
            account_number=account_number,
            bank_name=bank_name,
            transaction_type="Receive Money",
            amount=amount,
            description=description,
            status="Success",
            created_at=datetime.utcnow()
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Money received successfully.", "success")

        return redirect(url_for("transaction.transfer_success"))

    return render_template("receive_money.html")


# ==========================================================
# TRANSACTION HISTORY
# ==========================================================

@transaction_bp.route("/history")
@login_required
def history():

    from app import Transaction

    transactions = (
        Transaction.query
        .order_by(Transaction.created_at.desc())
        .all()
    )

    return render_template(
        "transaction_history.html",
        transactions=transactions
    )


# ==========================================================
# TRANSFER SUCCESS
# ==========================================================

@transaction_bp.route("/transfer-success")
@login_required
def transfer_success():

    return render_template("transfer_success_history.html")


# ==========================================================
# BALANCE ENQUIRY
# ==========================================================

@transaction_bp.route("/balance")
@login_required
def balance():

    return render_template(
        "balance.html",
        balance=current_user.wallet_balance
    )


# ==========================================================
# RECEIPT
# ==========================================================

@transaction_bp.route("/receipt/<reference>")
@login_required
def receipt(reference):

    from app import Transaction

    transaction = Transaction.query.filter_by(
        transaction_reference=reference
    ).first_or_404()

    return render_template(
        "receipt.html",
        transaction=transaction
    )
