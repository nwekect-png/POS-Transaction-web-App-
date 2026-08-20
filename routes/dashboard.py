"""
dashboard.py
Dashboard Blueprint for POS Transaction Web App
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

dashboard_bp = Blueprint("dashboard", __name__)


# ==========================================================
# USER DASHBOARD
# ==========================================================

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    from app import Transaction

    recent_transactions = (
        Transaction.query
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    total_transactions = Transaction.query.count()

    total_sent = Transaction.query.filter_by(
        transaction_type="Send Money"
    ).count()

    total_received = Transaction.query.filter_by(
        transaction_type="Receive Money"
    ).count()

    total_deposits = Transaction.query.filter_by(
        transaction_type="Deposit"
    ).count()

    total_withdrawals = Transaction.query.filter_by(
        transaction_type="Withdrawal"
    ).count()

    return render_template(
        "dashboard.html",
        user=current_user,
        balance=current_user.wallet_balance,
        total_transactions=total_transactions,
        total_sent=total_sent,
        total_received=total_received,
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals,
        transactions=recent_transactions
    )


# ==========================================================
# PROFILE
# ==========================================================

@dashboard_bp.route("/profile")
@login_required
def profile():

    return render_template(
        "profile.html",
        user=current_user
    )


# ==========================================================
# UPDATE PROFILE
# ==========================================================

@dashboard_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():

    from app import db

    if request.method == "POST":

        current_user.full_name = request.form["full_name"]
        current_user.email = request.form["email"]
        current_user.phone = request.form["phone"]

        db.session.commit()

        flash("Profile updated successfully.", "success")

        return redirect(url_for("dashboard.profile"))

    return render_template(
        "edit_profile.html",
        user=current_user
    )


# ==========================================================
# WALLET
# ==========================================================

@dashboard_bp.route("/wallet")
@login_required
def wallet():

    return render_template(
        "wallet.html",
        balance=current_user.wallet_balance,
        user=current_user
    )


# ==========================================================
# BALANCE ENQUIRY
# ==========================================================

@dashboard_bp.route("/balance")
@login_required
def balance():

    return render_template(
        "balance.html",
        balance=current_user.wallet_balance
    )


# ==========================================================
# SETTINGS
# ==========================================================

@dashboard_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    from app import db

    if request.method == "POST":

        current_user.full_name = request.form["full_name"]
        current_user.email = request.form["email"]
        current_user.phone = request.form["phone"]

        db.session.commit()

        flash("Settings updated successfully.", "success")

        return redirect(url_for("dashboard.settings"))

    return render_template(
        "settings.html",
        user=current_user
    )


# ==========================================================
# TRANSACTION SUMMARY
# ==========================================================

@dashboard_bp.route("/summary")
@login_required
def summary():

    from app import db, Transaction

    deposits = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter_by(
        transaction_type="Deposit"
    ).scalar() or 0

    withdrawals = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter_by(
        transaction_type="Withdrawal"
    ).scalar() or 0

    sent = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter_by(
        transaction_type="Send Money"
    ).scalar() or 0

    received = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter_by(
        transaction_type="Receive Money"
    ).scalar() or 0

    return render_template(
        "summary.html",
        deposits=deposits,
        withdrawals=withdrawals,
        sent=sent,
        received=received
    )


# ==========================================================
# RECENT TRANSACTIONS
# ==========================================================

@dashboard_bp.route("/recent-transactions")
@login_required
def recent_transactions():

    from app import Transaction

    transactions = (
        Transaction.query
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )

    return render_template(
        "recent_transactions.html",
        transactions=transactions
    )
