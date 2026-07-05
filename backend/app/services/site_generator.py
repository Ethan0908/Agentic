from __future__ import annotations

import json
import shutil
from pathlib import Path

from slugify import slugify

from app.models import Business


# Canonical generated-site template. The Docker compose file mounts the repo's
# site-template folder here, and every new website starts as a direct copy of it.
TEMPLATE_DIR = Path("/app/site-template")
OUTPUT_DIR = Path("/app/.generated-sites")


def repo_slug_for_business(business: Business) -> str:
    city = slugify(business.city or "local")
    name = slugify(business.name or f"business-{business.id}")
    slug = f"{name}-{city}"[:90].strip("-")
    return slug or f"business-{business.id}"


def _primary_type_display_name(raw_data: dict) -> str | None:
    value = raw_data.get("primaryTypeDisplayName")
    if isinstance(value, dict):
        return value.get("text")
    if isinstance(value, str):
        return value
    return None


def _first_email(business: Business) -> str | None:
    for contact in business.contacts or []:
        if contact.email:
            return contact.email
    return None


def build_business_payload(business: Business, website_url: str | None = None) -> dict:
    """Return only factual business data.

    Design strategy, copywriting, layout decisions, and sector research live in
    backend/app/prompts/website_generation_prompt.md. Keep this file clean.
    """
    raw_data = business.raw_data or {}
    return {
        "name": business.name,
        "category": business.category,
        "city": business.city,
        "address": business.address,
        "phone": business.phone,
        "email": _first_email(business),
        "originalWebsite": business.website_url,
        "previewWebsite": website_url,
        "searchKeyword": raw_data.get("searchKeyword"),
        "searchLocation": raw_data.get("searchLocation") or business.city,
        "placeTypes": raw_data.get("types") or [],
        "googlePrimaryType": raw_data.get("primaryType"),
        "googlePrimaryTypeDisplayName": _primary_type_display_name(raw_data),
        "rawData": raw_data,
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
