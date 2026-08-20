"""
user.py
User Blueprint for POS Transaction Web App
"""

import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)

from flask_login import login_required, current_user

user_bp = Blueprint(
    "user",
    __name__,
    url_prefix="/user"
)


# ==========================================================
# PROFILE
# ==========================================================

@user_bp.route("/profile")
@login_required
def profile():

    return render_template(
        "profile.html",
        user=current_user
    )


# ==========================================================
# EDIT PROFILE
# ==========================================================

@user_bp.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    from app import db

    if request.method == "POST":

        current_user.full_name = request.form["full_name"]
        current_user.email = request.form["email"]
        current_user.phone = request.form["phone"]

        db.session.commit()

        flash("Profile updated successfully.", "success")

        return redirect(url_for("user.profile"))

    return render_template(
        "edit_profile.html",
        user=current_user
    )


# ==========================================================
# WALLET
# ==========================================================

@user_bp.route("/wallet")
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

@user_bp.route("/balance")
@login_required
def balance():

    return render_template(
        "balance.html",
        balance=current_user.wallet_balance
    )


# ==========================================================
# CHANGE PASSWORD
# ==========================================================

@user_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    from app import db

    if request.method == "POST":

        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not check_password_hash(
            current_user.password,
            old_password
        ):

            flash("Current password is incorrect.", "danger")

            return redirect(url_for("user.change_password"))

        if new_password != confirm_password:

            flash("Passwords do not match.", "warning")

            return redirect(url_for("user.change_password"))

        current_user.password = generate_password_hash(new_password)

        db.session.commit()

        flash("Password updated successfully.", "success")

        return redirect(url_for("user.profile"))

    return render_template("change_password.html")


# ==========================================================
# CHANGE TRANSACTION PIN
# ==========================================================

@user_bp.route("/change-pin", methods=["GET", "POST"])
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

            flash("Current PIN is incorrect.", "danger")

            return redirect(url_for("user.change_pin"))

        if new_pin != confirm_pin:

            flash("PINs do not match.", "warning")

            return redirect(url_for("user.change_pin"))

        current_user.transaction_pin = generate_password_hash(new_pin)

        db.session.commit()

        flash("Transaction PIN changed successfully.", "success")

        return redirect(url_for("user.profile"))

    return render_template("change_pin.html")


# ==========================================================
# SETTINGS
# ==========================================================

@user_bp.route("/settings")
@login_required
def settings():

    return render_template(
        "settings.html",
        user=current_user
    )


# ==========================================================
# UPLOAD PROFILE PHOTO
# ==========================================================

@user_bp.route("/upload-photo", methods=["POST"])
@login_required
def upload_photo():

    from app import db

    if "photo" not in request.files:

        flash("No file selected.", "warning")

        return redirect(url_for("user.profile"))

    file = request.files["photo"]

    if file.filename == "":

        flash("Please choose a file.", "warning")

        return redirect(url_for("user.profile"))

    filename = secure_filename(file.filename)

    upload_folder = current_app.config["UPLOAD_FOLDER"]

    os.makedirs(upload_folder, exist_ok=True)

    file.save(os.path.join(upload_folder, filename))

    current_user.profile_image = filename

    db.session.commit()

    flash("Profile photo uploaded successfully.", "success")

    return redirect(url_for("user.profile"))
