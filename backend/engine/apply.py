import os
from typing import Optional, Tuple
from loguru import logger
from scrapers.base import BaseBrowser
from core.config import settings


class PlaywrightApplyEngine(BaseBrowser):
    """
    Automates interactions on job portals using pre-established session cookies.
    Includes smart apply method detection.
    """
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)

    async def detect_apply_method(self, job_url: str, portal: str) -> Tuple[str, Optional[str]]:
        """
        Scans the job page to determine the best apply method.
        Returns: (method, recipient_email_or_none)
        - 'email' + email address if mailto: link found
        - 'portal' if Easy Apply button found on-page
        - 'manual' if external redirect or no apply option found
        """
        cookie_string = os.getenv(f"{portal.upper()}_COOKIE", "")
        domain = f".{portal}.com" if portal == "naukri" else f".{portal}.com"
        page = await self.init_browser(cookie_string=cookie_string, domain=domain)

        try:
            logger.info(f"[Smart Route] Scanning apply method for: {job_url}")
            await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            # Check 1: Look for mailto: links (email apply)
            BLOCKED_DOMAINS = ["internshala.com", "naukri.com", "support", "complaints", "noreply", "no-reply"]
            mailto_links = await page.query_selector_all("a[href^='mailto:']")
            for link in mailto_links:
                href = await link.get_attribute("href")
                if not href:
                    continue
                email = href.replace("mailto:", "").split("?")[0].strip().lower()
                if not email or "@" not in email:
                    continue
                # Skip if email belongs to the portal itself or generic addresses
                is_blocked = any(blocked in email for blocked in BLOCKED_DOMAINS)
                if not is_blocked:
                    logger.info(f"[Smart Route] Detected recruiter email: {email}")
                    return "email", email

            # Check 2: Look for on-page Easy Apply buttons
            apply_selectors = [
                "button#easy_apply_button",
                ".apply_now_button",
                "button[class*='apply']",
                "a[class*='apply']",
                ".btn-apply",
                "#apply-button",
                "button:has-text('Apply')",
                "button:has-text('Easy Apply')",
            ]
            for selector in apply_selectors:
                try:
                    btn = await page.query_selector(selector)
                    if btn:
                        is_visible = await btn.is_visible()
                        if is_visible:
                            logger.info(f"[Smart Route] Detected portal apply button: {selector}")
                            return "portal", None
                except Exception:
                    continue

            # Check 3: Look for external redirect links (LinkedIn, company careers)
            external_selectors = [
                "a[href*='linkedin.com/jobs']",
                "a[href*='careers.']",
                "a[href*='jobs.']",
                "a:has-text('Apply on company website')",
                "a:has-text('Apply on LinkedIn')",
            ]
            for selector in external_selectors:
                try:
                    link = await page.query_selector(selector)
                    if link:
                        logger.info(f"[Smart Route] Detected external redirect: {selector}")
                        return "manual", None
                except Exception:
                    continue

            # Default: No clear apply method found
            logger.warning("[Smart Route] No apply method detected. Defaulting to manual.")
            return "manual", None

        except Exception as e:
            logger.error(f"[Smart Route] Detection failed: {e}")
            return "manual", None
        finally:
            await self.close()

    async def apply_to_internshala(self, job_url: str, cover_letter: str) -> str:
        """Loads Internshala job page, clicks apply, writes cover letter."""
        cookie_string = os.getenv("INTERNSHALA_COOKIE", "")
        page = await self.init_browser(cookie_string=cookie_string, domain=".internshala.com")

        try:
            logger.info(f"[Portal Apply] Opening: {job_url}")
            await page.goto(job_url, wait_until="domcontentloaded", timeout=45000)

            already_applied = await page.query_selector("text=Already applied") or await page.query_selector(".already_applied")
            if already_applied:
                return "applied"

            apply_btn = await page.query_selector("button#easy_apply_button, .apply_now_button")
            if not apply_btn:
                return "needs_manual_action"

            await apply_btn.click()
            await page.wait_for_timeout(2000)

            textareas = await page.query_selector_all("textarea")
            for area in textareas:
                placeholder = await area.get_attribute("placeholder") or ""
                label = await area.inner_text() or ""
                if "why should you be hired" in label.lower() or "cover letter" in placeholder.lower() or len(textareas) == 1:
                    await area.fill(cover_letter)
                    break

            submit_btn = await page.query_selector("input[type='submit'], button[type='submit'], #submit")
            if submit_btn:
                if settings.apply_mode == "real":
                    await submit_btn.click()
                    await page.wait_for_timeout(3000)
                    return "applied"
                else:
                    logger.info("[Portal Apply] DRY_RUN: skipped final submit. Set APPLY_MODE=real to submit for real.")
                    return "applied"

            return "needs_manual_action"

        except Exception as e:
            logger.error(f"[Portal Apply] Error: {e}")
            return "needs_manual_action"
        finally:
            await self.close()