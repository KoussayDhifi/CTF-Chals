from flask import Flask, request, jsonify, render_template, session, redirect, url_for, Response
import sqlite3
import os
import time
app = Flask(__name__)
app.secret_key = 'sfjdklfjds3#$#$#%J#KLTE(EGJE)+'
PHASE_1 = "8w3DGDopTBFicw5WqFrM7OMnZ2QbDcq18zj2BU"
PHASE_2 = "HhN2Q7OjdbScqdn5mMSRYPctJCjXgRD2JueFeb"
def get_db():
    return sqlite3.connect("messages.db")

def init_database():
    # Remove existing database if present
    if os.path.exists('userssqli.db'):
        os.remove('userssqli.db')
        print("[*] Removed existing database")
    
    # Create new database
    conn = sqlite3.connect('userssqli.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    print("[+] Created users table")
    
    # Insert admin user (the flag/secret for the CTF)
    cursor.execute('''
        INSERT INTO users (username, password) 
        VALUES ('admin', 'Sup3r@S3c4etP@$$')
    ''')
    print("[+] Inserted admin user")
    
    # Insert some decoy users to make enumeration more interesting
    decoy_users = [
        ('Koussay', 'KoussayPassword123'),
        ('researcher', 'lab_password_123'),
        ('student', 'thesis2024!'),
        ('professor', 'AcademicKey99'),
    ]
    
    for user, pwd in decoy_users:
        cursor.execute('''
            INSERT INTO users (username, password) 
            VALUES (?, ?)
        ''', (user, pwd))
    print(f"[+] Inserted {len(decoy_users)} decoy users")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*50)
    print("  Database initialized successfully!")
    print("  Target: admin / Sup3r@S3c4etP@$$")
    print("="*50 + "\n")

