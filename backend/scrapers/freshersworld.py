"""Freshersworld scraper — jobs + internship postings for freshers.

Design notes:
- Freshersworld (freshersworld.com) is JS-rendered and uses many container class
  names that change. We therefore parse defensively:
    1. Try known card containers.
    2. Fall back to any <a> whose href points at a job detail page.
  Either path yields (title, company, location, salary, url).
- Browsing listings does NOT require a login, so this scraper works guest-mode by
  default; a FRESHERWORLD_COOKIE can optionally be injected for richer results.
"""
from __future__ import annotations

import os
import re
from typing import List, Optional

from loguru import logger

from scrapers.base import BaseScraper, ScrapedJob


class FreshersworldScraper(BaseScraper):
    BASE_URL = "https://www.freshersworld.com"
    portal = "freshersworld"
    supports_jobs = True
    supports_internships = True

    # A job-detail link looks like /jobs/<slug>-job-<id> (or -internship-, -vacancy-).
    DETAIL_RE = re.compile(r"/jobs/[^/?#]+-(?:job|internship|vacancy|opening)s?-\d+", re.I)

    def _parse_salary(self, text: str):
        """Freshersworld shows salaries like 'INR 3 - 5 Lacs PA' or '2 LPA' or '₹5,000/mo'."""
        if not text:
            return None, None
        nums = [int(s.replace(",", "")) for s in re.findall(r"(\d[\d,]*)", text)]
        # Annually: look for "lac"/"lakh"/"lpa"; else assume monthly which we null out.
        if not nums:
            return None, None
        is_annual = bool(re.search(r"lac|lakh|lpa|annual|pa\b", text, re.I))
        low, high = nums[0], (nums[1] if len(nums) > 1 else nums[0])
        if is_annual:
            return low * 100000, high * 100000
        return None, None  # likely a monthly stipend; we don't guess

    def _search_url(self, keyword: str, job_type: str, location: str) -> str:
        kw = keyword.strip().replace(" ", "+")
        target = "Internship" if job_type == "internship" else "jobs"
        base = f"{self.BASE_URL}/jobs/jobsearch?searchType=Search&searchText={kw}&searchTarget={target}"
        if location:
            base += f"&location={location.strip().replace(' ', '+')}"
        return base

    def _is_detail_link(self, href: str) -> bool:
        return bool(href) and bool(self.DETAIL_RE.search(href))

    async def scrape(
        self,
        keyword: str,
        location: Optional[str] = None,
        max_results: int = 20,
        enrich: bool = True,
        skip_urls: Optional[set] = None,
        job_type: str = "job",
    ) -> List[ScrapedJob]:
        jobs: List[ScrapedJob] = []
        cookie_string = os.getenv("FRESHERWORLD_COOKIE", "")
        page = await self.ensure_page(cookie_string=cookie_string, domain=".freshersworld.com")

        try:
            search_url = self._search_url(keyword, job_type, location or "")
            logger.info(f"[Freshersworld] Navigating to: {search_url}")
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                logger.warning(f"[Freshersworld] goto issue (continuing): {e}")
            await page.wait_for_timeout(3000)

            # Try the richest HTML extraction first (JS-rendered), then fall back
            # to raw HTML anchor parsing.
            raw_html = await page.content()
            cards = await self._query_card_elements(page)
            extracted = await self._extract_from_elements(cards, max_results)
            if len(extracted) < 2:
                logger.info("[Freshersworld] Low card yield; falling back to generic link parsing.")
                extracted = self._extract_from_html(raw_html)

            seen = set()
            for item in extracted:
                if len(jobs) >= max_results:
                    break
                url = item.get("url")
                title = (item.get("title") or "").strip()
                if not url or not title or not self._is_detail_link(url):
                    continue
                key = title.lower()
                if key in seen:
                    continue
                seen.add(key)
                if skip_urls and url in skip_urls:
                    continue
                jobs.append(ScrapedJob(
                    portal="freshersworld",
                    title=title,
                    company_name=(item.get("company") or "").strip(),
                    location=(item.get("location") or "").strip() or None,
                    salary_min=item.get("salary_min"),
                    salary_max=item.get("salary_max"),
                    description=(item.get("description") or "").strip() or None,
                    url=url,
                    job_type=job_type,
                ))
            logger.info(f"[Freshersworld] '{keyword}' ({job_type}) -> {len(jobs)} jobs")
        except Exception as e:
            logger.error(f"[Freshersworld] scrape failed for '{keyword}': {e}")
        finally:
            if self.close_browser_on_scrape:
                await self.close()
        return jobs

    async def _query_card_elements(self, page):
        for sel in (
            ".job-card, .jobList, .jobOpportunities, .job-detail, .job-container, "
            ".job-listing, .fw-card, .search-result, .card, .job-row, li",
            "div[class*='job']",
        ):
            try:
                els = await page.query_selector_all(sel)
                if els and len(els) > 3:
                    return els
            except Exception:
                continue
        return []

    async def _extract_from_elements(self, cards, max_results) -> List[dict]:
        out = []
        for card in cards[: max_results * 4]:
            try:
                link = (await card.query_selector("a[href*='/jobs/']")
                        or await card.query_selector("h2 a, h3 a, h4 a"))
                if not link:
                    continue
                href = await link.get_attribute("href")
                title = (await link.inner_text()).strip()
                text = (await card.inner_text()).strip() if card else ""
                # Company: often a small element; best-effort.
                company = ""
                comp = await card.query_selector(".company, .company-name, .cmp, .employer")
                if comp:
                    company = (await comp.inner_text()).strip()
                location = ""
                loc = await card.query_selector(".location, .city, .loc")
                if loc:
                    location = (await loc.inner_text()).strip()
                lo, hi = self._parse_salary(text)
                out.append({
                    "url": url_prefixed(href),
                    "title": title or "",
                    "company": company or (line_company(text)),
                    "location": location or re.search(r"\b(?:Bangalore|Mumbai|Hyderabad|Chennai|Delhi|Pune|Noida|Gurgaon|Kolkata|Ahmedabad|Remote|Pan-India)\b", text, re.I).group(0) if re.search(r"\b(?:Bangalore|Mumbai|Hyderabad|Chennai|Delhi|Pune|Noida|Gurgaon|Kolkata|Ahmedabad|Remote|Pan-India)\b", text, re.I) else "",
                    "salary_min": lo,
                    "salary_max": hi,
                    "description": text[:1000] or None,
                })
            except Exception:
                continue
        return out

    def _extract_from_html(self, html: str) -> List[dict]:
        """Fallback: regex-pull job-detail anchors and their nearest heading text."""
        out = []
        for m in re.finditer(r'<a[^>]+href="([^"]*\/jobs\/[^"]*(?:-job|-internship|-vacancy|-opening)s?-\d+[^"]*)"[^>]*>(.*?)</a>', html, re.I | re.S):
            href = m.group(1)
            title = re.sub(r"<[^>]+>", " ", m.group(2)).strip()
            title = re.sub(r"\s+", " ", title)
            if not title:
                # Try title attribute
                tm = re.search(r'title="([^"]+)"', m.group(0), re.I)
                title = (tm.group(1) if tm else "").strip()
            if title:
                out.append({"url": url_prefixed(href), "title": title})
        # De-dup preserving order
        seen, dedup = set(), []
        for o in out:
            k = o["title"].lower()
            if k in seen:
                continue
            seen.add(k)
            dedup.append(o)
        return dedup


def url_prefixed(href: str) -> str:
    href = href or ""
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return "https://www.freshersworld.com" + href
    return "https://www.freshersworld.com/" + href


def line_company(text: str) -> str:
    """Best-effort: pick a plausible company line from card text."""
    for line in (text or "").splitlines():
        line = line.strip()
        if line and not re.search(r"(?:₹|INR|Salary|LPA|Exp|Years|Apply|View|Posted)", line, re.I):
            return line
    return ""
