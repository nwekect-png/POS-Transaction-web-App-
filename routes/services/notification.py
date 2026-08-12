""
notification.py
Notification utilities for POS Transaction Web App
"""

import os
import random
from flask_mail import Mail, Message

mail = Mail()


# ==========================================
# Initialize Flask-Mail
# ==========================================

def init_mail(app):
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

    mail.init_app(app)


# ==========================================
# Send Email
# ==========================================

def send_email(recipient, subject, body):
    """
    Send an email notification.
    """

    try:
        msg = Message(
            subject=subject,
            recipients=[recipient]
        )

        msg.body = body

        mail.send(msg)

        return True

    except Exception as e:
        print("Email Error:", e)
        return False


# ==========================================
# Welcome Email
# ==========================================

def send_welcome_email(user):

    subject = "Welcome to POS Transaction System"

    body = f"""
Hello {user.full_name},

Your account has been created successfully.

Username: {user.username}

Thank you for choosing our POS platform.

Regards,
POS Transaction Team
"""

    return send_email(user.email, subject, body)


# ==========================================
# Deposit Notification
# ==========================================

def send_deposit_notification(user, amount):

    subject = "Deposit Successful"

    body = f"""
Dear {user.full_name},

A deposit of ₦{amount:,.2f}
has been credited to your wallet.

Available Balance:
₦{user.wallet_balance:,.2f}

Thank you.
"""

    return send_email(user.email, subject, body)


# ==========================================
# Withdrawal Notification
# ==========================================

def send_withdrawal_notification(user, amount):

    subject = "Cash Withdrawal"

    body = f"""
Dear {user.full_name},

Your withdrawal of ₦{amount:,.2f}
was successful.

Current Wallet Balance:
₦{user.wallet_balance:,.2f}
"""

    return send_email(user.email, subject, body)


# ==========================================
# Send Money Notification
# ==========================================

def send_transfer_notification(user, amount, recipient):

    subject = "Money Transfer Successful"

    body = f"""
Dear {user.full_name},

Your transfer of ₦{amount:,.2f}
to {recipient}
was successful.

Thank you for using our POS system.
"""

    return send_email(user.email, subject, body)


# ==========================================
# Receive Money Notification
# ==========================================

def receive_transfer_notification(user, amount, sender):

    subject = "Money Received"

    body = f"""
Dear {user.full_name},

You received ₦{amount:,.2f}
from {sender}.

Current Wallet Balance:
₦{user.wallet_balance:,.2f}
"""

    return send_email(user.email, subject, body)


# ==========================================
# Low Balance Alert
# ==========================================

def low_balance_notification(user):

    subject = "Low Wallet Balance"

    body = f"""
Dear {user.full_name},

Your wallet balance is low.

Current Balance:
₦{user.wallet_balance:,.2f}

Please fund your wallet.
"""

    return send_email(user.email, subject, body)


# ==========================================
# Password Reset Notification
# ==========================================

def password_reset_notification(user):

    subject = "Password Changed"

    body = f"""
Hello {user.full_name},

Your account password has been changed successfully.

If you did not perform this action,
please contact the administrator immediately.
"""

    return send_email(user.email, subject, body)


# ==========================================
# Generate OTP
# ==========================================

def generate_otp():
    return str(random.randint(100000, 999999))


# ==========================================
# Send OTP Email
# ==========================================

def send_otp(user):

    otp = generate_otp()

    subject = "Your One-Time Password (OTP)"

    body = f"""
Dear {user.full_name},

Your verification code is:

{otp}

This OTP expires in 5 minutes.

Do not share it with anyone.
"""

    send_email(user.email, subject, body)

    return otp


# ==========================================
# SMS Placeholder
# ==========================================

def send_sms(phone_number, message):
    """
    Replace this with your preferred SMS provider
    (e.g. Termii, Twilio, Africa's Talking).
    """

    print(f"SMS to {phone_number}: {message}")

    return True