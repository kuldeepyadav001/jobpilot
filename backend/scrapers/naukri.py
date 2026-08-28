import re
import urllib.parse
from typing import List, Optional
from loguru import logger
from scrapers.base import BaseScraper, ScrapedJob


class NaukriScraper(BaseScraper):
    BASE_URL = "https://www.naukri.com"

    def _parse_salary(self, salary_str: str):
        """Parses Lakhs per annum to integer INR values."""
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

    async def scrape(self, keyword: str, location: Optional[str] = None, max_results: int = 20) -> List[ScrapedJob]:
        jobs: List[ScrapedJob] = []
        page = await self.init_browser(domain=".naukri.com")

        try:
            formatted_kw = keyword.strip().lower().replace(" ", "-")
            search_url = f"{self.BASE_URL}/{formatted_kw}-jobs"
            if location:
                formatted_loc = location.strip().lower().replace(" ", "-")
                search_url += f"-in-{formatted_loc}"

            logger.info(f"[Naukri] Navigating to: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)

            # Wait for job tuple cards
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
                    desc = (await desc_elem.inner_text()).strip() if desc_elem else f"{title} at {company_name}"

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
                        description=desc,
                        url=job_url
                    ))
                except Exception as e:
                    logger.debug(f"[Naukri] Error parsing card: {e}")
                    continue

            logger.info(f"[Naukri] Scraped {len(jobs)} jobs successfully")
            return jobs

        except Exception as e:
            logger.error(f"[Naukri] Scraping failed: {e}")
            return jobs
        finally:
            await self.close()