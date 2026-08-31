#!/usr/bin/env python3
"""Export your FULL Naukri cookie string (including httpOnly cookies).

`document.cookie` CANNOT read Naukri's httpOnly session cookies — that's why the
easy console snippet was too short/empty. This tool instead connects to your
ALREADY-LOGGED-IN Chrome via Chrome DevTools Protocol (CDP) and reads the browser's
entire cookie jar for naukri.com, printing a ready-to-paste value.

NO HUNTING THROUGH THE NETWORK TAB / 200 REQUESTS.

HOW TO USE
----------
1) Install:  python -m pip install requests websocket-client
2) Start Chrome with remote debugging and log into Naukri:
     - Windows:  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" \
                    --remote-debugging-port=9222 --restore-last-session
     - macOS:    open -na "Google Chrome" --args --remote-debugging-port=9222
     - Linux:    google-chrome --remote-debugging-port=9222
    (If Chrome is already open, fully quit it first, then relaunch this way.)
3) In that Chrome window, log in to https://www.naukri.com
4) Run:  python export_naukri_cookie.py
5) Copy the printed NAUKRI_COOKIE value into .env, restart the backend.
"""
import json
import re
import urllib.request
import websocket

CDP_HTTP = "http://127.0.0.1:9222"
DOMAIN = ".naukri.com"


def get_targets():
    with urllib.request.urlopen(f"{CDP_HTTP}/json", timeout=5) as r:
        return json.loads(r.read().decode())


def main():
    targets = get_targets()
    page = next((t for t in targets if t.get("type") == "page" and "naukri" in (t.get("url") or "")), None)
    if not page:
        page = next((t for t in targets if t.get("type") == "page"), None)
    if not page:
        print("No browser tab found. Make sure Chrome was started with --remote-debugging-port=9222.")
        return

    ws_url = page["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url, timeout=10)
    mid = [0]

    def send(method, params=None):
        mid[0] += 1
        ws.send(json.dumps({"id": mid[0], "method": method, "params": params or {}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == mid[0]:
                return msg.get("result", {})

    # Ask the browser for ALL its cookies for the Naukri domain (incl. httpOnly).
    result = send("Network.getAllCookies")
    cookies = result.get("cookies", [])

    pairs = []
    for c in cookies:
        host = (c.get("domain") or "").lower()
        if "naukri" in host:
            pairs.append(f"{c.get('name')}={c.get('value')}")

    ws.close()

    if not pairs:
        print("No Naukri cookies found. Are you logged in at naukri.com? Retry after logging in.")
        return

    cookie_str = "; ".join(pairs)
    print("=== NAUKRI_COOKIE (paste into .env) ===")
    print(cookie_str)
    print("=== Length:", len(cookie_str), "chars", "(>50 looks OK)" if len(cookie_str) > 50 else "(TOO SHORT)")


if __name__ == "__main__":
    main()
