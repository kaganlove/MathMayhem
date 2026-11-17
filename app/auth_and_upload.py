"""One-click YouTube OAuth listener & Episode 001 uploader."""

from __future__ import annotations

import http.server
import socketserver
import threading
import urllib.parse
from pathlib import Path
from app.youtube_uploader import (
    CLIENT_SECRETS_FILE,
    TOKEN_FILE,
    exchange_code_for_token,
    get_authorization_url,
    upload_youtube_short,
)

PORT = 8888
auth_code_received = threading.Event()
received_code = None

class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global received_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            received_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px; background: #f0fdf4;">
                <h1 style="color: #166534;">🎉 YouTube Authorization Successful!</h1>
                <p style="font-size: 18px; color: #15803d;">Math Mishaps has been connected. You can return to chat — the upload is starting!</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
            auth_code_received.set()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No authorization code found in request.")

    def log_message(self, format, *args):
        pass  # Suppress default server noise


def start_server():
    server = socketserver.TCPServer(("127.0.0.1", PORT), OAuthCallbackHandler)
    server.timeout = 1.0
    while not auth_code_received.is_set():
        server.handle_request()
    server.server_close()


def do_upload():
    video_path = Path("renders/episodes/ep001_directors_cut_master_1080x1920.mp4")

    # High-CTR, algorithm-optimized title and description
    title = "NEVER Divide By Zero! 😱💥 (What Actually Happens) #Shorts"
    description = (
        "What happens when you divide by zero on a giant pedestal calculator? 😱💥\n\n"
        "Episode 001 of Math Mishaps (formerly Math Mayhem): 'Never Divide by Zero'.\n\n"
        "🔬 The Mathematical Truth (Validated via SymPy):\n"
        "• 10 ÷ 2 = 5\n"
        "• 10 ÷ 1 = 10\n"
        "• 10 ÷ 0 = UNDEFINED (Division by zero is impossible in standard arithmetic!)\n"
        "• 0 ÷ 0 = INDETERMINATE (The forbidden cliffhanger!)\n\n"
        "100% procedurally animated in Python with Cairo. Pure silent visual pantomime.\n\n"
        "Drop your favorite math paradox in the comments! 👇\n\n"
        "#MathMishaps #MathMayhem #Shorts #Animation #Math #DivideByZero #STEM #Science #Cartoon #IndieAnimation"
    )

    tags = [
        "Math Mishaps",
        "Math Mayhem",
        "Never Divide by Zero",
        "division by zero",
        "zero divided by zero",
        "0 divided by 0",
        "math animation",
        "cairo animation",
        "math shorts",
        "calculus",
        "indeterminate form",
        "funny math",
        "stem animation",
        "shorts",
        "comedy animation",
        "stick figure animation",
        "educational shorts",
        "math paradox",
    ]

    print("Beginning YouTube upload...")
    result = upload_youtube_short(
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        category_id="27",  # Education
        privacy_status="public",
    )
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--code":
        code_input = sys.argv[2]
        print(f"Exchanging provided code...")
        exchange_code_for_token(code_input)
        res = do_upload()
        print(f"SUCCESS: {res['shorts_url']}")
        sys.exit(0)

    if TOKEN_FILE.exists():
        print("Existing token.json found. Proceeding with upload...")
        res = do_upload()
        print(f"SUCCESS: {res['shorts_url']}")
    else:
        auth_url = get_authorization_url()
        print(f"AUTH_URL_START\n{auth_url}\nAUTH_URL_END", flush=True)
        print(f"Waiting for callback on http://localhost:{PORT}/ ...", flush=True)
        t = threading.Thread(target=start_server)
        t.start()
        # Wait up to 30 minutes for authorization
        if auth_code_received.wait(timeout=1800):
            print("Authorization code received! Exchanging token...")
            exchange_code_for_token(received_code)
            res = do_upload()
            print(f"SUCCESS: {res['shorts_url']}")
        else:
            print("Timed out waiting for browser callback.")
