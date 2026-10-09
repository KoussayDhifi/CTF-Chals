from flask import Flask, session, render_template, request
import re
import secrets



TAG_REGEX = re.compile(
    r'^&lt;[^&]*(?:&[^;]+;[^&]*)*&gt;.*$',
    re.DOTALL
)


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
with open("flag.txt", "rt") as f:
    FLAG = f.read()

@app.route("/")
def home():

    if "nonce" not in session:
        session["nonce"] = secrets.token_hex(16)

    if request.args.get("message"):
        message = request.args.get("message")
        return render_template("home.html", message=message, nonce=session["nonce"])
    
    return render_template("home.html", nonce=session["nonce"])


@app.route("/activate-flag", methods=["POST"])
def activateFlag():
    
    data = request.get_json()
    print(data)
    message = data.get("message") if data else None
    print("received Message ", message)
    if not message or not TAG_REGEX.match(message) or "giveSecret" not in message:
        print(TAG_REGEX.match(message))
        return render_template("gotcha.html")

    nonce = request.headers.get("X-Nonce")
    if not nonce or nonce != session["nonce"]:
        return render_template("gotcha.html")
    else:
        session["solved"] = True
        print("FLAG ACTIVATED")
        return "SOLVED", 200
    
@app.route("/flag")
def flag():

    if session.get("solved") == True:
        session["solved"] = False
        return render_template("flag.html", FLAG=FLAG)
    
    else:
        return render_template("gotcha.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
