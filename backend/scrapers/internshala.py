import re
import urllib.parse
from typing import List, Optional
from loguru import logger
from scrapers.base import BaseScraper, ScrapedJob


class InternshalaScraper(BaseScraper):
    BASE_URL = "https://internshala.com"

    def _parse_salary(self, salary_str: str):
        """Extracts min and max yearly/monthly salary in INR."""
        if not salary_str:
            return None, None
        nums = [int(s.replace(",", "")) for s in re.findall(r"\d[\d,]*", salary_str)]
        if len(nums) == 1:
            return nums[0], nums[0]
        elif len(nums) >= 2:
            return nums[0], nums[1]
        return None, None

    async def scrape(self, keyword: str, location: Optional[str] = None, max_results: int = 20) -> List[ScrapedJob]:
        jobs: List[ScrapedJob] = []
        page = await self.init_browser(domain=".internshala.com")

        try:
            # Build search URL
            query_keyword = keyword.strip().lower().replace(" ", "-")
            search_url = f"{self.BASE_URL}/jobs/{query_keyword}-jobs"
            if location:
                query_location = location.strip().lower().replace(" ", "-")
                search_url += f"-in-{query_location}"

            logger.info(f"[Internshala] Navigating to: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)

            # Wait for job container cards
            await page.wait_for_selector(".individual_internship", timeout=15000)
            cards = await page.query_selector_all(".individual_internship")

            for card in cards[:max_results]:
                try:
                    title_elem = await card.query_selector(".job-internship-name")
                    company_elem = await card.query_selector(".company-name")
                    location_elem = await card.query_selector(".locations span")
                    salary_elem = await card.query_selector(".desktop .sal") or await card.query_selector(".salary .desktop")
                    link_elem = await card.query_selector(".job-internship-name a") or await card.query_selector("a.job-title-href")

                    if not title_elem or not company_elem or not link_elem:
                        continue

                    title = (await title_elem.inner_text()).strip()
                    company_name = (await company_elem.inner_text()).strip()
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
                        description=f"Role: {title} at {company_name}",
                        url=job_url
                    ))
                except Exception as e:
                    logger.debug(f"[Internshala] Error parsing a card: {e}")
                    continue

            logger.info(f"[Internshala] Scraped {len(jobs)} jobs successfully")
            return jobs

        except Exception as e:
            logger.error(f"[Internshala] Scraping failed: {e}")
            return jobs
        finally:
            await self.close()