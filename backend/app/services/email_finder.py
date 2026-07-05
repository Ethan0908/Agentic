from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
COMMON_CONTACT_PATHS = ["/", "/contact", "/contact-us", "/about", "/about-us", "/team"]


@dataclass
class EmailFinding:
    email: str
    source_url: str
    confidence: int


def _normalise_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        return f"https://{url}"
    return url


def _same_domain(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower().replace("www.", "") == urlparse(b).netloc.lower().replace("www.", "")


def _extract_emails(text: str) -> set[str]:
    emails = {match.group(0).strip(".,;:()[]{}<>").lower() for match in EMAIL_RE.finditer(text)}
    return {email for email in emails if not email.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))}


def _candidate_urls(homepage: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = {urljoin(homepage, path) for path in COMMON_CONTACT_PATHS}

    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(" ", strip=True).lower()
        if "contact" in href.lower() or "about" in href.lower() or "team" in href.lower() or "contact" in text:
            absolute = urljoin(homepage, href)
            if _same_domain(homepage, absolute):
                urls.add(absolute)

    return list(urls)[:10]


async def find_public_emails(website_url: str) -> list[EmailFinding]:
    homepage = _normalise_url(website_url)
    findings: dict[str, EmailFinding] = {}

    async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers={"User-Agent": "AgenticLeadResearch/0.1"}) as client:
        try:
            home_response = await client.get(homepage)
            home_response.raise_for_status()
        except httpx.HTTPError:
            return []

        urls = _candidate_urls(str(home_response.url), home_response.text)

        for url in urls:
            try:
                response = await client.get(url)
                if response.status_code >= 400:
                    continue
            except httpx.HTTPError:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            visible_text = soup.get_text(" ", strip=True)
            mailto_emails = set()
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.lower().startswith("mailto:"):
                    mailto_emails.update(_extract_emails(href.replace("mailto:", "")))

            text_emails = _extract_emails(visible_text)
            for email in mailto_emails | text_emails:
                confidence = 90 if email in mailto_emails else 70
                if "contact" in url.lower():
                    confidence += 5
                existing = findings.get(email)
                if not existing or confidence > existing.confidence:
                    findings[email] = EmailFinding(email=email, source_url=url, confidence=min(confidence, 100))

    return sorted(findings.values(), key=lambda item: item.confidence, reverse=True)
