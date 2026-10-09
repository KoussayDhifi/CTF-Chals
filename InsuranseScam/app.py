import sqlite3
import hashlib
import time
import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, g

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = '/tmp/insuranse.db'
FLAG_PATH = '/flags/admin_flag.txt'

# ─────────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────────

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    if os.path.exists(DATABASE):
        return
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            full_name TEXT,
            policy_number TEXT
        )
    ''')
    # Admin password stored as SHA-1
    admin_pass = os.environ.get('ADMIN_PASSWORD')
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password, role, full_name, policy_number) VALUES (?, ?, ?, ?, ?)",
        ('admin', admin_pass, 'admin', 'System Administrator', 'ADM-0001')
    )
    # Regular users
    users = [
        ('jdoe', hashlib.sha1(b'password123').hexdigest(), 'user', 'John Doe', 'POL-4821'),
        ('msmith', hashlib.sha1(b'sunshine99').hexdigest(), 'user', 'Mary Smith', 'POL-3374'),
        ('rjohnson', hashlib.sha1(b'football77').hexdigest(), 'user', 'Robert Johnson', 'POL-9102'),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO users (username, password, role, full_name, policy_number) VALUES (?, ?, ?, ?, ?)",
        users
    )
    db.commit()
    db.close()

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        time.sleep(random.uniform(0.2, 0.5))

        try:
            db = get_db()
            hashed_input = password if username == 'admin' else hashlib.sha1(password.encode()).hexdigest()
            # Parameterised query — immune to SQL injection
            cursor = db.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username, hashed_input)
            )
            user = cursor.fetchone()
        except Exception:
            error = 'Invalid credentials.'
            return render_template('login.html', error=error)

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            session['policy_number'] = user['policy_number']
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials.'

    return render_template('login.html', error=error)

@app.route('/policies', methods=['GET', 'POST'])
def policies():
    results = None
    error = None
    if request.method == 'POST':
        search = request.form.get('search', '')

        time.sleep(random.uniform(0.2, 0.5))

        # Input sanitized — blocking dangerous keywords
        blacklist = ['=', 'like', 'LIKE', 'drop', 'DROP', 'delete', 'DELETE']
        for item in blacklist:
            if item in search:
                error = 'Invalid search term.'
                return render_template('policies.html', results=None, error=error)

        try:
            db = get_db()
            # Search policies by policy number — safe, validated above
            query = "SELECT full_name, policy_number, role FROM users WHERE policy_number = '" + search + "'"
            cursor = db.execute(query)
            results = cursor.fetchall()
        except Exception:
            # Suppress errors
            results = []

    return render_template('policies.html', results=results, error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin'))
    return render_template('dashboard.html')

@app.route('/admin')
def admin():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    flag = '[FLAG FILE NOT FOUND]'
    try:
        with open(FLAG_PATH, 'r') as f:
            flag = f.read().strip()
    except Exception:
        pass
    return render_template('admin.html', flag=flag)

@app.route('/source')
def source():
    with open(__file__, 'r') as f:
        code = f.read()
    return render_template('source.html', code=code)

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
