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


def _city_phrase(city: str | None) -> str:
    return f" in {city}" if city else ""


def business_type_defaults(business_type: str, design_style: str, business_name: str, city: str | None) -> dict:
    lower_type = business_type.lower()
    city_phrase = _city_phrase(city)

    if "sushi" in lower_type:
        return {
            "headline": f"Sushi, takeout, and dine-in for {business_name}",
            "services": ["Sushi rolls and chef selections", "Takeout and pickup", "Dine-in service", "Party trays and group orders"],
            "cta": "Call to order or reserve",
            "subheadline": f"A mobile-friendly sushi restaurant site for customers looking for menus, pickup, directions, and quick contact{city_phrase}.",
            "designDirection": "Warm restaurant layout, appetizing sections, refined typography, moderate rounded corners only.",
        }
    if "restaurant" in lower_type:
        return {
            "headline": f"A better local restaurant site for {business_name}",
            "services": ["Menu highlights", "Dine-in information", "Takeout and pickup", "Location and contact"],
            "cta": "Call for current hours or ordering",
            "subheadline": f"A clear restaurant site built around menu discovery, quick calls, and directions{city_phrase}.",
            "designDirection": "Hospitality layout, clear menu/service blocks, tasteful visuals, moderate rounded corners only.",
        }
    if "dental" in lower_type:
        return {
            "headline": f"Patient-focused dental care at {business_name}",
            "services": ["Preventive care", "Cosmetic dentistry", "Emergency appointments", "Family dental services"],
            "cta": "Call to book an appointment",
            "subheadline": f"A clean dental clinic site focused on appointments, services, trust, and location{city_phrase}.",
            "designDirection": "Clean clinical layout, white space, calm trust-building sections, subtle corners.",
        }
    if "plumbing" in lower_type:
        return {
            "headline": f"Reliable plumbing help from {business_name}",
            "services": ["Emergency plumbing calls", "Drain and leak troubleshooting", "Water heater help", "Residential service visits"],
            "cta": "Call for plumbing service",
            "subheadline": f"A direct service-business site focused on urgent calls, clear service areas, and customer confidence{city_phrase}.",
            "designDirection": "Blue-collar layout: strong blocky sections, square or low-radius corners, bold contact CTA, practical service cards, no soft startup/SaaS look.",
        }
    if design_style == "rugged-blue-collar":
        return {
            "headline": f"Dependable local service from {business_name}",
            "services": ["Service calls", "Repairs and troubleshooting", "Installation help", "Residential and local service"],
            "cta": "Call for service",
            "subheadline": f"A practical service-company site focused on phone calls, service areas, and clear next steps{city_phrase}.",
            "designDirection": "Blue-collar layout: strong blocky sections, square or low-radius corners, bold contact CTA, practical service cards, no soft startup/SaaS look.",
        }
    if "salon" in lower_type:
        return {
            "headline": f"Book services with {business_name}",
            "services": ["Hair and styling services", "Appointments", "Beauty treatments", "Location and contact"],
            "cta": "Call to book a visit",
            "subheadline": f"A polished salon site built for bookings, service discovery, and mobile customers{city_phrase}.",
            "designDirection": "Polished lifestyle layout, elegant typography, visual service sections, moderate rounded corners.",
        }
    if "fitness" in lower_type:
        return {
            "headline": f"Train with {business_name}",
            "services": ["Classes or training", "Membership information", "Schedule inquiries", "Location and contact"],
            "cta": "Call to ask about training",
            "subheadline": f"A fitness site focused on programs, calls, and getting new members through the door{city_phrase}.",
            "designDirection": "Energetic local-business layout with strong CTAs and practical program sections.",
        }
    return {
        "headline": f"A clearer website for {business_name}",
        "services": ["What you offer", "Contact and location", "Service highlights", "Fast mobile experience"],
        "cta": "Contact us today",
        "subheadline": f"A mobile-first local-business site focused on calls, directions, and new customers{city_phrase}.",
        "designDirection": "Professional local-business layout. Choose styling based on the category, not a generic sushi/restaurant template.",
    }


def build_business_payload(business: Business, website_url: str | None = None) -> dict:
    raw = business.raw_data or {}
    search_keyword = raw.get("searchKeyword")
    context_text = business_context_text(business)
    business_type = infer_business_type(business)
    design_style = infer_design_style(business_type, context_text)
    defaults = business_type_defaults(business_type, design_style, business.name, business.city)
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
        "headline": defaults["headline"],
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
