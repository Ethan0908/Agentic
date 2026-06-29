from __future__ import annotations

import json
import shutil
from pathlib import Path

from slugify import slugify

from app.models import Business


TEMPLATE_DIR = Path("/app/site-template")
OUTPUT_DIR = Path("/app/.generated-sites")


def repo_slug_for_business(business: Business) -> str:
    city = slugify(business.city or "local")
    name = slugify(business.name)
    return f"lead-{name}-{city}"[:90].strip("-")


def build_business_payload(business: Business, website_url: str | None = None) -> dict:
    return {
        "name": business.name,
        "category": business.category or "Local Business",
        "city": business.city,
        "phone": business.phone,
        "email": business.contacts[0].email if business.contacts else None,
        "address": business.address,
        "originalWebsite": business.website_url,
        "previewWebsite": website_url,
        "headline": f"A cleaner website concept for {business.name}",
        "subheadline": "Fast, mobile-friendly, and focused on calls, directions, and new customers.",
        "services": [
            "Mobile-first landing page",
            "Clear contact section",
            "Simple service highlights",
            "Fast Vercel hosting",
        ],
        "cta": "Contact us today",
    }


def generate_local_site(business: Business) -> dict:
    if not TEMPLATE_DIR.exists():
        raise FileNotFoundError(f"Site template folder not found: {TEMPLATE_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = repo_slug_for_business(business)
    destination = OUTPUT_DIR / slug

    if destination.exists():
        shutil.rmtree(destination)

    shutil.copytree(TEMPLATE_DIR, destination)
    payload = build_business_payload(business)
    (destination / "business.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return {
        "slug": slug,
        "local_path": str(destination),
        "business_json": payload,
    }
