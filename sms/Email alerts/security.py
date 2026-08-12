"""
security.py
Security utilities for POS Transaction Web App
"""

import os
import uuid
import random
import bcrypt
from functools import wraps
from datetime import datetime
from cryptography.fernet import Fernet
from flask import session, redirect, url_for, flash

# ==========================================================
# ENCRYPTION KEY
# ==========================================================

# Generate one with:
# from cryptography.fernet import Fernet
# print(Fernet.generate_key().decode())

SECRET_KEY = os.getenv(
    "FERNET_SECRET_KEY",
    "REPLACE_WITH_YOUR_GENERATED_FERNET_KEY"
).encode()

cipher = Fernet(SECRET_KEY)

# ==========================================================
# PASSWORD FUNCTIONS
# ==========================================================

def hash_password(password):
    """Hash a user password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(
        password.encode(),
        salt
    ).decode()


def verify_password(password, hashed_password):
    """Verify a password."""
    return bcrypt.checkpw(
        password.encode(),
        hashed_password.encode()
    )

# ==========================================================
# TRANSACTION PIN
# ==========================================================

def hash_pin(pin):
    """Hash a transaction PIN."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(
        pin.encode(),
        salt
    ).decode()


def verify_pin(pin, hashed_pin):
    """Verify transaction PIN."""
    return bcrypt.checkpw(
        pin.encode(),
        hashed_pin.encode()
    )

# ==========================================================
# ENCRYPTION
# ==========================================================

def encrypt(text):
    """Encrypt sensitive text."""
    return cipher.encrypt(
        text.encode()
    ).decode()


def decrypt(encrypted_text):
    """Decrypt encrypted text."""
    return cipher.decrypt(
        encrypted_text.encode()
    ).decode()

# ==========================================================
# OTP
# ==========================================================

def generate_otp():
    """Generate a six-digit OTP."""
    return str(random.randint(100000, 999999))

# ==========================================================
# TRANSACTION REFERENCE
# ==========================================================

def generate_reference():
    """Generate unique transaction reference."""
    return "POS-" + uuid.uuid4().hex[:12].upper()

# ==========================================================
# RECEIPT NUMBER
# ==========================================================

def generate_receipt_number():
    """Generate receipt number."""
    return datetime.now().strftime("RCPT%Y%m%d%H%M%S")

# ==========================================================
# LOGIN REQUIRED DECORATOR
# ==========================================================

def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            flash("Please login first.", "warning")

            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view

# ==========================================================
# ADMIN REQUIRED DECORATOR
# ==========================================================

def admin_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if session.get("role") != "Admin":

            flash("Administrator access required.", "danger")

            return redirect(url_for("dashboard"))

        return view(*args, **kwargs)

    return wrapped_view

# ==========================================================
# VALIDATIONS
# ==========================================================

def valid_account_number(account_number):
    """Validate a Nigerian account number."""
    return account_number.isdigit() and len(account_number) == 10


def valid_amount(amount):
    """Ensure transaction amount is greater than zero."""
    try:
        return float(amount) > 0
    except (ValueError, TypeError):
        return False


def valid_pin(pin):
    """Transaction PIN must be exactly four digits."""
    return pin.isdigit() and len(pin) == 4

# ==========================================================
# TRANSACTION FEE
# ==========================================================

def calculate_transaction_fee(amount):
    """
    Example POS fee calculation.
    Replace this logic with your business rules.
    """
    amount = float(amount)

    if amount <= 5000:
        return 10.00
    elif amount <= 20000:
        return 25.00
    elif amount <= 100000:
        return 50.00
    else:
        return 100.00