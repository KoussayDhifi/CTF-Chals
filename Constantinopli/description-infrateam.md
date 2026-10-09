## 1️⃣ Infra team description (what they need to know & care about)

### **Challenge Overview (Infra View)**

This challenge is a **single web service** composed of three tightly coupled phases:

1. **SQL Injection (Authentication Bypass / Timing-based SQLi)**
2. **RSA Cryptography (Password recovery via weak RSA setup)**
3. **Reflected DOM XSS with Admin Bot (Cookie Exfiltration)**

The infrastructure must support:

* A **Flask web application**
* A **headless admin bot** (Playwright) acting as a victim
* **SQLite databases** (persistent during container runtime)
* Internal loopback access (`127.0.0.1`) between the bot and the app

---

### **Components**

#### 🧠 Web Application (Flask)

* Runs on a single exposed port (default: `5000`)
* Handles:

  * SQLi login logic (intentionally vulnerable)
  * RSA encryption challenge (weak modulus, leaked primes)
  * XSS injection surface (search endpoint)
  * Admin message submission
  * Webhook-style listener & storage endpoints

No reverse proxy is required.

---

#### 🤖 Admin Bot (Victim)

* Headless Chromium via **Playwright**
* Periodically:

  1. Reads URLs from `messages.db`
  2. Visits them with a **FLAG stored in a cookie**
* Cookie properties:

  * `httpOnly = False` (required for XSS)
  * Domain: `127.0.0.1`
* Visits run in isolated browser contexts
* Alerts/dialogs are auto‑dismissed to prevent blocking

**Important:**
The bot must run **inside the same container or network namespace** as the Flask app so that `127.0.0.1` resolves correctly.

---

### **Databases**

* `userssqli.db` → SQLi phase
* `messages.db` → admin bot queue + stolen data
* Databases are created at runtime
* Persistence is **not required across restarts**

---

### **Security Assumptions (Intentional Weaknesses)**

Infra should **not**:

* Add WAFs
* Sanitize inputs
* Enforce CSP
* Enable HttpOnly cookies
* Patch SQL injection or XSS

This is **by design**.


