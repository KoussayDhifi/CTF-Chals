from flask import Flask, request, render_template, redirect, url_for, session, make_response
from bcrypt import hashpw, gensalt, checkpw
import sqlite3
import jwt
import datetime
from dotenv import load_dotenv
import os

# --------------------------------------------------
# Setup
# --------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret-for-ctf")

JWT_SECRET = os.getenv("SECRET_JWT")
print(JWT_SECRET)
# --------------------------------------------------
# Database
# --------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect("database.db", timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password BLOB,
        is_admin INTEGER
    )
    """)

    # Create admin if not exists
    admin = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if admin is None:
        admin_password = os.urandom(32).hex()  # strong & irrelevant
        hashed = hashpw(admin_password.encode(), gensalt())

        conn.execute(
            "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
            ("admin", hashed, 1)
        )
        conn.commit()

    return conn


def check_password_hash(stored_password, provided_password):
    return checkpw(provided_password.encode(), stored_password)

# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    token = request.cookies.get("Authorization")
    print(f"Token: {token}")
    is_admin = False
    print(f"Payload: {JWT_SECRET}")
    if token.startswith("Bearer "):
        try:
            payload = jwt.decode(
                token.split(" ")[1],
                JWT_SECRET,
                algorithms=["HS256"]
            )
            
            if payload.get("role") == "admin":
                is_admin = True
        except jwt.InvalidTokenError:
            print("Invalid token")
            pass

    # Admin sees normal admin page
    if is_admin:
        with open("flag.txt", "r") as f:
            flag = f.read().strip()
        return render_template("home.html", is_admin=True, flag=flag)

    # ---- LFI PART ----
    page = request.args.get("page")
    print(page)

    if page and (page.find("flag") != -1 or page.find("FLAG") != -1)    :
        content = "Hey hey hey what are you doing there? No flags for you! 🦫"
        
    else:
        try:
            with open(f"challenge/text/{page}", "r") as f:
                content = f.read()
        except Exception:
            content = "🦫 Beaver says: I couldn't find what you're looking for..."

    return render_template(
        "page.html",
        content=content
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db_connection()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user"] = user["username"]
            session["role"] = user["is_admin"]

            resp = make_response(redirect(url_for("index")))

            # Only admins get JWT
            if user["is_admin"] == 1:
                token = jwt.encode(
                    {
                        "user": user["username"],
                        "role": "admin",
                        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
                    },
                    JWT_SECRET,
                    algorithm="HS256"
                )
                resp.set_cookie("Authorization", f"Bearer {token}", httponly=True)
            
            else:
                token = jwt.encode(
                    {
                        "user": user["username"],
                        "role": "user",
                        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
                    },
                    JWT_SECRET,
                    algorithm="HS256"
                )
                resp.set_cookie("Authorization", f"Bearer {token}", httponly=True)

            return resp

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return "Username and password required", 400

        hashed = hashpw(password.encode(), gensalt())
        db = get_db_connection()

        try:
            db.execute(
                "INSERT INTO users (username, password, is_admin) VALUES (?, ?, 0)",
                (username, hashed)
            )
            db.commit()
        except sqlite3.IntegrityError:
            return "Username already exists", 400

        return redirect(url_for("login"))

    return render_template("register.html")




# --------------------------------------------------
# Run
# --------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
