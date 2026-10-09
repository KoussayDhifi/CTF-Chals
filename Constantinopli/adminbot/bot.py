import sqlite3
import time
from playwright.sync_api import sync_playwright
import os
from urllib.parse import urlparse

DB = "messages.db"
VISIT_DELAY = 2
CYCLE_DELAY = 10
PAGE_TIMEOUT = 5000

FLAG = open("flag.txt").read().strip()


def init_db():
    conn = sqlite3.connect(DB)
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stolen(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            data TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created")
    conn.commit()
    conn.close()


def get_urls():
    init_db()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT url FROM messages")
    rows = cur.fetchall()
    print(f"Fetched URLs: {rows}")
    conn.close()
    return rows


# ------------------- URL Verification -------------------
def load_allowed_base():
    """Read allowed base URL from url.txt and parse it"""
    with open("url.txt", "r") as f:
        base = f.read().strip()
        if not base:
            raise Exception("url.txt is empty")
        parsed = urlparse(base)
        return {
            "scheme": parsed.scheme,
            "hostname": parsed.hostname,
            "port": parsed.port
        }


def is_allowed_url(url: str, allowed_base: dict) -> bool:
    """Check if a given URL matches the allowed base URL"""
    try:
        parsed = urlparse(url.strip())
        # Compare scheme, hostname, and port
        if parsed.scheme != allowed_base["scheme"]:
            return False
        if parsed.hostname != allowed_base["hostname"]:
            return False
        if parsed.port != allowed_base["port"]:
            return False
        return True
    except Exception:
        return False
# --------------------------------------------------------


def main():
    allowed_base = load_allowed_base()
    print(f"[+] Allowed base URL: {allowed_base}")
    hostname = allowed_base["hostname"] or "localhost"
    print(f"[+] Admin bot will only visit URLs under: {hostname}")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-popup-blocking",
                "--disable-notifications",
                "--disable-infobars",
                "--no-sandbox",
            ]
        )

        print("[+] Admin bot started")

        while True:
            urls = get_urls()
            print("DB absolute path bot:", os.path.abspath(DB))

            for row in urls:
                url = row["url"]

                # Verify base URL before visiting
                if not is_allowed_url(url, allowed_base):
                    print(f"[!] Blocked URL (invalid base): {url}")
                    continue


                context = browser.new_context()
                page = context.new_page()
                context.add_cookies([
                    {
                        "name": "session",
                        "value": "eyJwaGFzZVR3byI6IkhoTjJRN09qZGJTY3FkbjVtTVNSWVBjdEpDalhnUkQySnVlRmViIn0.aXx-qA.kGAwvagM5TxIupQu7e99PDj3uKE",
                        "domain": hostname,
                        "path": "/",
                        "httpOnly": True,
                        "secure": False,
                        "sameSite": "Lax"
                    },
                    {
                        "name": "FLAG",
                        "value": FLAG,
                        "domain": hostname,
                        "path": "/",
                        "httpOnly": False,   # MUST be false for XSS
                        "secure": False,
                        "sameSite": "Lax"
                    }
                ])

                # Kill alert(), confirm(), prompt()
                page.on("dialog", lambda d: d.dismiss())

                try:
                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=PAGE_TIMEOUT
                    )
                    page.wait_for_timeout(VISIT_DELAY * 1000)
                except Exception as e:
                    print(f"[!] Error visiting {url}: {e}")

                context.close()

            time.sleep(CYCLE_DELAY)


if __name__ == "__main__":
    main()
