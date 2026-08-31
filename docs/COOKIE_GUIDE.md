# Cookie Setup Guide (JobPilot)

JobPilot uses browser "session cookies" to apply to Portals as **you** (logged in).
A stale cookie is the #1 cause of "marked Applied but portal still shows Apply Now."

## Diagnose with "Test Login"
In the app: **Settings → Portal Cookie Status → Test Login**.
- 🟢 Green = cookie valid, you are logged in.
- 🔴 Red = cookie invalid / expired → refresh it as below.

(The old "Cookie length" read-out only proves text is present — it did **not** prove
you were logged in. That's why the apply looked fine but nothing was submitted.)

---

## Internshala (easy)

1. Log in at **https://internshala.com** in a normal browser tab.
2. Press **F12** → **Console** tab.
3. Paste the contents of `scripts/cookie_grabber.js` and press **Enter**.
4. Copy the printed value and set:
   ```
   INTERNSHALA_COOKIE=<pasted value>
   ```
   in your `.env`.
5. `docker compose restart backend`.

---

## Naukri (httpOnly — use the CDP exporter, no hunting)

Naukri keeps its session in **httpOnly** cookies, so `document.cookie` **cannot** read
them. Don't hunt through the 200+ requests in the Network tab. Use the bundled CDP
exporter, which reads the browser's *entire* cookie jar automatically:

1. Install the two small deps (once):
   ```bash
   python -m pip install requests websocket-client
   ```
2. Fully quit Chrome, then relaunch it with remote debugging and log into Naukri:
   ```
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
   ```
3. In that Chrome window, go to https://www.naukri.com and log in.
4. Run the exporter:
   ```bash
   python scripts/export_naukri_cookie.py
   ```
5. Copy the printed `NAUKRI_COOKIE` value into `.env`, then:
   ```bash
   docker compose restart backend
   ```
6. Go to Settings → **Test Login** → it should be green.

### Alternative (no script): DevTools → Application tab
1. Log in at **https://www.naukri.com**.
2. **F12** → **Application** → **Cookies** → `https://www.naukri.com`.
3. This is a clean table (no 200 network requests). Right-click a row → **Copy value**,
   or select several and copy. Join the `CookieName=Value` pairs with `; `.

> The Application tab lists only the cookies for the current site — you don't have to
> sift through network requests.

---

## Notes for Naukri specifically

- **Naukri auto-apply is NOT built yet.** Even with a valid cookie, Naukri jobs are
  currently routed to **"Needs Action"** for you to apply manually. The cookie is
  still worth keeping valid so we're ready when Naukri apply is added, and so
  scraping reliably works long-term.
- Internshala is the portal that actually auto-applies today.

## Keep in mind
- Cookies **expire** — refresh them periodically (set a reminder every ~2 weeks).
- After changing a cookie, **restart the backend** (`docker compose restart backend`)
  and re-run **Test Login** to confirm.
