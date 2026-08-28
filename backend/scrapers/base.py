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
    """Manages headless Chromium lifecycle and cookie injection."""
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def init_browser(self, cookie_string: Optional[str] = None, domain: Optional[str] = None) -> Page:
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )

        if cookie_string and domain:
            cookies = []
            for item in cookie_string.split(";"):
                if "=" in item:
                    name, value = item.strip().split("=", 1)
                    cookies.append({"name": name, "value": value, "domain": domain, "path": "/"})
            if cookies:
                await self.context.add_cookies(cookies)

        page = await self.context.new_page()
        return page

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()


class BaseScraper(BaseBrowser, ABC):
    @abstractmethod
    async def scrape(self, keyword: str, location: Optional[str] = None, max_results: int = 20) -> List[ScrapedJob]:
        """Scrapes jobs matching search criteria."""
        pass