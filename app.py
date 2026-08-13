from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)

DATABASE = "pos_transaction.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'Agent',
            status TEXT DEFAULT 'Active',
            wallet_balance REAL DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # Create default admin account
    admin = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if admin is None:
        password = generate_password_hash("admin123")

        conn.execute("""
            INSERT INTO users
            (
                full_name,
                username,
                email,
                phone,
                password,
                role,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Administrator",
            "admin",
            "admin@example.com",
            "08000000000",
            password,
            "Admin",
            "Active"
        ))

        conn.commit()

    conn.close()


@app.route("/")
def index():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not username or not email or not password:
            flash("Please complete all required fields.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        conn = get_db()

        existing_username = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_username:
            conn.close()
            flash("Username already exists.", "danger")
            return render_template("register.html")

        existing_email = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_email:
            conn.close()
            flash("Email already exists.", "danger")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        conn.execute("""
            INSERT INTO users
            (
                full_name,
                username,
                email,
                phone,
                password,
                role,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            full_name,
            username,
            email,
            phone,
            hashed_password,
            "Agent",
            "Active"
        ))

        conn.commit()
        conn.close()

        flash("Registration successful. Please login.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Enter username and password.", "danger")
            return render_template("login.html")

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user is None:
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

        if user["status"] != "Active":
            flash("Your account is not active.", "danger")
            return render_template("login.html")

        if not check_password_hash(user["password"], password):
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

        session.clear()

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["full_name"] = user["full_name"]
        session["role"] = user["role"]

        flash("Login successful.", "success")

        if user["role"] == "Admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    if user is None:
        session.clear()
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        user=user
    )


@app.route("/admin_dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        flash("Administrator access required.", "danger")
        return redirect(url_for("dashboard"))

    conn = get_db()

    users = conn.execute("""
        SELECT
            id,
            full_name,
            username,
            email,
            phone,
            role,
            status,
            wallet_balance,
            created_at
        FROM users
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        users=users
    )


@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))


@app.route("/health")
def health():

    return "POS Transaction Web App is running successfully."


@app.errorhandler(404)
def page_not_found(error):

    try:
        return render_template("404.html"), 404
    except Exception:
        return "404 - Page not found", 404


@app.errorhandler(500)
def internal_error(error):

    try:
        return render_template("500.html"), 500
    except Exception:
        return "500 - Internal server error", 500


# Initialize database
init_db()


# Start application
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=False
    )