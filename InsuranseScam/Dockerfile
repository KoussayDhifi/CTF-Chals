FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /flags && \
    echo "CyberHorizon{bl1nd_sqli_w1th_b1n4ry_s34rch_m4st3r}" > /flags/admin_flag.txt && \
    chmod 440 /flags/admin_flag.txt

RUN ADMIN_PASSWORD='cl@ims_d3ni3d_2024_#@#$%HI'

RUN python -c "import sqlite3; db=sqlite3.connect('/tmp/insuranse.db'); cur=db.cursor(); cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT \"user\", full_name TEXT, policy_number TEXT, secret_token TEXT)'); admin_token=__import__(\"hashlib\").sha256(b'horizon_internal_token_2024').hexdigest()[:24]; cur.execute('INSERT OR IGNORE INTO users (username,password,role,full_name,policy_number,secret_token) VALUES (?,?,?,?,?,?)',('admin','cl@ims_d3ni3d_2024_#@#$%HI','admin','System Administrator','ADM-0001',admin_token)); cur.executemany('INSERT OR IGNORE INTO users (username,password,role,full_name,policy_number,secret_token) VALUES (?,?,?,?,?,?)',[('jdoe','password123','user','John Doe','POL-4821',None),('msmith','sunshine99','user','Mary Smith','POL-3374',None),('rjohnson','football77','user','Robert Johnson','POL-9102',None)]); db.commit(); db.close()"
EXPOSE 5000

CMD ["python", "app.py"]