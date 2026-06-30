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
    slug = f"{name}-{city}"[:90].strip("-")
    return slug or f"business-{business.id}"


def infer_business_type(name: str, category: str | None) -> str:
    text = f"{name} {category or ''}".lower()
    if any(word in text for word in ["sushi", "ramen", "izakaya", "japanese"]):
        return "sushi restaurant"
    if any(word in text for word in ["restaurant", "cafe", "pizza", "grill", "kitchen", "bistro", "bakery"]):
        return "restaurant"
    if any(word in text for word in ["dentist", "dental", "orthodont"]):
        return "dental clinic"
    if any(word in text for word in ["plumb", "drain", "water heater"]):
        return "plumbing service"
    if any(word in text for word in ["salon", "spa", "barber", "hair", "nail"]):
        return "salon"
    if any(word in text for word in ["gym", "fitness", "yoga", "pilates"]):
        return "fitness studio"
    return category or "local business"


def business_type_defaults(business_type: str) -> dict:
    lower_type = business_type.lower()
    if "sushi" in lower_type or "restaurant" in lower_type:
        return {
            "services": ["Dine-in experience", "Takeout and pickup", "Menu highlights", "Group orders and catering"],
            "cta": "Call to order or reserve a table",
            "subheadline": "A clean, mobile-friendly restaurant site built around menu discovery, quick calls, and directions.",
        }
    if "dental" in lower_type:
        return {
            "services": ["Preventive care", "Cosmetic dentistry", "Emergency appointments", "Family dental services"],
            "cta": "Book an appointment",
            "subheadline": "A clear dental clinic site focused on appointments, services, trust, and location.",
        }
    if "plumbing" in lower_type:
        return {
            "services": ["Emergency plumbing", "Drain cleaning", "Water heater help", "Residential service calls"],
            "cta": "Call for service",
            "subheadline": "A fast service-business site focused on urgent calls, service areas, and customer confidence.",
        }
    if "salon" in lower_type:
        return {
            "services": ["Hair and styling services", "Appointments", "Beauty treatments", "Location and contact"],
            "cta": "Book a visit",
            "subheadline": "A polished salon site built for bookings, service discovery, and mobile customers.",
        }
    return {
        "services": ["Mobile-first landing page", "Clear contact section", "Service highlights", "Fast Vercel hosting"],
        "cta": "Contact us today",
        "subheadline": "Fast, mobile-friendly, and focused on calls, directions, and new customers.",
    }


def build_business_payload(business: Business, website_url: str | None = None) -> dict:
    business_type = infer_business_type(business.name, business.category)
    defaults = business_type_defaults(business_type)
    return {
        "name": business.name,
        "category": business.category or business_type,
        "businessType": business_type,
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
