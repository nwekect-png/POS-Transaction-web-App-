"""
auth.py
Authentication Blueprint for POS Transaction Web App
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)


# ==========================================================
# REGISTER
# ==========================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    from app import db, User

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        full_name = request.form["full_name"]
        username = request.form["username"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        transaction_pin = request.form["transaction_pin"]

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "warning")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists.", "warning")
            return redirect(url_for("auth.register"))

        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            password=generate_password_hash(password),
            transaction_pin=generate_password_hash(transaction_pin),
            wallet_balance=0.0,
            role="Agent",
            status="Active"
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")

        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ==========================================================
# LOGIN
# ==========================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    from app import User

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user is None:

            flash("Invalid username or password.", "danger")

            return redirect(url_for("auth.login"))

        if user.status != "Active":

            flash("Account is inactive.", "danger")

            return redirect(url_for("auth.login"))

        if not check_password_hash(user.password, password):

            flash("Invalid username or password.", "danger")

            return redirect(url_for("auth.login"))

        login_user(user)

        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role

        flash("Login successful.", "success")

        if user.role == "Admin":
            return redirect(url_for("admin.dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ==========================================================
# LOGOUT
# ==========================================================

@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    session.clear()

    flash("Logged out successfully.", "success")

    return redirect(url_for("auth.login"))


# ==========================================================
# CHANGE PASSWORD
# ==========================================================

@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    from app import db

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not check_password_hash(current_user.password, current_password):

            flash("Current password is incorrect.", "danger")

            return redirect(url_for("auth.change_password"))

        if new_password != confirm_password:

            flash("Passwords do not match.", "warning")

            return redirect(url_for("auth.change_password"))

        current_user.password = generate_password_hash(new_password)

        db.session.commit()

        flash("Password changed successfully.", "success")

        return redirect(url_for("dashboard"))

    return render_template("change_password.html")


# ==========================================================
# CHANGE TRANSACTION PIN
# ==========================================================

@auth_bp.route("/change-pin", methods=["GET", "POST"])
@login_required
def change_pin():

    from app import db

    if request.method == "POST":

        old_pin = request.form["old_pin"]
        new_pin = request.form["new_pin"]
        confirm_pin = request.form["confirm_pin"]

        if not check_password_hash(
            current_user.transaction_pin,
            old_pin
        ):

            flash("Invalid current PIN.", "danger")

            return redirect(url_for("auth.change_pin"))

        if new_pin != confirm_pin:

            flash("PINs do not match.", "warning")

            return redirect(url_for("auth.change_pin"))

        current_user.transaction_pin = generate_password_hash(new_pin)

        db.session.commit()

        flash("Transaction PIN updated successfully.", "success")

        return redirect(url_for("dashboard"))

    return render_template("change_pin.html")


# ==========================================================
# FORGOT PASSWORD
# ==========================================================

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        flash(
            "Password reset functionality can be implemented using email OTP.",
            "info"
        )

        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")