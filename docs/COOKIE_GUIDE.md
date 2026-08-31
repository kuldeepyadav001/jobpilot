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

## Naukri (needs the Application tab)

Naukri keeps its session in **httpOnly** cookies, so `document.cookie` can't read them.
Use the Application panel instead:

1. Log in at **https://www.naukri.com**.
2. **F12** → **Application** tab → **Cookies** → `https://www.naukri.com`.
3. Find the session cookie(s) — typically named `naukri.com` or similar. Copy the
   **cookie name** and **value** for the main session one.
4. Assemble into the format `name=value` and set:
   ```
   NAUKRI_COOKIE=name=value
   ```
   (Add more cookies joined by `; ` if several are needed for the session.)
5. `docker compose restart backend`, then hit **Test Login** again — should be green.

> If you'd like, you can copy the *whole* list: in the Application tab, right-click →
> **Copy all**, then join all the `CookieName=Value` pairs with `; `.

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
