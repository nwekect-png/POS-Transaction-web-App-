"""
reports.py
Reports Blueprint for POS Transaction Web App
"""

import csv
from datetime import datetime, timedelta
from io import StringIO

from flask import (
    Blueprint,
    render_template,
    request,
    Response
)

from flask_login import login_required

reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)


# ==========================================================
# REPORT DASHBOARD
# ==========================================================

@reports_bp.route("/")
@login_required
def reports():

    from app import db, Transaction

    total_transactions = Transaction.query.count()

    total_deposit = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter_by(
        transaction_type="Deposit"
    ).scalar() or 0

    total_withdrawal = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter_by(
        transaction_type="Withdrawal"
    ).scalar() or 0

    total_sent = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter_by(
        transaction_type="Send Money"
    ).scalar() or 0

    total_received = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter_by(
        transaction_type="Receive Money"
    ).scalar() or 0

    return render_template(
        "reports.html",
        total_transactions=total_transactions,
        total_deposit=total_deposit,
        total_withdrawal=total_withdrawal,
        total_sent=total_sent,
        total_received=total_received
    )


# ==========================================================
# TRANSACTION HISTORY
# ==========================================================

@reports_bp.route("/transactions")
@login_required
def transactions():

    from app import Transaction

    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(
        "transaction_history.html",
        transactions=transactions
    )


# ==========================================================
# SUCCESSFUL TRANSFERS
# ==========================================================

@reports_bp.route("/successful")
@login_required
def successful_transfers():

    from app import Transaction

    transactions = Transaction.query.filter_by(
        status="Success"
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(
        "transfer_success_history.html",
        transactions=transactions
    )


# ==========================================================
# DAILY REPORT
# ==========================================================

@reports_bp.route("/daily")
@login_required
def daily_report():

    from app import Transaction

    today = datetime.utcnow().date()

    transactions = Transaction.query.filter(
        Transaction.created_at >= datetime.combine(
            today,
            datetime.min.time()
        )
    ).all()

    return render_template(
        "daily_report.html",
        transactions=transactions
    )


# ==========================================================
# WEEKLY REPORT
# ==========================================================

@reports_bp.route("/weekly")
@login_required
def weekly_report():

    from app import Transaction

    start = datetime.utcnow() - timedelta(days=7)

    transactions = Transaction.query.filter(
        Transaction.created_at >= start
    ).all()

    return render_template(
        "weekly_report.html",
        transactions=transactions
    )


# ==========================================================
# MONTHLY REPORT
# ==========================================================

@reports_bp.route("/monthly")
@login_required
def monthly_report():

    from app import Transaction

    start = datetime.utcnow() - timedelta(days=30)

    transactions = Transaction.query.filter(
        Transaction.created_at >= start
    ).all()

    return render_template(
        "monthly_report.html",
        transactions=transactions
    )


# ==========================================================
# SEARCH TRANSACTIONS
# ==========================================================

@reports_bp.route("/search")
@login_required
def search():

    from app import Transaction

    keyword = request.args.get("q", "")

    transactions = Transaction.query.filter(

        (Transaction.sender_name.contains(keyword)) |

        (Transaction.receiver_name.contains(keyword)) |

        (Transaction.account_number.contains(keyword)) |

        (Transaction.transaction_reference.contains(keyword))

    ).all()

    return render_template(
        "transaction_history.html",
        transactions=transactions
    )


# ==========================================================
# EXPORT CSV
# ==========================================================

@reports_bp.route("/export")
@login_required
def export_csv():

    from app import Transaction

    output = StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Reference",
        "Type",
        "Sender",
        "Receiver",
        "Account",
        "Bank",
        "Amount",
        "Status",
        "Date"
    ])

    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).all()

    for t in transactions:

        writer.writerow([
            t.transaction_reference,
            t.transaction_type,
            t.sender_name,
            t.receiver_name,
            t.account_number,
            t.bank_name,
            t.amount,
            t.status,
            t.created_at
        ])

    return Response(

        output.getvalue(),

        mimetype="text/csv",

        headers={
            "Content-Disposition":
            "attachment; filename=transactions.csv"
        }
    )