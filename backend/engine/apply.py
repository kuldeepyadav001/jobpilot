import os
from contextlib import suppress
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

            # Check 2: Look for on-page Easy Apply triggers (button OR the <a>
            # 'Apply now' link Internshala actually uses — this is why applying
            # failed: the old code only looked for <button> elements).
            apply_selectors = [
                "button#easy_apply_button",
                ".apply_now_button",
                "button[class*='apply']",
                "a[class*='apply']",
                ".btn-apply",
                "#apply-button",
                "button:has-text('Apply')",
                "button:has-text('Easy Apply')",
                "a:has-text('Apply now')",
                "a:has-text('Apply Now')",
                "a[href*='interstitial/application']",
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

    async def _is_logged_in(self, page) -> bool:
        """Checks the page for evidence we're NOT signed in (so we can fail fast)."""
        login_redirect = await page.query_selector("a[href*='/login/'], #sign_up, .login_btn, button:has-text('Login')")
        if login_redirect:
            return False
        # A signed-in Internshala page usually shows the user's name / account.
        return True

    async def _confirmed_applied_page_probe(self, page) -> bool:
        """Testable probe: returns True if the page matches any post-submit success signal.

        Extracted from _confirmed_applied so the logic can be unit-tested without a
        live browser / page object, by passing a stub that answers query_selector().
        """
        success_selectors = [
            "text=Application submitted",
            "text=You've applied",
            "text=You have applied",
            "text=Successfully applied",
            "text=Already applied",
            "text=Applied",
        ]
        for sel in success_selectors:
            try:
                found = await page.query_selector(sel)
                if found:
                    return True
            except Exception:
                continue
        return False

    async def _confirmed_applied(self, page) -> bool:
        """True only if the apply actually went through — checks for a success signal."""
        # Success signals after submitting on Internshala.
        success_selectors = [
            "text=Application submitted",
            "text=You've applied",
            "text=You have applied",
            "text=Successfully applied",
            "text=Already applied",
            ".already_applied",
            "text=Applied",
        ]
        for sel in success_selectors:
            try:
                if await page.query_selector(sel):
                    return True
            except Exception:
                continue
        # Also treat the apply button switching to a disabled/applied state as success.
        try:
            btn = await page.query_selector("button#easy_apply_button, .apply_now_button")
            if btn:
                disabled = await btn.get_attribute("disabled")
                cls = (await btn.get_attribute("class")) or ""
                if disabled is not None or "applied" in cls.lower():
                    return True
        except Exception:
            pass
        return False

    async def apply_to_internshala(self, job_url: str, cover_letter: str) -> str:
        """Loads Internshala job page, clicks apply, writes cover letter, and VERIFIES
        the submission actually went through before reporting success.

        Returns:
          - 'applied'            only when a post-submit success signal is confirmed.
          - 'needs_manual_action' when it could not submit OR could not confirm success
                                 (stale cookie / not logged in / flow changed). These are
                                 NOT falsely marked applied.
        """
        cookie_string = os.getenv("INTERNSHALA_COOKIE", "")
        page = await self.init_browser(cookie_string=cookie_string, domain=".internshala.com")

        try:
            logger.info(f"[Portal Apply] Opening: {job_url}")
            await page.goto(job_url, wait_until="domcontentloaded", timeout=45000)

            # Already applied previously? Nothing to do.
            already_applied = await page.query_selector("text=Already applied") or await page.query_selector(".already_applied")
            if already_applied:
                logger.info("[Portal Apply] Already applied for this job.")
                return "applied"

            if not await self._is_logged_in(page):
                logger.warning("[Portal Apply] Looks like NOT logged in — cookie may be stale. "
                               "Not submitting. Refresh INTERNSHALA_COOKIE.")
                return "needs_manual_action"

            # Find the apply trigger across BOTH <button> AND the <a> 'Apply now'
            # link Internshala actually renders (the previous button-only selector
            # matched nothing, so no real application ever fired).
            apply_btn = (
                await page.query_selector("button#easy_apply_button, .apply_now_button")
                or await page.query_selector("a:has-text('Apply now')")
                or await page.query_selector("a:has-text('Apply Now')")
                or await page.query_selector("a[href*='interstitial/application']")
            )
            if not apply_btn:
                logger.warning("[Portal Apply] No apply link/button found on page. Flagging for manual.")
                return "needs_manual_action"

            await apply_btn.click()
            await page.wait_for_timeout(3000)
            logger.info(f"[Portal Apply] After clicking apply, now at: {page.url}")

            # The interstitial application form usually shows a job summary then a
            # form (this is the step the user described: "it shows a form with job
            # confirmation and all, you have to click again"). It can be one page or
            # a continue->confirm->submit sequence. We handle both by looping until a
            # real submit is available or a step transitions.
            for _step in range(4):
                # Fill the cover-letter 'why should you be hired' box.
                textareas = await page.query_selector_all("textarea")
                for area in textareas:
                    placeholder = (await area.get_attribute("placeholder")) or ""
                    label = (await area.inner_text()) or ""
                    if "why should you be hired" in label.lower() or "cover letter" in placeholder.lower() or len(textareas) == 1:
                        try:
                            await area.fill(cover_letter)
                        except Exception:
                            pass
                        break

                # Tick any required 'I accept / I agree' checkboxes so submit is allowed.
                checks = await page.query_selector_all(
                    "input[type='checkbox']:not(:checked), input[type='radio']"
                )
                with suppress(Exception):
                    for c in checks[:12]:
                        try:
                            await c.check(timeout=1500)
                        except Exception:
                            pass

                # APPLY GATE: in dry-run, reach the confirmation form but do NOT hit
                # the final submit (never falsely mark applied).
                if settings.apply_mode != "real":
                    logger.info("[Portal Apply] DRY_RUN: stopped before final submit. "
                                "Set APPLY_MODE=real to submit for real.")
                    return "needs_manual_action"

                # Look for the real submit/continue on this step. Internshala's final
                # action is often a button labelled Submit/Apply, or a Continue/Next
                # between confirmation pages.
                submit_btn = await page.query_selector(
                    "input[type='submit'], button[type='submit'], #submit, "
                    "button:has-text('Submit Application'), button:has-text('Submit'), "
                    "button:has-text('Apply'), a:has-text('Continue'), "
                    "button:has-text('Continue'), button:has-text('Confirm')"
                )
                if not submit_btn:
                    logger.warning(f"[Portal Apply] Step {_step}: no submit/continue button "
                                   f"(url={page.url}). Flagging for manual.")
                    return "needs_manual_action"
                url_before = page.url
                await submit_btn.click()
                await page.wait_for_timeout(3500)
                logger.info(f"[Portal Apply] Step {_step} clicked submit/continue; now at: {page.url}")
                if await self._confirmed_applied(page):
                    logger.info(f"[Portal Apply] Submission CONFIRMED for {job_url}")
                    return "applied"
                # If the page didn't transition after the click, looping would just
                # re-click the same button (risking a double submit); stop here.
                if page.url == url_before:
                    logger.warning(f"[Portal Apply] Page did not advance after click "
                                   f"(url={page.url}). Stopping this attempt (manual review).")
                    return "needs_manual_action"

        except Exception as e:
            logger.error(f"[Portal Apply] Error: {e}")
            return "needs_manual_action"
        finally:
            await self.close()

    async def _is_naukri_applied_confirmed(self, page) -> bool:
        """True if the page shows a Naukri 'Applied' confirmation."""
        selectors = [
            "text=Applied successfully",
            "text=You have applied",
            "text=Application submitted",
            "text=Not accepted",
            "text=Applied",
            ".applied-success",
            ".status-msg",
            "button:has-text('Applied')",
            "button:has-text('Withdraw')",
        ]
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    # Avoid false positive on passive 'Apply' button labels.
                    if sel.startswith("button"):
                        continue
                    return True
            except Exception:
                continue
        return False

    async def apply_to_naukri(self, job_url: str, cover_letter: str) -> str:
        """Best-effort Naukri auto-apply with honest verification.

        Returns 'applied' ONLY when Naukri confirms the submission; 'needs_manual_action'
        when the job requires profile completion, login, an external site redirect, or
        a step we can't verify. Naukri is heavily gated (profile-complete requirement and
        reCAPTCHA), so many jobs will legitimately route to manual rather than be falsely
        marked applied.
        """
        cookie_string = os.getenv("NAUKRI_COOKIE", "")
        page = await self.init_browser(cookie_string=cookie_string, domain=".naukri.com")
        try:
            logger.info(f"[Naukri Apply] Opening: {job_url}")
            await page.goto(job_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2500)

            # Already applied?
            if await self._is_naukri_applied_confirmed(page):
                logger.info("[Naukri Apply] Already applied / confirmed applied.")
                return "applied"

            if not await self._is_logged_in(page):
                logger.warning("[Naukri Apply] NOT logged in. Refresh NAUKRI_COOKIE.")
                return "needs_manual_action"

            # External redirect (company careers site / LinkedIn) => never auto-apply.
            external = await page.query_selector(
                "a[href*='careers.'], a[href*='career.'], a[href*='company'], a[href*='linkedin.com/jobs'], a:has-text('Company Website')"
            )
            if external:
                logger.warning("[Naukri Apply] External site apply — routing to manual (can't automate).")
                return "needs_manual_action"

            # Find Naukri's Apply button (multiple known classes/texts).
            apply_btn = (
                await page.query_selector("button:has-text('Apply')")
                or await page.query_selector("#app_buttons .apply-button")
                or await page.query_selector("button.btn-primary:has-text('Apply')")
                or await page.query_selector("a[href*='application'], a:has-text('Apply')")
            )
            if not apply_btn:
                logger.warning("[Naukri Apply] No apply button found. Flagging for manual.")
                return "needs_manual_action"

            await apply_btn.click()
            await page.wait_for_timeout(3500)

            # Naukri sometimes opens an "Easy Apply" modal with a 'Submit'/'Continue'.
            submit_btn = (
                await page.query_selector("button:has-text('Send')")
                or await page.query_selector("button:has-text('Submit Application')")
                or await page.query_selector("button:has-text('Submit')")
                or await page.query_selector("button:has-text('Continue')")
                or await page.query_selector("input[type='submit']")
            )
            if not submit_btn:
                logger.warning("[Naukri Apply] No final submit control found. Flagging for manual.")
                return "needs_manual_action"

            if settings.apply_mode == "real":
                await submit_btn.click()
                await page.wait_for_timeout(4000)
                if await self._is_naukri_applied_confirmed(page):
                    logger.info(f"[Naukri Apply] Submission CONFIRMED for {job_url}")
                    return "applied"
                logger.warning(f"[Naukri Apply] Clicked submit but could NOT confirm success for {job_url}. "
                               "Flagging for manual (likely profile-complete gate).")
                return "needs_manual_action"
            else:
                logger.info("[Naukri Apply] DRY_RUN: skipped final submit. Set APPLY_MODE=real to apply for real.")
                return "needs_manual_action"

        except Exception as e:
            logger.error(f"[Naukri Apply] Error: {e}")
            return "needs_manual_action"
        finally:
            await self.close()