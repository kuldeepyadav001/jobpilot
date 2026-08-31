import os
import re
import asyncio
from typing import List, Optional
from loguru import logger
from scrapers.base import BaseScraper, ScrapedJob


class InternshalaScraper(BaseScraper):
    BASE_URL = "https://internshala.com"

    def _parse_salary(self, salary_str: str):
        """Internshala internships pay a monthly stipend; jobs pay an annual salary."""
        if not salary_str:
            return None, None
        nums = [int(s.replace(",", "")) for s in re.findall(r"\d[\d,]*", salary_str)]
        if len(nums) == 1:
            return nums[0], nums[0]
        elif len(nums) >= 2:
            return nums[0], nums[1]
        return None, None

    def _search_url(self, keyword: str, job_type: str, location: str) -> str:
        """Build the CORRECT Internshala search URL for jobs vs internships.

        Internshala has two SEPARATE sections, and each honours a keyword only via
        the `keywords-<term>` route:
          - Internships: /internships/keywords-{kw}/   (monthly stipend)
          - Jobs:        /jobs/keywords-{kw}/          (annual salary)

        IMPORTANT: the older `/internships/{kw}-internships` form silently 302s to
        the generic `/internships/` page (ALL internships — finance, marketing, ...)
        and DROPS the keyword, so it returned the wrong listings. Never append a
        `-in-{loc}` suffix either — it also breaks the keyword filter.
        """
        kw = keyword.strip().lower().replace(" ", "-")
        if job_type == "internship":
            url = f"{self.BASE_URL}/internships/keywords-{kw}"
        else:
            url = f"{self.BASE_URL}/jobs/keywords-{kw}"
        # `location` is intentionally NOT added to the path: the -in-{loc} suffix
        # disables the keyword filter on Internshala. Location is still captured
        # per-job from the card itself, and can be filtered later in-app.
        return url + "/"

    async def scrape(self, keyword: str, location: Optional[str] = None, max_results: int = 20,
                     enrich: bool = True, skip_urls: Optional[set] = None,
                     job_type: str = "job") -> List[ScrapedJob]:
        """Scrapes Internshala. `job_type` selects the section: 'job' or 'internship'."""
        jobs: List[ScrapedJob] = []
        cookie_string = os.getenv("INTERNSHALA_COOKIE", "")
        page = await self.ensure_page(cookie_string=cookie_string, domain=".internshala.com")
        is_internship = (job_type == "internship")

        try:
            search_url = self._search_url(keyword, job_type, location or "")
            logger.info(f"[Internshala] Navigating to: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)

            if cookie_string:
                session_ok = await self.check_session_valid(page, "internshala")
                if not session_ok:
                    logger.warning("[Internshala] Session validation failed. Proceeding in guest browsing mode.")

            cards = await page.query_selector_all(".individual_internship, .individual-job")
            if not cards:
                cards = await page.query_selector_all(".job-detail, .internship_detail, .individual_internship")

            for card in cards[:max_results]:
                try:
                    title_elem = (await card.query_selector(".job-internship-name")
                                  or await card.query_selector("h3")
                                  or await card.query_selector(".job-title")
                                  or await card.query_selector(".profile"))
                    company_elem = (await card.query_selector(".company-name")
                                    or await card.query_selector(".company")
                                    or await card.query_selector(".link_display"))
                    location_elem = await card.query_selector(".locations span") or await card.query_selector(".location")
                    salary_elem = (await card.query_selector(".stipend .desktop, .salary .desktop, .salary")
                                   or await card.query_selector(".desktop .sal"))
                    link_elem = (await card.query_selector(".job-internship-name a")
                                 or await card.query_selector("a.job-title-href")
                                 or await card.query_selector(".link_display a")
                                 or await card.query_selector("a"))

                    if not title_elem or not link_elem:
                        continue

                    title = (await title_elem.inner_text()).strip()
                    company_name = (await company_elem.inner_text()).strip() if company_elem else "Unknown"
                    loc = (await location_elem.inner_text()).strip() if location_elem else "Remote"
                    sal_text = (await salary_elem.inner_text()).strip() if salary_elem else ""
                    sal_min, sal_max = self._parse_salary(sal_text)

                    href = await link_elem.get_attribute("href")
                    job_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

                    jobs.append(ScrapedJob(
                        portal="internshala",
                        title=title,
                        company_name=company_name,
                        location=loc,
                        salary_min=sal_min,
                        salary_max=sal_max,
                        description="",  # Will be enriched below
                        url=job_url,
                        job_type="internship" if is_internship else "job",
                    ))
                except Exception as e:
                    logger.debug(f"[Internshala] Error parsing card: {e}")
                    continue

            logger.info(f"[Internshala] Scraped {len(jobs)} {job_type}s from listing page")

            # --- ENRICH: Fetch full JD for each job ---
            if enrich and skip_urls:
                skipped = sum(1 for j in jobs if j.url in skip_urls)
                jobs = [j for j in jobs if j.url not in skip_urls]
                if skipped:
                    logger.info(f"[Internshala] Skipped enriching {skipped} jobs already in DB; "
                                f"enriching {len(jobs)} new.")
            if enrich:
                logger.info(f"[Internshala] Enriching {len(jobs)} jobs with full descriptions...")
            for job in jobs:
                if not enrich:
                    break
                try:
                    await asyncio.sleep(2)
                    await page.goto(job.url, wait_until="domcontentloaded", timeout=30000)

                    desc_selectors = [
                        ".text-container",
                        ".detail_view",
                        ".internship_detail",
                        ".job-detail",
                        "#job_description",
                        ".description",
                        ".detail_container",
                    ]

                    full_desc = ""
                    for selector in desc_selectors:
                        desc_elem = await page.query_selector(selector)
                        if desc_elem:
                            full_desc = (await desc_elem.inner_text()).strip()
                            if len(full_desc) > 50:
                                break

                    if full_desc and len(full_desc) > 50:
                        job.description = full_desc[:3000]
                        logger.debug(f"[Internshala] Got full JD ({len(full_desc)} chars) for: {job.title[:40]}")
                    else:
                        job.description = f"{job.title} at {job.company_name}"

                except Exception as e:
                    logger.debug(f"[Internshala] Failed to enrich JD for {job.url}: {e}")
                    job.description = f"{job.title} at {job.company_name}"

            return jobs

        except Exception as e:
            logger.error(f"[Internshala] Scraping failed: {e}")
            return jobs
        finally:
            if self.close_browser_on_scrape:
                await self.close()
