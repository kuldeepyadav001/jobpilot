// COOKIE GRABBER for JobPilot
// Open this in the browser's DevTools console on the portal you're logged into:
//   - Naukri: https://www.naukri.com
//   - Internshala: https://internshala.com
// Then run everything below, and copy the printed value straight into your .env.
//
// NOTE: Naukri stores its session in httpOnly cookies, which `document.cookie`
// CANNOT read. For Naukri you must use the DevTools -> Application -> Cookies
// method instead (see COOKIE_GUIDE.md). This snippet works fully for Internshala,
// and gives you part of the Naukri cookie string if it's non-httpOnly.
function grabCookies() {
  const list = document.cookie.split(';').map(c => c.trim()).filter(Boolean);
  return list.join('; ');
}

const host = window.location.hostname;
if (host.includes('internshala.com')) {
  const c = grabCookies();
  console.log('%c=== INTERNSHALA_COOKIE paste this into .env ===', 'color:#12b886;font-weight:bold');
  console.log(c);
  console.log('Length:', c.length, 'chars', c.length > 50 ? '(looks OK)' : '(TOO SHORT — not logged in?)');
} else if (host.includes('naukri.com')) {
  const c = grabCookies();
  console.log('%c=== NAUKRI_COOKIE (partial — see COOKIE_GUIDE.md for the full httpOnly method) ===', 'color:#f59e0b;font-weight:bold');
  console.log(c);
  console.log('Length:', c.length, 'chars');
  console.log('If this is SHORT or missing, Naukri uses httpOnly cookies — use DevTools > Application > Cookies instead.');
} else {
  console.log('Open the console while on naukri.com or internshala.com.');
}