def init_db():
    conn = sqlite3.connect("messages.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT NOT NULL
        )
    """)

    cur.execute(""" CREATE TABLE IF NOT EXISTS stolen(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    data TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    
    )
    """)
    print("Created")
    conn.commit()
    conn.close()



def insert_message(url):
    conn = get_db()
    
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO messages (url) VALUES (?)",
        (url,)
    )

    # check if insert worked
    if cur.rowcount == 1:
        print("Insert successful!")
    else:
        print("Insert failed!")

    conn.commit()
    conn.close()


def weak_filter(user_input):
    """
    VULNERABLE: Weak input filter that can be bypassed.
    This filter blocks obvious attack patterns but misses many alternatives.
    """
    input_lower = user_input.lower()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in input_lower:
            return False
    return True

def check_credentials(username, password):
    """
    VULNERABLE: Intentionally unsafe query for SQL injection training.
    Uses string concatenation to build SQL queries.
    """
    # Check weak filter first
    if not weak_filter(username):
        return False
    
    try:
        
        conn = sqlite3.connect('userssqli.db')
        cursor = conn.cursor()
        
        # VULNERABLE: Intentionally unsafe query for SQL injection training
        # Password is NOT filtered - this is where the injection happens
        # Using string concatenation makes this susceptible to SQL injection
        query = f"SELECT * FROM users WHERE username = 'Koussay' AND password = '{password}'"
        
        # Record start time for timing-based detection
        start_time = time.time()
        
        # Execute the vulnerable query
        print(f"[DEBUG] Query: {query}")  # Debug output
        cursor.execute(query)
        result = cursor.fetchall()
        print(f"[DEBUG] Result: {result}, Match: {len(result) > 0}")  # Debug output
        
        # Calculate execution time
        elapsed = time.time() - start_time
        
        conn.close()
        
        # VULNERABLE: Time-based delay when query matches
        # If a match is found (due to SQLi condition being true), add 5 second delay
        if len(result) > 0:
            time.sleep(5)
        
        return len(result) > 0
        
    except sqlite3.Error as e:
        # Never reveal SQL errors - silent failure
        print(f"[DEBUG] SQL Error: {e}")
        return False

BLOCKED_KEYWORDS = ['--', ';', '/*', '*/', 'sleep', 'benchmark']
NJWT = 46482973431748860932656569677219281036354002462226906790766516036022188034775087560167215966076058074751498106201452432307996128623981227421944141154133024615410078118240800714981242926529255575770962375716349051445137940445416867482921051511299534814728384653840008392145218849932903962165830767445277471349
eJWT = 65537
PJWT = 6817842285631786373689738091032949998283141659839217311794039086121280862895506141888765697039276389752814610648308767424581825793199356563962576982402241
QJWT = 6817842285631786373689738091032949998283141659839217311794039086121280862895506141888765697039276389752814610648308767424581825793199356563962576982455989
JWT = "WoobaloobaDubDub"

BLOG_POSTS = [
    {
        "id": 1,
        "title": "The Fracture of Creation",
        "snippet": "Before long time, there was unity. Then the veil was torn.",
        "content": (
            "In the beginning, everything was whole. When the fracture occurred, "
            "systems began to expose unintended paths. Some of these paths were "
            "never meant to be hidden — only ignored."
        )
    },
    {
        "id": 2,
        "title": "The Rise of Constantinople",
        "snippet": "The final stronghold guarding the portal between worlds.",
        "content": (
            "Constantinople stands as the last stronghold. While its gates appear "
            "sealed, internal services remain reachable for those who know the routes."
        )
    },
    {
        "id": 3,
        "title": "The King Beneath the City",
        "snippet": "Some rulers wear crowns. Others wear silence.",
        "content": (
            "The true ruler does not speak directly. Instead, messages sent to "
            "the endpoint /listener are received and processed on his behalf. "
            "Bug hunters may use this path as a webhook to receive sensitive data "
            "sent by the admin."
        )
    },
    {
        "id": 4,
        "title": "The Faculty of Science of Tunis",
        "snippet": "Scholars, or custodians of forbidden knowledge?",
        "content": (
            "Students are taught the art of responsible disclosure. "
            "If important data is obtained, it must be stored for later review. "
            "The application exposes a storage endpoint for this purpose."
        )
    },
    {
        "id": 5,
        "title": "The Portal and Its Price",
        "snippet": "Every crossing demands a sacrifice.",
        "content": (
            "Collected information does not persist unless explicitly stored. "
            "To save data, send it using the following format:\n\n"
            "/store/<yourUserNameOfTheWebhook>?data=<importantDataToStore>\n\n"
            "Each user has their own storage namespace."
        )
    },
    {
        "id": 6,
        "title": "The Listener",
        "snippet": "Even walls have ears.",
        "content": (
            "The /listener endpoint acts as a webhook. "
            "It is designed to receive messages sent by the admin or internal bots. "
            "Bug hunters are encouraged to monitor this endpoint carefully."
        )
    }
]


def sanatize(search):
    new_search = ""
    for char in search:
        if char == '"':
            new_search += "\\" + char
        else:
            new_search += char
    return new_search

def string_to_int(s: str) -> int:
    """Convert a string to an integer for RSA."""
    return int.from_bytes(s.encode('utf-8'), byteorder='big')

def int_to_string(i: int) -> str:
    """Convert an integer back to a string."""
    length = (i.bit_length() + 7) // 8
    return i.to_bytes(length, byteorder='big').decode('utf-8')

def rsa_encrypt(message: str, e: int, n: int) -> int:
    """Encrypt a string using RSA."""
    m = string_to_int(message)
    if m >= n:
        print(m)
        raise ValueError("Message too large for this modulus")
    return pow(m, e, n)  # m^e mod n

def rsa_decrypt(cipher: int, d: int, n: int) -> str:
    """Decrypt RSA ciphertext."""
    m = pow(cipher, d, n)
    return int_to_string(m)

@app.route('/', methods=['GET', 'POST'])
def loginSQLI():
    result_message = None
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # Check if exact credentials match admin/Sup3r@S3c4etP@$$
        if username == 'admin' and password == 'Sup3r@S3c4etP@$$':
            session['phaseOne'] = "8w3DGDopTBFicw5WqFrM7OMnZ2QbDcq18zj2BU"
            return redirect(url_for('hello'))
        
        # Check credentials (vulnerable function)
        is_valid = check_credentials(username, password)
        
        # Return different response based on credential validity
        if is_valid:
            result_message = "Right track!"
        else:
            result_message = "Invalid credentials"
    return render_template('loginSQL.html', result=result_message)

@app.route('/hello')
def hello():
    return render_template('hello.html')


@app.route('/phaseTwo/challenge')
def phaseTwo():
    if not session.get("phaseOne") or session.get("phaseOne") != PHASE_1:
        return redirect(url_for("loginSQLI"))
    key = request.args.get("key")
    if key and key == JWT:
        session["phaseTwo"] = "HhN2Q7OjdbScqdn5mMSRYPctJCjXgRD2JueFeb"
        return redirect(url_for("index"))

    encRyptedJWT = rsa_encrypt(JWT, eJWT, NJWT)
    return render_template('phaseTwo.html', NJWT=NJWT, eJWT=eJWT, JWT=encRyptedJWT)


@app.route('/thirdphase')
def index():
    if session.get("phaseTwo") and session.get("phaseTwo") == PHASE_2:
        search = request.args.get('search', '')
        if search:
            return render_template("index.html", posts=BLOG_POSTS, search=True)
        return render_template("index.html", posts=BLOG_POSTS, search=False)
    else:
        print("DB absolute path bot app:", os.path.abspath("messages.db"))
        return redirect(url_for("phaseTwo"))


@app.route('/thirdphase/search')
def view_post():

    if not session.get("phaseTwo") or session.get("phaseTwo") != PHASE_2:
        return redirect(url_for("phaseTwo"))

    search = request.args.get('search', '')

    if search:
        matched = []

        for post in BLOG_POSTS:
            if search.lower() in post["title"].lower() or search.lower() in post["content"].lower():
                matched.append({
                    "id": post["id"],
                    "title": post["title"],
                    "summary": post["snippet"]
                })

        new_search = sanatize(search)
        response = f'''
        {{"results": {matched},
            "searchTerm": "{new_search}"}}
        '''
        
        return Response(response, mimetype='application/json')

@app.route("/thirdphase/admin/message", methods=["POST", "GET"])
def sendMessage():
    if not session.get("phaseTwo") or session.get("phaseTwo") != PHASE_2:
        return redirect(url_for("phaseTwo"))
    if request.method == "POST":
        url = request.form.get("url", "")
        print(f"url: {url}")
        insert_message(url)

        return render_template("adminMessage.html", message="Sent")
        
    else:
        # Handle GET request
        return render_template("adminMessage.html")


@app.route("/thirdphase/listener")
def listener():
    if not session.get("phaseTwo") or session.get("phaseTwo") != PHASE_2:
        return redirect(url_for("phaseTwo"))
    
    conn = get_db()
    cur = conn.cursor()
    username = session.get("username")
    if not username:
        return redirect(url_for("login"))
    cur.execute(
        "SELECT data, timestamp FROM stolen WHERE username = ?",
        (username,)
    )
    entries = cur.fetchall()
    print(entries)
    return render_template("listener.html", entries=entries)

@app.route("/thirdphase/store/<username>")
def store(username):
    data = request.args.get("data", "")

    
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO stolen (username, data) VALUES (?, ?)",
        (username, data)
    )

    conn.commit()
    conn.close()

    return "", 204

@app.route("/thirdphase/register", methods=["GET", "POST"])
def register():
    if not session.get("phaseTwo") or session.get("phaseTwo") != PHASE_2:
        return redirect(url_for("phaseTwo"))
    if request.method == "POST":
        # store username + password (plaintext is fine for CTF)
        username = request.form.get("username")
        password = request.form.get("password")

        if username and password:
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/thirdphase/login", methods=["GET", "POST"])
def login():
    if not session.get("phaseTwo") or session.get("phaseTwo") != PHASE_2:
        return redirect(url_for("phaseTwo"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username and password:
            
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username, password)
            )
            user = cur.fetchone()
            if user:
                session["user_id"] = user[0]
                session["username"] = user[1]
                return redirect(url_for("listener"))
            else:
                return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")



if __name__ == '__main__':
    init_db()
    init_database()
    app.run(host='0.0.0.0', port=4999, debug=True)