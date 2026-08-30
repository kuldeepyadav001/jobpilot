from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger


@dataclass
class ScrapedJob:
    portal: str
    title: str
    company_name: str
    location: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    description: Optional[str]
    url: str


class BaseBrowser:
    """
    Manages headless Chromium lifecycle, cookie injection, and session validation.
    Used by both scrapers (Internshala/Naukri) and the apply engine.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def init_browser(
        self,
        cookie_string: Optional[str] = None,
        domain: Optional[str] = None
    ) -> Page:
        """
        Launches a stealth-configured Chromium instance.
        Injects session cookies if provided.
        """
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        self.context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )

        # Inject session cookies from .env
        if cookie_string and domain:
            cookies = []
            for item in cookie_string.split(";"):
                item = item.strip()
                if "=" in item:
                    name, value = item.split("=", 1)
                    cookies.append({
                        "name": name.strip(),
                        "value": value.strip(),
                        "domain": domain,
                        "path": "/",
                    })
            if cookies:
                await self.context.add_cookies(cookies)
                logger.debug(f"[Browser] Injected {len(cookies)} cookies for {domain}")

        page = await self.context.new_page()
        return page

    async def check_session_valid(self, page: Page, portal: str) -> bool:
        """
        Checks if the injected session cookies are still valid.
        Returns True if logged in, False if session expired.

        Detection methods:
        1. URL redirect to login/signin page
        2. "Session expired" or "Please login" text on page
        3. Missing user profile element (portal-specific)
        """
        try:
            current_url = page.url.lower()

            # Check 1: Redirected to login page
            login_indicators = ["/login", "/signin", "/sign-in", "/auth", "/register"]
            if any(indicator in current_url for indicator in login_indicators):
                logger.warning(
                    f"[Cookie Health] {portal} redirected to login page. "
                    f"Cookie expired. Update {portal.upper()}_COOKIE in .env"
                )
                return False

            # Check 2: Look for session expired text on page body
            expired_texts = [
                "session expired",
                "please login",
                "sign in to continue",
                "your session has timed out",
                "please sign in",
                "log in to continue",
            ]
            try:
                page_text = (await page.inner_text("body", timeout=5000)).lower()
            except Exception:
                page_text = ""

            for text in expired_texts:
                if text in page_text:
                    logger.warning(
                        f"[Cookie Health] {portal} shows '{text}'. "
                        f"Cookie expired. Update {portal.upper()}_COOKIE in .env"
                    )
                    return False

            # Check 3: Portal-specific profile indicators
            if portal == "internshala":
                profile = await page.query_selector(
                    ".profile_name, .user-name, .header-profile, "
                    ".nav-user-name, .student-dashboard"
                )
                if not profile:
                    logger.warning(
                        "[Cookie Health] Internshala profile element missing. "
                        "Cookie may be expired."
                    )
                    return False

            elif portal == "naukri":
                profile = await page.query_selector(
                    ".nI-gNb-drawer, .logged-in, .usr-pic, "
                    ".nav-user, .userLogin"
                )
                if not profile:
                    logger.warning(
                        "[Cookie Health] Naukri profile element missing. "
                        "Cookie may be expired."
                    )
                    return False

            logger.info(f"[Cookie Health] {portal} session is valid.")
            return True

        except Exception as e:
            logger.error(f"[Cookie Health] Validation check failed for {portal}: {e}")
            # Default to True on error to avoid blocking scraping on false negatives
            return True

    async def close(self):
        """Closes browser context and browser instance cleanly."""
        try:
            if self.context:
                await self.context.close()
        except Exception as e:
            logger.debug(f"[Browser] Context close error (non-critical): {e}")
        try:
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.debug(f"[Browser] Browser close error (non-critical): {e}")


class BaseScraper(BaseBrowser, ABC):
    """
    Abstract base class for all portal scrapers.
    Inherits browser lifecycle from BaseBrowser.
    Subclasses must implement the scrape() method.
    """

    @abstractmethod
    async def scrape(
        self,
        keyword: str,
        location: Optional[str] = None,
        max_results: int = 20
    ) -> List[ScrapedJob]:
        """Scrapes jobs matching search criteria from the portal."""
        pass