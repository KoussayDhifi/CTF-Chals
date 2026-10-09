"""
FST Multiverse Communication Portal - CTF Challenge
Server-Side Template Injection (SSTI) via Mako Templates

WARNING: This application is intentionally vulnerable for CTF purposes.
DO NOT deploy in production!
"""

from flask import Flask, request
from mako.template import Template
import re
import builtins
import os
import io
import sys

app = Flask(__name__)

# ============================================
# Runtime Sandbox (applied to template module only)
# ============================================

MAX_LENGTH = 120
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLAG_FILE = os.path.abspath(os.path.join(BASE_DIR, 'flag.txt'))

_ALLOW_READ_PREFIXES = {
    os.path.normcase(os.path.abspath(getattr(sys, 'base_prefix', sys.prefix))),
    os.path.normcase(os.path.abspath(sys.prefix)),
    os.path.normcase(os.path.abspath(getattr(sys, 'exec_prefix', sys.prefix))),
}

_original_open = builtins.open


def _canonicalize_requested_path(file_name):
    path_text = str(file_name)
    if not os.path.isabs(path_text):
        path_text = os.path.join(BASE_DIR, path_text)
    return os.path.abspath(path_text)


def sandboxed_open(file, mode='r', *args, **kwargs):
    requested_path = _canonicalize_requested_path(file)

    requested_norm = os.path.normcase(requested_path)

    if any(marker in mode for marker in ('w', 'a', 'x', '+')):
        raise PermissionError('Write access denied')

    if requested_path == FLAG_FILE:
        return _original_open(FLAG_FILE, mode, *args, **kwargs)

    # Allow Python + site-packages to function (Werkzeug/Flask read dist-info metadata).
    if any(requested_norm.startswith(prefix + os.sep) or requested_norm == prefix for prefix in _ALLOW_READ_PREFIXES):
        return _original_open(requested_path, mode, *args, **kwargs)

    raise PermissionError('Access denied: only flag.txt is accessible')


def sandboxed_import(*args, **kwargs):
    raise PermissionError('Import is disabled in this sandbox')


def build_template_builtins():
    """Return a builtins dict used only for the Mako template module."""
    base = dict(builtins.__dict__)
    base['open'] = sandboxed_open
    base['__import__'] = sandboxed_import
    return base


# Apply sandbox globally for file reads, but with an allowlist so the app stack still works.
builtins.open = sandboxed_open
io.open = sandboxed_open

# ============================================
# Input Validation
# ============================================

def sanitize_message(message):
    """
    Basic validation while intentionally keeping SSTI behavior for CTF.
    """
    
    # Length check
    if len(message) > MAX_LENGTH:
        return None, "Transmission too long for multiverse relay (max 120 chars)"

    # Allow printable text only to avoid control-character abuse
    if not re.fullmatch(r"[\x20-\x7E\t\n\r]*", message):
        return None, "Unsupported control characters detected"

    return message, None

# ============================================
# Mako Template (Vulnerable Rendering)
# ============================================

