import os
from typing import Optional
from playwright.async_api import Page
from loguru import logger
from scrapers.base import BaseBrowser
from core.config import settings


class PlaywrightApplyEngine(BaseBrowser):
    """
    Automates interactions on job portals using pre-established session cookies.
    """
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)

    async def apply_to_internshala(self, job_url: str, cover_letter: str) -> str:
        """
        Loads Internshala job page, clicks apply, writes response answers.
        Returns state string: 'applied' or 'needs_manual_action'.
        """
        cookie_string = os.getenv("INTERNSHALA_COOKIE", "")
        page = await self.init_browser(cookie_string=cookie_string, domain=".internshala.com")

        try:
            logger.info(f"[Portal Apply] Opening: {job_url}")
            await page.goto(job_url, wait_until="domcontentloaded", timeout=45000)

            # Check if already applied on page
            already_applied = await page.query_selector("text=Already applied") or await page.query_selector(".already_applied")
            if already_applied:
                logger.warning(f"[Portal Apply] Already applied according to portal page.")
                return "applied"

            # Click primary action CTA
            apply_btn = await page.query_selector("button#easy_apply_button, .apply_now_button")
            if not apply_btn:
                logger.warning("[Portal Apply] Apply button missing or off-site redirect required.")
                return "needs_manual_action"

            await apply_btn.click()
            await page.wait_for_timeout(2000)

            # Look for answer input textareas
            textareas = await page.query_selector_all("textarea")
            for area in textareas:
                placeholder = await area.get_attribute("placeholder") or ""
                label = await area.inner_text() or ""
                if "why should you be hired" in label.lower() or "cover letter" in placeholder.lower() or len(textareas) == 1:
                    await area.fill(cover_letter)
                    break

            # Confirm submit step
            submit_btn = await page.query_selector("input[type='submit'], button[type='submit'], #submit")
            if submit_btn:
                if settings.environment == "production":
                    await submit_btn.click()
                    await page.wait_for_timeout(3000)
                    logger.info("[Portal Apply] Application successfully submitted.")
                    return "applied"
                else:
                    logger.info("[Portal Apply] SAFE MODE: Skipped final submit button click.")
                    return "applied"

            return "needs_manual_action"

        except Exception as e:
            logger.error(f"[Portal Apply] Automation encountered issue: {e}")
            return "needs_manual_action"
        finally:
            await self.close()