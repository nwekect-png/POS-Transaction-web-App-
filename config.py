"""
config.py
Configuration settings for POS Transaction Web App
"""

import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ======================================================
    # Flask
    # ======================================================
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "change-this-secret-key-in-production"
    )

    # ======================================================
    # Database
    # ======================================================
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "pos_transaction.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ======================================================
    # Session
    # ======================================================
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Set to True only when using HTTPS
    SESSION_COOKIE_SECURE = False

    # ======================================================
    # Upload Folder
    # ======================================================
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB

    # ======================================================
    # POS Settings
    # ======================================================
    DEFAULT_CURRENCY = "NGN"

    MIN_TRANSACTION_AMOUNT = 100

    MAX_TRANSACTION_AMOUNT = 5000000

    DEFAULT_TRANSACTION_FEE = 10.00

    # ======================================================
    # Receipt
    # ======================================================
    RECEIPT_PREFIX = "RCPT"

    REFERENCE_PREFIX = "POS"

    # ======================================================
    # Pagination
    # ======================================================
    USERS_PER_PAGE = 20

    TRANSACTIONS_PER_PAGE = 20


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False

    SESSION_COOKIE_SECURE = True


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}