PORTAL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FST Multiverse Portal</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='75' font-size='75'>🌌</text></svg>">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 50%, #0a0a2a 100%);
            min-height: 100vh;
            color: #e0e0ff;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 2.5em;
            color: #00d4ff;
            text-shadow: 0 0 20px #00d4ff, 0 0 40px #0088ff;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            color: #8888cc;
            font-size: 0.9em;
            letter-spacing: 2px;
        }
        
        .story-section {
            background: rgba(20, 20, 50, 0.8);
            border: 1px solid #3333aa;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 0 15px rgba(0, 100, 255, 0.2);
        }
        
        .story-section h2 {
            color: #ff66ff;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .story-section p {
            line-height: 1.8;
            color: #aaaadd;
        }
        
        .form-section {
            background: rgba(30, 30, 60, 0.9);
            border: 2px solid #00d4ff;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
        }
        
        .form-section h3 {
            color: #00d4ff;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .form-section input[type="text"] {
            width: 100%;
            padding: 15px;
            background: #0a0a1a;
            border: 1px solid #4444aa;
            border-radius: 8px;
            color: #00ff88;
            font-family: 'Courier New', monospace;
            font-size: 1em;
            margin-bottom: 15px;
        }
        
        .form-section input[type="text"]:focus {
            outline: none;
            border-color: #00d4ff;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }
        
        .form-section button {
            background: linear-gradient(135deg, #00d4ff, #0088ff);
            color: #000;
            border: none;
            padding: 15px 40px;
            border-radius: 8px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 2px;
            transition: all 0.3s;
        }
        
        .form-section button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 212, 255, 0.5);
        }
        
        .output-section {
            background: rgba(10, 10, 30, 0.95);
            border: 1px solid #22aa22;
            border-radius: 10px;
            padding: 25px;
            font-family: 'Courier New', monospace;
        }
        
        .output-section .log-header {
            color: #22ff22;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .output-section .log-text {
            color: #88aa88;
            margin-bottom: 20px;
            font-style: italic;
        }
        
        .rendered-message {
            background: #000;
            padding: 20px;
            border-radius: 5px;
            border-left: 3px solid #00ff88;
            color: #00ff88;
            word-wrap: break-word;
        }
        
        .error-message {
            background: rgba(255, 50, 50, 0.2);
            border: 1px solid #ff4444;
            padding: 15px;
            border-radius: 5px;
            color: #ff8888;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #555588;
            font-size: 0.8em;
        }
        
        .badge {
            display: inline-block;
            background: rgba(255, 100, 255, 0.2);
            border: 1px solid #ff66ff;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.7em;
            color: #ff66ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>FST Multiverse Portal</h1>
            <p class="subtitle">Experimental Interdimensional Messaging System – Research Build</p>
            <span class="badge">Faculty of Sciences of Tunis</span>
        </header>
        
        <section class="story-section">
            <h2>📡 Research Initiative #7749</h2>
            <p>
                After years of theoretical work, FST's Quantum Computing Lab has successfully 
                established contact with parallel universes. Our experimental <strong>
                Interdimensional Renderer</strong> allows messages to be transmitted to 
                your alternate-universe counterpart.
            </p>
            <p style="margin-top: 15px; color: #ff8866;">
                ⚠️ WARNING: Strange glitches have been reported. The rendering engine, built by 
                our top CS students, appears to have some... instabilities. Security team is 
                investigating.
            </p>
        </section>
        
        <section class="form-section">
            <h3>📨 Transmit Your Message</h3>
            <form method="POST" action="/">
                <input 
                    type="text" 
                    name="message" 
                    placeholder="Enter a message for your alternate-universe self…"
                    autocomplete="off"
                    maxlength="120"
                >
                <button type="submit">⚡ Transmit</button>
            </form>
        </section>
        
        % if rendered_output is not None:
        <section class="output-section">
            <div class="log-header">🛰 Transmission Log</div>
            <p class="log-text">
                "Your message has been encoded and reflected through the Multiverse Node…"
            </p>
            <div class="rendered-message">
                <strong>Rendered Message:</strong><br><br>
                ${rendered_output}
            </div>
        </section>
        % endif
        
        % if error_message is not None:
        <section class="output-section">
            <div class="error-message">
                ❌ Transmission Failed: ${error_message}
            </div>
        </section>
        % endif
        
        <footer class="footer">
            <p>FST Research Division • Quantum Computing Lab</p>
            <p>MIR Engine v0.3-beta • "Rendering the impossible"</p>
        </footer>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def portal():
    rendered_output = None
    error_message = None
    
    if request.method == 'POST':
        user_message = request.form.get('message', '')
        
        if user_message:
            # Apply "sanitization"
            sanitized, error = sanitize_message(user_message)
            
            if error:
                error_message = error
            else:
                try:
                    vulnerable_template = f"""
                    <span class="user-msg">{sanitized}</span>
                    """

                    inner_template = Template(vulnerable_template)
                    # Critical: sandbox only the template module's builtins,
                    # so the server runtime (Flask/Werkzeug) keeps working.
                    inner_template.module.__dict__['__builtins__'] = build_template_builtins()
                    rendered_output = inner_template.render()
                except Exception:
                    error_message = "Dimensional instability detected. Check your transmission format."
    
    # Render the main page template
    main_template = Template(PORTAL_TEMPLATE)
    return main_template.render(rendered_output=rendered_output, error_message=error_message)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
