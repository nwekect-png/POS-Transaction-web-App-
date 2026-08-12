"""
transfer_service.py
Transfer Service for POS Transaction Web App
"""

from datetime import datetime
from werkzeug.security import check_password_hash


class TransferService:

    def __init__(self, db, User, Transaction):
        self.db = db
        self.User = User
        self.Transaction = Transaction

    # ==========================================
    # Generate Reference
    # ==========================================

    def generate_reference(self):
        import uuid
        return "POS-" + uuid.uuid4().hex[:12].upper()

    # ==========================================
    # Verify Transaction PIN
    # ==========================================

    def verify_pin(self, user, pin):

        if not user.transaction_pin:
            return False

        return check_password_hash(
            user.transaction_pin,
            pin
        )

    # ==========================================
    # Deposit
    # ==========================================

    def deposit(
        self,
        user,
        customer,
        account_number,
        bank_name,
        amount
    ):

        reference = self.generate_reference()

        user.wallet_balance += amount

        transaction = self.Transaction(
            transaction_reference=reference,
            sender_name=customer,
            receiver_name=customer,
            account_number=account_number,
            bank_name=bank_name,
            transaction_type="Deposit",
            amount=amount,
            description="Cash Deposit",
            status="Success",
            created_at=datetime.utcnow()
        )

        self.db.session.add(transaction)
        self.db.session.commit()

        return transaction

    # ==========================================
    # Withdrawal
    # ==========================================

    def withdraw(
        self,
        user,
        customer,
        account_number,
        bank_name,
        amount
    ):

        if user.wallet_balance < amount:
            raise ValueError("Insufficient wallet balance.")

        reference = self.generate_reference()

        user.wallet_balance -= amount

        transaction = self.Transaction(
            transaction_reference=reference,
            sender_name=customer,
            receiver_name=customer,
            account_number=account_number,
            bank_name=bank_name,
            transaction_type="Withdrawal",
            amount=amount,
            description="Cash Withdrawal",
            status="Success",
            created_at=datetime.utcnow()
        )

        self.db.session.add(transaction)
        self.db.session.commit()

        return transaction

    # ==========================================
    # Send Money
    # ==========================================

    def send_money(
        self,
        user,
        sender,
        receiver,
        account_number,
        bank_name,
        amount,
        narration=""
    ):

        if user.wallet_balance < amount:
            raise ValueError("Insufficient wallet balance.")

        reference = self.generate_reference()

        user.wallet_balance -= amount

        transaction = self.Transaction(
            transaction_reference=reference,
            sender_name=sender,
            receiver_name=receiver,
            account_number=account_number,
            bank_name=bank_name,
            transaction_type="Send Money",
            amount=amount,
            description=narration,
            status="Success",
            created_at=datetime.utcnow()
        )

        self.db.session.add(transaction)
        self.db.session.commit()

        return transaction

    # ==========================================
    # Receive Money
    # ==========================================

    def receive_money(
        self,
        user,
        sender,
        receiver,
        account_number,
        bank_name,
        amount,
        narration=""
    ):

        reference = self.generate_reference()

        user.wallet_balance += amount

        transaction = self.Transaction(
            transaction_reference=reference,
            sender_name=sender,
            receiver_name=receiver,
            account_number=account_number,
            bank_name=bank_name,
            transaction_type="Receive Money",
            amount=amount,
            description=narration,
            status="Success",
            created_at=datetime.utcnow()
        )

        self.db.session.add(transaction)
        self.db.session.commit()

        return transaction

    # ==========================================
    # Transaction History
    # ==========================================

    def get_transactions(self):

        return self.Transaction.query.order_by(
            self.Transaction.created_at.desc()
        ).all()

    # ==========================================
    # Transaction by Reference
    # ==========================================

    def get_transaction(self, reference):

        return self.Transaction.query.filter_by(
            transaction_reference=reference
        ).first()

    # ==========================================
    # Total Deposits
    # ==========================================

    def total_deposits(self):

        return self.Transaction.query.filter_by(
            transaction_type="Deposit"
        ).count()

    # ==========================================
    # Total Withdrawals
    # ==========================================

    def total_withdrawals(self):

        return self.Transaction.query.filter_by(
            transaction_type="Withdrawal"
        ).count()

    # ==========================================
    # Total Transfers
    # ==========================================

    def total_transfers(self):

        return self.Transaction.query.filter(
            self.Transaction.transaction_type.in_(
                ["Send Money", "Receive Money"]
            )
        ).count()