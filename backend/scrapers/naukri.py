import os
import re
import asyncio
from typing import List, Optional
from loguru import logger
from scrapers.base import BaseScraper, ScrapedJob


class NaukriScraper(BaseScraper):
    BASE_URL = "https://www.naukri.com"

    def _parse_salary(self, salary_str: str):
        if not salary_str or "Not disclosed" in salary_str:
            return None, None
        nums = [float(s) for s in re.findall(r"\d+(?:\.\d+)?", salary_str)]
        if len(nums) == 1:
            val = int(nums[0] * 100000) if "Lac" in salary_str or "PA" in salary_str else int(nums[0])
            return val, val
        elif len(nums) >= 2:
            multiplier = 100000 if "Lac" in salary_str or "PA" in salary_str else 1
            return int(nums[0] * multiplier), int(nums[1] * multiplier)
        return None, None

    async def scrape(self, keyword: str, location: Optional[str] = None, max_results: int = 20,
                     enrich: bool = True, skip_urls: Optional[set] = None) -> List[ScrapedJob]:
        jobs: List[ScrapedJob] = []
        cookie_string = os.getenv("NAUKRI_COOKIE", "")
        page = await self.ensure_page(cookie_string=cookie_string, domain=".naukri.com")

        try:
            formatted_kw = keyword.strip().lower().replace(" ", "-")
            search_url = f"{self.BASE_URL}/{formatted_kw}-jobs"
            if location:
                formatted_loc = location.strip().lower().replace(" ", "-")
                search_url += f"-in-{formatted_loc}"

            logger.info(f"[Naukri] Navigating to: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)

            # Check session health if cookies were provided
            if cookie_string:
                session_ok = await self.check_session_valid(page, "naukri")
                if not session_ok:
                    logger.warning("[Naukri] Session validation failed. Proceeding in guest browsing mode.")

            await page.wait_for_selector(".srp-jobtuple-wrapper, .jobTuple", timeout=15000)
            cards = await page.query_selector_all(".srp-jobtuple-wrapper, .jobTuple")

            for card in cards[:max_results]:
                try:
                    title_elem = await card.query_selector("a.title")
                    company_elem = await card.query_selector("a.comp-name") or await card.query_selector(".subTitle")
                    location_elem = await card.query_selector(".locWdth") or await card.query_selector(".location")
                    salary_elem = await card.query_selector(".salWdth") or await card.query_selector(".salary")
                    desc_elem = await card.query_selector(".job-desc") or await card.query_selector(".job-description")

                    if not title_elem or not company_elem:
                        continue

                    title = (await title_elem.inner_text()).strip()
                    company_name = (await company_elem.inner_text()).strip()
                    loc = (await location_elem.inner_text()).strip() if location_elem else "India"
                    sal_text = (await salary_elem.inner_text()).strip() if salary_elem else ""
                    sal_min, sal_max = self._parse_salary(sal_text)
                    short_desc = (await desc_elem.inner_text()).strip() if desc_elem else ""

                    job_url = await title_elem.get_attribute("href")
                    if not job_url:
                        continue

                    jobs.append(ScrapedJob(
                        portal="naukri",
                        title=title,
                        company_name=company_name,
                        location=loc,
                        salary_min=sal_min,
                        salary_max=sal_max,
                        description=short_desc,
                        url=job_url
                    ))
                except Exception as e:
                    logger.debug(f"[Naukri] Error parsing card: {e}")
                    continue

            logger.info(f"[Naukri] Scraped {len(jobs)} jobs from listing page")

            # --- ENRICH: Fetch full JD for each job ---
            if enrich and skip_urls:
                skipped = sum(1 for j in jobs if j.url in skip_urls)
                jobs = [j for j in jobs if j.url not in skip_urls]
                if skipped:
                    logger.info(f"[Naukri] Skipped enriching {skipped} jobs already in DB; "
                                f"enriching {len(jobs)} new.")
            if enrich:
                logger.info(f"[Naukri] Enriching {len(jobs)} jobs with full descriptions...")
            for job in jobs:
                if not enrich:
                    break  # Lightweight mode (diagnostics): listing-card data is enough
                try:
                    await asyncio.sleep(2)
                    await page.goto(job.url, wait_until="domcontentloaded", timeout=30000)

                    desc_selectors = [
                        ".job-description",
                        ".dang-inner-html",
                        ".styles_JDC__dang-inner-html__h0K4t",
                        "[class*='jobDescription']",
                        ".description",
                        "#jobDesc",
                    ]

                    full_desc = ""
                    for selector in desc_selectors:
                        desc_elem = await page.query_selector(selector)
                        if desc_elem:
                            full_desc = (await desc_elem.inner_text()).strip()
                            if len(full_desc) > 80:
                                break

                    if full_desc and len(full_desc) > 80:
                        job.description = full_desc[:3000]
                        logger.debug(f"[Naukri] Got full JD ({len(full_desc)} chars) for: {job.title[:40]}")
                    else:
                        if not job.description or len(job.description) < 30:
                            job.description = f"{job.title} at {job.company_name}"

                except Exception as e:
                    logger.debug(f"[Naukri] Failed to enrich JD for {job.url}: {e}")
                    if not job.description or len(job.description) < 30:
                        job.description = f"{job.title} at {job.company_name}"

            return jobs

        except Exception as e:
            logger.error(f"[Naukri] Scraping failed: {e}")
            return jobs
        finally:
            if self.close_browser_on_scrape:
                await self.close()