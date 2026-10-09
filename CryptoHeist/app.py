import os
import random
import sqlite3
import time
import threading
from datetime import datetime
from functools import wraps

from flask import (Flask, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "wt_crypto_s3cr3t_2024")

DATABASE = "trading.db"
FLAG = "CyberHorizon{r4c3_c0nd1t10n_m4st3r_tr4b3ls1}"

_rate_limit_store = {}
_rate_limit_lock = threading.Lock()

# ─── Database ────────────────────────────────────────────────────────────────

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            balance     REAL    NOT NULL DEFAULT 5.0,
            created_at  TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS coins (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol      TEXT    UNIQUE NOT NULL,
            name        TEXT    NOT NULL,
            price       REAL    NOT NULL,
            description TEXT,
            icon        TEXT
        );

        CREATE TABLE IF NOT EXISTS cart (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            coin_id     INTEGER NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(coin_id) REFERENCES coins(id)
        );

        CREATE TABLE IF NOT EXISTS promo_codes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    UNIQUE NOT NULL,
            discount    REAL    NOT NULL DEFAULT 0.05,
            active      INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS promo_usage (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            promo_id    INTEGER NOT NULL,
            used_at     TEXT    NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(promo_id) REFERENCES promo_codes(id)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            coin_id     INTEGER NOT NULL,
            quantity    INTEGER NOT NULL,
            price_paid  REAL    NOT NULL,
            discount    REAL    NOT NULL DEFAULT 0.0,
            purchased_at TEXT   NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(coin_id) REFERENCES coins(id)
        );

        CREATE TABLE IF NOT EXISTS cart_session (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER UNIQUE NOT NULL,
            total_discount  REAL    NOT NULL DEFAULT 0.0,
            last_updated    TEXT    NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)

    # Seed coins
    coins = [
        ("BTC",  "Bitcoin",       0.85,  "The original cryptocurrency.",       "₿"),
        ("ETH",  "Ethereum",      0.40,  "Smart contract platform.",           "Ξ"),
        ("SOL",  "Solana",        0.25,  "High-performance blockchain.",       "◎"),
        ("XRP",  "Ripple",        0.15,  "Fast cross-border payments.",        "✕"),
        ("DOGE", "Dogecoin",      0.10,  "The meme coin that started it all.", "Ð"),
        ("ADA",  "Cardano",       0.20,  "Proof-of-stake pioneer.",            "₳"),
        ("AVAX", "Avalanche",     0.30,  "Blazing fast consensus.",            "🔺"),
        ("FLAG", "FLAG Token",  1000.00, "Ultra-rare governance token. Only Walid knows what it unlocks.", "🚩"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO coins (symbol, name, price, description, icon) VALUES (?,?,?,?,?)",
        coins,
    )

    # Seed promo codes (NOT visible in the UI — discoverable via /backup/)
    promos = [
        ("WALID2024",   0.05),
        ("CRYPTO5OFF",  0.05),
        ("TRABELSI_VIP", 0.05),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO promo_codes (code, discount) VALUES (?,?)",
        promos,
    )

    db.commit()
    db.close()


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def current_user():
    if "user_id" not in session:
        return None
    return get_db().execute(
        "SELECT * FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# ─── Rate limiting (basic, bypassable with concurrency) ──────────────────────

def rate_limit(max_per_second=3):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            uid = session.get("user_id", request.remote_addr)
            key = f"{uid}:{f.__name__}"
            now = time.time()
            with _rate_limit_lock:
                timestamps = _rate_limit_store.get(key, [])
                timestamps = [t for t in timestamps if now - t < 1.0]
                if len(timestamps) >= max_per_second:
                    return jsonify({"error": "Rate limit exceeded. Slow down."}), 429
                timestamps.append(now)
                _rate_limit_store[key] = timestamps
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─── Routes: Auth ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("market"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        if not username or not password:
            flash("All fields required.", "danger")
            return render_template("register.html")
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            flash("Username already taken.", "danger")
            return render_template("register.html")
        db.execute(
            "INSERT INTO users (username, password, balance, created_at) VALUES (?,?,?,?)",
            (username, generate_password_hash(password), 5.0, datetime.utcnow().isoformat()),
        )
        db.commit()
        flash("Account created! You start with $5.00 in your wallet.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not user or not check_password_hash(user["password"], password):
            flash("Invalid credentials.", "danger")
            return render_template("login.html")
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash(f"Welcome back, {username}!", "success")
        return redirect(url_for("market"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))


# ─── Routes: Market ───────────────────────────────────────────────────────────

@app.route("/market")
@login_required
def market():
    db = get_db()
    coins = db.execute("SELECT * FROM coins ORDER BY price ASC").fetchall()
    user = current_user()
    return render_template("market.html", coins=coins, user=user)


# ─── Routes: Cart ─────────────────────────────────────────────────────────────

@app.route("/cart")
@login_required
def cart():
    db = get_db()
    user = current_user()
    items = db.execute(
        """SELECT cart.id, cart.quantity, coins.symbol, coins.name,
                  coins.price, coins.icon,
                  (cart.quantity * coins.price) as subtotal
           FROM cart
           JOIN coins ON coins.id = cart.coin_id
           WHERE cart.user_id = ?""",
        (session["user_id"],),
    ).fetchall()

    cart_state = db.execute(
        "SELECT total_discount FROM cart_session WHERE user_id = ?",
        (session["user_id"],),
    ).fetchone()

    raw_total = sum(row["subtotal"] for row in items)
    discount_pct = cart_state["total_discount"] if cart_state else 0.0
    discounted_total = raw_total * (1 - discount_pct)

    return render_template(
        "cart.html",
        items=items,
        user=user,
        raw_total=raw_total,
        discount_pct=discount_pct * 100,
        discounted_total=discounted_total,
    )


@app.route("/cart/add", methods=["POST"])
@login_required
def add_to_cart():
    coin_id = request.form.get("coin_id")
    db = get_db()
    coin = db.execute("SELECT * FROM coins WHERE id = ?", (coin_id,)).fetchone()
    if not coin:
        flash("Coin not found.", "danger")
        return redirect(url_for("market"))
    existing = db.execute(
        "SELECT id, quantity FROM cart WHERE user_id = ? AND coin_id = ?",
        (session["user_id"], coin_id),
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE id = ?",
            (existing["id"],),
        )
    else:
        db.execute(
            "INSERT INTO cart (user_id, coin_id, quantity) VALUES (?,?,1)",
            (session["user_id"], coin_id),
        )
    db.commit()
    flash(f"{coin['name']} added to cart.", "success")
    return redirect(url_for("market"))


@app.route("/cart/remove/<int:cart_id>", methods=["POST"])
@login_required
def remove_from_cart(cart_id):
    db = get_db()
    db.execute(
        "DELETE FROM cart WHERE id = ? AND user_id = ?",
        (cart_id, session["user_id"]),
    )
    db.commit()
    flash("Item removed.", "info")
    return redirect(url_for("cart"))


# ─── Routes: Promo Code (VULNERABLE ENDPOINT) ────────────────────────────────

@app.route("/cart/apply_promo", methods=["POST"])
@login_required
@rate_limit(max_per_second=7)
def apply_promo():
    code = request.form.get("promo_code", "").strip().upper()
    user_id = session["user_id"]
    db = get_db()

    if not code:
        return jsonify({"error": "No promo code provided."}), 400

    # Validate the code exists and is active
    promo = db.execute(
        "SELECT * FROM promo_codes WHERE code = ? AND active = 1", (code,)
    ).fetchone()
    if not promo:
        return jsonify({"error": "Invalid or expired promo code."}), 400

    # ── Intentionally flawed check ──────────────────────────────────────────
    # This checks the session flag AND the database — but both checks happen
    # before the write, leaving a race window between concurrent requests.
    if session.get("promo_applied") == code:
        return jsonify({"error": "You have already applied this promo code."}), 400

    already_used = db.execute(
        "SELECT id FROM promo_usage WHERE user_id = ? AND promo_id = ?",
        (user_id, promo["id"]),
    ).fetchone()
    if already_used:
        return jsonify({"error": "Promo code already used."}), 400

    # ── Artificial processing delay (creates the race window) ───────────────
    time.sleep(random.uniform(0.2, 0.6))

    # Apply discount to shared cart_session state
    existing_state = db.execute(
        "SELECT * FROM cart_session WHERE user_id = ?", (user_id,)
    ).fetchone()

    discount_rate = promo["discount"]

    if existing_state:
        new_discount = existing_state["total_discount"] + discount_rate
        db.execute(
            "UPDATE cart_session SET total_discount = ?, last_updated = ? WHERE user_id = ?",
            (new_discount, datetime.utcnow().isoformat(), user_id),
        )
    else:
        db.execute(
            "INSERT INTO cart_session (user_id, total_discount, last_updated) VALUES (?,?,?)",
            (user_id, discount_rate, datetime.utcnow().isoformat()),
        )

    # Record usage (too late — race already won)
    db.execute(
        "INSERT INTO promo_usage (user_id, promo_id, used_at) VALUES (?,?,?)",
        (user_id, promo["id"], datetime.utcnow().isoformat()),
    )
    db.commit()

    # Set the session flag after the write (not before — another mistake)
    session["promo_applied"] = code

    # Calculate current totals for response
    items = db.execute(
        """SELECT SUM(cart.quantity * coins.price) as raw_total
           FROM cart JOIN coins ON coins.id = cart.coin_id
           WHERE cart.user_id = ?""",
        (user_id,),
    ).fetchone()
    raw_total = items["raw_total"] or 0.0

    state = db.execute(
        "SELECT total_discount FROM cart_session WHERE user_id = ?", (user_id,)
    ).fetchone()
    total_discount = state["total_discount"] if state else 0.0
    final_total = raw_total * (1 - total_discount)

    return jsonify({
        "success": True,
        "message": f"Promo code applied! {discount_rate * 100:.0f}% discount added.",
        "discount_pct": round(total_discount * 100, 2),
        "raw_total": round(raw_total, 4),
        "final_total": round(final_total, 4),
    })


# ─── Routes: Checkout ─────────────────────────────────────────────────────────

@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    user_id = session["user_id"]
    db = get_db()
    user = current_user()

    items = db.execute(
        """SELECT cart.id, cart.quantity, cart.coin_id,
                  coins.symbol, coins.name, coins.price,
                  (cart.quantity * coins.price) as subtotal
           FROM cart
           JOIN coins ON coins.id = cart.coin_id
           WHERE cart.user_id = ?""",
        (user_id,),
    ).fetchall()

    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart"))

    cart_state = db.execute(
        "SELECT total_discount FROM cart_session WHERE user_id = ?", (user_id,)
    ).fetchone()

    raw_total = sum(row["subtotal"] for row in items)
    discount_pct = cart_state["total_discount"] if cart_state else 0.0
    final_total = raw_total * (1 - discount_pct)

    if user["balance"] < final_total:
        flash(
            f"Insufficient funds. You need ${final_total:.4f} but only have ${user['balance']:.4f}.",
            "danger",
        )
        return redirect(url_for("cart"))

    # Process purchase
    now = datetime.utcnow().isoformat()
    for item in items:
        item_price = item["price"] * item["quantity"] * (1 - discount_pct)
        db.execute(
            """INSERT INTO transactions
               (user_id, coin_id, quantity, price_paid, discount, purchased_at)
               VALUES (?,?,?,?,?,?)""",
            (user_id, item["coin_id"], item["quantity"],
             item_price, discount_pct, now),
        )

    db.execute(
        "UPDATE users SET balance = balance - ? WHERE id = ?",
        (final_total, user_id),
    )
    db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM cart_session WHERE user_id = ?", (user_id,))
    db.commit()

    session.pop("promo_applied", None)
    flash(
        f"Purchase successful! You spent ${final_total:.4f} (saved {discount_pct * 100:.1f}%).",
        "success",
    )
    return redirect(url_for("wallet"))


# ─── Routes: Wallet ───────────────────────────────────────────────────────────

@app.route("/wallet")
@login_required
def wallet():
    user_id = session["user_id"]
    db = get_db()
    user = current_user()

    txns = db.execute(
        """SELECT transactions.*, coins.symbol, coins.name, coins.icon
           FROM transactions
           JOIN coins ON coins.id = transactions.coin_id
           WHERE transactions.user_id = ?
           ORDER BY transactions.purchased_at DESC""",
        (user_id,),
    ).fetchall()

    owned_flags = [t for t in txns if t["symbol"] == "FLAG"]
    flag_value = FLAG if owned_flags else None

    return render_template("wallet.html", user=user, transactions=txns, flag=flag_value)


# ─── Hidden OSINT endpoint ────────────────────────────────────────────────────

@app.route("/backup/promo_codes.txt")
def exposed_promo_file():
    content = (
        "# Walid Trading Platform - Internal Promo Codes\n"
        "# Generated: 2024-01-15\n"
        "# DO NOT DISTRIBUTE\n\n"
        "WALID2024        = 5% discount\n"
        "CRYPTO5OFF       = 5% discount\n"
        "TRABELSI_VIP     = 5% discount (VIP customers only)\n\n"
        "# Note: Each code is single-use per account.\n"
        "# Contact admin@walid-trading.com for additional codes.\n"
    )
    from flask import Response
    return Response(content, mimetype="text/plain")


@app.route("/backup/")
def backup_index():
    from flask import Response
    html = """<!DOCTYPE html>
<html><head><title>Index of /backup/</title></head>
<body>
<h1>Index of /backup/</h1><hr>
<pre>
<a href="/backup/promo_codes.txt">promo_codes.txt</a>        2024-01-15 03:14    312
<a href="/backup/config_backup.py">config_backup.py</a>       2024-01-15 03:14    1.2K
</pre><hr></body></html>"""
    return Response(html, mimetype="text/html")


@app.route("/backup/config_backup.py")
def exposed_config():
    content = (
        '# Walid Trading Platform - Configuration Backup\n'
        '# This file should NOT be publicly accessible!\n\n'
        'DATABASE = "trading.db"\n'
        'SECRET_KEY = "wt_crypto_s3cr3t_2024"\n'
        'ADMIN_USER = "walid"\n'
        'ADMIN_PASS = "Tr@b3ls!2024"\n\n'
        '# Promo code discount rate\n'
        'PROMO_DISCOUNT = 0.05  # 5 percent\n\n'
        '# Payment processing delay (seconds) - artificial throttle\n'
        'PAYMENT_DELAY_MIN = 0.2\n'
        'PAYMENT_DELAY_MAX = 0.6\n'
    )
    from flask import Response
    return Response(content, mimetype="text/plain")


# ─── API: Cart state (for JS polling) ────────────────────────────────────────

@app.route("/api/cart/state")
@login_required
def cart_state_api():
    user_id = session["user_id"]
    db = get_db()
    items = db.execute(
        """SELECT SUM(cart.quantity * coins.price) as raw_total
           FROM cart JOIN coins ON coins.id = cart.coin_id
           WHERE cart.user_id = ?""",
        (user_id,),
    ).fetchone()
    raw_total = items["raw_total"] or 0.0
    state = db.execute(
        "SELECT total_discount FROM cart_session WHERE user_id = ?", (user_id,)
    ).fetchone()
    discount = state["total_discount"] if state else 0.0
    return jsonify({
        "raw_total": round(raw_total, 4),
        "discount_pct": round(discount * 100, 2),
        "final_total": round(raw_total * (1 - discount), 4),
    })


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
