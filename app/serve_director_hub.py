"""Persistent Server & Cloudflare Tunnel Runner for Math Mishaps Director Hub."""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

PORT = 8000
CLOUDFLARED_BIN = Path("tools/cloudflared.exe")


def run_hub():
    print(f"Starting Math Mishaps Studio Server on port {PORT}...", flush=True)

    # 1. Start Uvicorn
    uvicorn_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:create_app",
        "--factory",
        "--host",
        "0.0.0.0",
        "--port",
        str(PORT),
    ]
    server_proc = subprocess.Popen(
        uvicorn_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Wait for server to start
    time.sleep(2)

    # 2. Start Cloudflare Tunnel
    if not CLOUDFLARED_BIN.exists():
        print(f"Error: {CLOUDFLARED_BIN} not found.", flush=True)
        return

    print("Opening secure Cloudflare Tunnel to the internet...", flush=True)
    tunnel_cmd = [
        str(CLOUDFLARED_BIN),
        "tunnel",
        "--url",
        f"http://127.0.0.1:{PORT}",
    ]
    tunnel_proc = subprocess.Popen(
        tunnel_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    public_url = None
    start_time = time.time()
    while time.time() - start_time < 20:
        line = tunnel_proc.stderr.readline()
        if not line:
            time.sleep(0.1)
            continue
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match:
            public_url = match.group(0)
            break

    if public_url:
        director_url = f"{public_url}/director"
        Path("data").mkdir(exist_ok=True)
        Path("data/public_url.txt").write_text(director_url, encoding="utf-8")
        print("\n" + "=" * 60, flush=True)
        print("🎉 MATH MISHAPS DIRECTOR HUB IS ONLINE!", flush=True)
        print(f"👉 PERSISTENT MOBILE URL: {director_url}", flush=True)
        print("=" * 60 + "\n", flush=True)
    else:
        print("Warning: Could not extract Cloudflare tunnel URL within timeout.", flush=True)

    # Keep both running
    try:
        while True:
            time.sleep(1)
            if server_proc.poll() is not None:
                print("Server exited unexpectedly.")
                break
            if tunnel_proc.poll() is not None:
                print("Tunnel exited unexpectedly.")
                break
    except KeyboardInterrupt:
        pass
    finally:
        server_proc.terminate()
        tunnel_proc.terminate()


if __name__ == "__main__":
    run_hub()
