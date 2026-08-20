"""
admin.py
Admin Routes for POS Transaction Web App
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# --------------------------------------------------
# Admin Permission Decorator
# --------------------------------------------------

def admin_only():

    if current_user.role != "Admin":
        flash("Administrator access required.", "danger")
        return False

    return True


# --------------------------------------------------
# Dashboard
# --------------------------------------------------

@admin_bp.route("/dashboard")
@login_required
def dashboard():

    if not admin_only():
        return redirect(url_for("dashboard"))

    from app import db, User, Transaction

    total_users = User.query.count()

    total_transactions = Transaction.query.count()

    total_balance = db.session.query(
        db.func.sum(User.wallet_balance)
    ).scalar() or 0

    recent_transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).limit(10).all()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_transactions=total_transactions,
        total_balance=total_balance,
        recent_transactions=recent_transactions
    )


# --------------------------------------------------
# Users
# --------------------------------------------------

@app.route("/users")
def users():
def users():

    if not admin_only():
        return redirect(url_for("dashboard"))

    from app import User

    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    return render_template(
        "user.html",
        users=users
    )


# --------------------------------------------------
# View User
# --------------------------------------------------

@admin_bp.route("/user/<int:user_id>")
@login_required
def view_user(user_id):

    if not admin_only():
        return redirect(url_for("dashboard"))

    from app import User

    user = User.query.get_or_404(user_id)

    return render_template(
        "profile.html",
        user=user
    )


# --------------------------------------------------
# Edit User
# --------------------------------------------------

@admin_bp.route("/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
def edit_user(user_id):

    if not admin_only():
        return redirect(url_for("dashboard"))

    from app import db, User

    user = User.query.get_or_404(user_id)

    if request.method == "POST":

        user.full_name = request.form["full_name"]
        user.email = request.form["email"]
        user.phone = request.form["phone"]
        user.role = request.form["role"]

        db.session.commit()

        flash("User updated successfully.", "success")

        return redirect(url_for("admin.users"))

    return render_template(
        "edit_user.html",
        user=user
    )


# --------------------------------------------------
# Activate User
# --------------------------------------------------

@admin_bp.route("/activate/<int:user_id>")
@login_required
def activate(user_id):

    if not admin_only():
        return redirect(url_for("dashboard"))

    from app import db, User

    user = User.query.get_or_404(user_id)

    user.status = "Active"

    db.session.commit()

    flash("User activated.", "success")

    return redirect(url_for("admin.users"))


# --------------------------------------------------
# Deactivate User
# --------------------------------------------------

@admin_bp.route("/deactivate/<int:user_id>")
@login_required
def deactivate(user_id):

    if not admin_only():
        return redirect(url_for("dashboard"))

    from app import db, User

    user = User.query.get_or_404(user_id)

    user.status = "Inactive"

    db.session.commit()

    flash("User deactivated.", "warning")

    return redirect(url_for("admin.users"))


# --------------------------------------------------
# Delete User
# --------------------------------------------------

@admin_bp.route("/delete/<int:user_id>")
@login_required
def delete(user_id):

    if not admin_only():
        return redirect(url_for("dashboard"))

    from app import db, User

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:

        flash("You cannot delete yourself.", "danger")

        return redirect(url_for("admin.users"))

    db.session.delete(user)

    db.session.commit()

    flash("User deleted successfully.", "success")

    return redirect(url_for("admin.users"))


# --------------------------------------------------
# Transactions
# --------------------------------------------------

@admin_bp.route("/transactions")
@login_required
def transactions():

    if not admin_only():
        return redirect(url_for("dashboard"))

    from app import Transaction

    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(
        "transaction_history.html",
        transactions=transactions
    )


# --------------------------------------------------
# Reports
# --------------------------------------------------

@admin_bp.route("/reports")
@login_required
def reports():

    if not admin_only():
        return redirect(url_for("dashboard"))

    from app import db, Transaction

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

    total_amount = db.session.query(
        db.func.sum(Transaction.amount)
    ).scalar() or 0

    return render_template(
        "reports.html",
        deposits=deposits,
        withdrawals=withdrawals,
        sent=sent,
        received=received,
        total_amount=total_amount
    )
