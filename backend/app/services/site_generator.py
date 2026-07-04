from __future__ import annotations

import json
import shutil
from pathlib import Path

from slugify import slugify

from app.models import Business


TEMPLATE_DIR = Path("/app/site-template")
OUTPUT_DIR = Path("/app/.generated-sites")

BLUE_COLLAR_TERMS = [
    "plumb",
    "drain",
    "water heater",
    "electric",
    "hvac",
    "heating",
    "cooling",
    "roof",
    "construction",
    "contractor",
    "landscap",
    "lawn",
    "pest",
    "cleaning",
    "janitor",
    "garage door",
    "locksmith",
    "moving",
    "mover",
    "paint",
    "flooring",
    "concrete",
    "masonry",
    "carpentry",
    "auto repair",
    "mechanic",
    "towing",
]

RESTAURANT_TERMS = ["restaurant", "cafe", "pizza", "grill", "kitchen", "bistro", "bakery", "meal takeaway", "food"]


def repo_slug_for_business(business: Business) -> str:
    city = slugify(business.city or "local")
    name = slugify(business.name)
    slug = f"{name}-{city}"[:90].strip("-")
    return slug or f"business-{business.id}"


def business_context_text(business: Business) -> str:
    raw = business.raw_data or {}
    parts = [business.name, business.category or "", raw.get("searchKeyword") or "", raw.get("searchLocation") or ""]
    types = raw.get("types") or []
    if isinstance(types, list):
        parts.extend(str(item).replace("_", " ") for item in types)
    primary_type = raw.get("primaryType")
    if primary_type:
        parts.append(str(primary_type).replace("_", " "))
    primary_type_display_name = raw.get("primaryTypeDisplayName") or {}
    if isinstance(primary_type_display_name, dict):
        parts.append(primary_type_display_name.get("text") or "")
    return " ".join(part for part in parts if part).lower()


def infer_business_type(business: Business) -> str:
    text = business_context_text(business)
    # Most-specific classifiers first. This avoids a broad Google type like
    # "Restaurant" overriding the user's original "sushi restaurant" search.
    if any(word in text for word in ["sushi", "ramen", "izakaya", "japanese"]):
        return "sushi restaurant"
    if any(word in text for word in ["dentist", "dental", "orthodont"]):
        return "dental clinic"
    if any(word in text for word in ["plumb", "drain", "water heater"]):
        return "plumbing service"
    if any(word in text for word in ["electric", "hvac", "heating", "cooling", "roof", "construction", "contractor"]):
        return "blue-collar service business"
    if any(word in text for word in ["salon", "spa", "barber", "hair", "nail"]):
        return "salon"
    if any(word in text for word in ["gym", "fitness", "yoga", "pilates"]):
        return "fitness studio"
    if any(word in text for word in RESTAURANT_TERMS):
        return "restaurant"
    return business.category or ((business.raw_data or {}).get("searchKeyword")) or "local business"


def infer_design_style(business_type: str, context_text: str) -> str:
    lower_type = business_type.lower()
    if any(term in f"{lower_type} {context_text}" for term in BLUE_COLLAR_TERMS):
        return "rugged-blue-collar"
    if any(term in lower_type for term in ["sushi", "restaurant", "cafe", "bakery"]):
        return "hospitality"
    if any(term in lower_type for term in ["dental", "medical", "clinic"]):
        return "clean-clinical"
    if any(term in lower_type for term in ["salon", "spa", "beauty"]):
        return "polished-lifestyle"
    return "professional-local"


def business_type_defaults(business_type: str, design_style: str) -> dict:
    lower_type = business_type.lower()
    if "sushi" in lower_type:
        return {
            "services": ["Sushi and rolls", "Takeout and pickup", "Dine-in experience", "Party trays and group orders"],
            "cta": "Call to order or reserve a table",
            "subheadline": "A clean, mobile-friendly sushi restaurant site built around menu discovery, quick calls, and directions.",
            "designDirection": "Warm restaurant layout, appetizing sections, refined typography, moderate rounded corners only.",
        }
    if "restaurant" in lower_type:
        return {
            "services": ["Menu highlights", "Dine-in experience", "Takeout and pickup", "Group orders and catering"],
            "cta": "Call to order or reserve a table",
            "subheadline": "A clean, mobile-friendly restaurant site built around menu discovery, quick calls, and directions.",
            "designDirection": "Hospitality layout, clear menu/service blocks, tasteful visuals, moderate rounded corners only.",
        }
    if "dental" in lower_type:
        return {
            "services": ["Preventive care", "Cosmetic dentistry", "Emergency appointments", "Family dental services"],
            "cta": "Book an appointment",
            "subheadline": "A clear dental clinic site focused on appointments, services, trust, and location.",
            "designDirection": "Clean clinical layout, white space, calm trust-building sections, subtle rounded corners.",
        }
    if "plumbing" in lower_type or design_style == "rugged-blue-collar":
        return {
            "services": ["Emergency service calls", "Repairs and troubleshooting", "Installation help", "Residential and local service"],
            "cta": "Call for service",
            "subheadline": "A direct, hard-working service site focused on calls, service areas, and customer confidence.",
            "designDirection": "Blue-collar layout: strong blocky sections, square or low-radius corners, bold contact CTA, practical service cards, no soft startup/SaaS look.",
        }
    if "salon" in lower_type:
        return {
            "services": ["Hair and styling services", "Appointments", "Beauty treatments", "Location and contact"],
            "cta": "Book a visit",
            "subheadline": "A polished salon site built for bookings, service discovery, and mobile customers.",
            "designDirection": "Polished lifestyle layout, elegant typography, visual service sections, moderate rounded corners.",
        }
    return {
        "services": ["Mobile-first landing page", "Clear contact section", "Service highlights", "Fast Vercel hosting"],
        "cta": "Contact us today",
        "subheadline": "Fast, mobile-friendly, and focused on calls, directions, and new customers.",
        "designDirection": "Professional local-business layout. Choose styling based on the category, not a generic sushi/restaurant template.",
    }


def build_business_payload(business: Business, website_url: str | None = None) -> dict:
    raw = business.raw_data or {}
    search_keyword = raw.get("searchKeyword")
    context_text = business_context_text(business)
    business_type = infer_business_type(business)
    design_style = infer_design_style(business_type, context_text)
    defaults = business_type_defaults(business_type, design_style)
    return {
        "name": business.name,
        "category": business.category or search_keyword or business_type,
        "businessType": business_type,
        "designStyle": design_style,
        "designDirection": defaults["designDirection"],
        "searchKeyword": search_keyword,
        "searchLocation": raw.get("searchLocation") or business.city,
        "placeTypes": raw.get("types") or [],
        "googlePrimaryType": raw.get("primaryType"),
        "city": business.city,
        "phone": business.phone,
        "email": business.contacts[0].email if business.contacts else None,
        "address": business.address,
        "originalWebsite": business.website_url,
        "previewWebsite": website_url,
        "headline": f"A cleaner website concept for {business.name}",
        "subheadline": defaults["subheadline"],
        "services": defaults["services"],
        "cta": defaults["cta"],
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
