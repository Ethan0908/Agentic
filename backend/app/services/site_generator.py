"""Website generation service.

GitHub is the source of truth for this file. The Raspberry Pi should run a direct
copy of the repository instead of keeping separate local-only generator logic.

The generator no longer relies on one template and one huge prompt. It now:
1. normalizes business data,
2. selects a vertical-specific copy/default profile,
3. selects a design system,
4. creates a compact site plan,
5. writes business/design/section JSON into the generated site,
6. optionally launches Codex/Claude refinement,
7. writes a deterministic quality report before the site is treated as ready.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

try:
    from .agentic_site_builder import build_claude_agent_prompt, build_site_plan, run_claude_refinement, write_site_plan
    from .env_loader import load_local_env
    from .site_quality import QualityReport, assert_quality_gate, validate_generated_site, write_quality_report
except ImportError:  # pragma: no cover - lets this file run as a direct script during local debugging.
    from agentic_site_builder import build_claude_agent_prompt, build_site_plan, run_claude_refinement, write_site_plan
    from env_loader import load_local_env
    from site_quality import QualityReport, assert_quality_gate, validate_generated_site, write_quality_report


REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_FILE = REPO_ROOT / "backend" / "app" / "prompts" / "website_generation_prompt.md"
TEMPLATE_DIR = REPO_ROOT / "site-template"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "generated_sites"
DEFAULT_MINIMUM_QUALITY_SCORE = 75


@dataclass(frozen=True)
class GeneratedSite:
    """Result returned after rendering a website folder."""

    slug: str
    path: Path
    business_name: str
    design_system: str
    quality_score: int | None = None
    quality_report_path: Path | None = None


class SiteGenerationError(RuntimeError):
    """Raised when the site generator cannot safely complete a build step."""


def slugify(value: str, fallback: str = "generated-site") -> str:
    """Return a lowercase dash-separated slug safe for repos and folders."""

    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    return cleaned or fallback


def _string(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _list(value: Any, fallback: list[Any] | None = None) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return fallback or []
    return [value]


def _blob(raw: Mapping[str, Any]) -> str:
    return json.dumps(raw, ensure_ascii=False).lower()


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def detect_vertical(raw: Mapping[str, Any]) -> str:
    """Map loose lead data to a copy/design vertical.

    This is deterministic on purpose. Codex can still refine, but the baseline
    must already sound like the business instead of a generic local-service page.
    """

    text = _blob(raw)
    if _has_any(text, ("omakase", "sushi", "restaurant", "dining", "chef", "bar", "cafe", "catering", "tasting menu")):
        return "restaurant-hospitality"
    if _has_any(text, ("emergency", "urgent", "24/7", "same day", "sewer", "leak", "water damage", "locksmith", "towing")):
        return "emergency-service"
    if _has_any(text, ("clinic", "dental", "medical", "therapy", "chiropractor", "physio", "wellness", "doctor")):
        return "clinical-wellness"
    if _has_any(text, ("spa", "salon", "facial", "massage", "beauty", "lashes", "nails", "hair")):
        return "beauty-wellness"
    if _has_any(text, ("law", "legal", "accounting", "finance", "insurance", "consulting", "real estate", "mortgage", "advisory")):
        return "professional-advisory"
    if _has_any(text, ("plumbing", "hvac", "electrician", "roof", "cleaning", "repair", "contractor", "home service", "garage", "appliance")):
        return "home-service"
    if _has_any(text, ("software", "saas", "app", "ai", "marketing", "agency", "technology", "startup")):
        return "modern-growth"
    return "local-service"


def _page_copy_for_vertical(vertical: str, name: str, business_type: str, service_area: str) -> dict[str, Any]:
    common_cards = [
        {"title": "Clear next step", "description": "Visitors should know exactly what to send, ask, or book after reading the page."},
        {"title": "Specific details", "description": "The site should answer practical questions instead of relying on vague marketing language."},
        {"title": "Easy contact", "description": "The primary CTA stays visible and connected to the available contact method."},
    ]

    if vertical == "restaurant-hospitality":
        return {
            "panelLabel": "Dining path",
            "panelHeading": "A polished path from interest to reservation.",
            "servicesEyebrow": "Experience",
            "servicesHeading": f"A focused {business_type} experience in {service_area}.",
            "servicesIntro": f"The page gives guests the dining style, reservation path, and practical details they need before choosing {name}.",
            "standardEyebrow": "Dining standard",
            "standardHeading": "Make the visit feel considered before guests arrive.",
            "standardBody": "A strong restaurant site sets expectations around the experience, timing, party details, and contact path without inventing menu items, ratings, or availability.",
            "standardLink": "Start a reservation request →",
            "standardCards": [
                {"title": "Experience first", "description": "Guests quickly understand the style of dining and what makes the visit distinct."},
                {"title": "Reservation clarity", "description": "The CTA guides visitors toward the next booking or inquiry step."},
                {"title": "Useful details", "description": "Party size, timing, dietary questions, and private-event interest have a clear place to go."},
            ],
            "processHeading": "From interest to a confirmed dining plan.",
            "processIntro": "A simple reservation flow reduces hesitation and keeps important dining details organized before arrival.",
            "confidenceHeading": "What guests can expect before booking.",
            "confidenceIntro": "The site should make the experience feel intentional while staying honest about what has been confirmed.",
        }

    if vertical == "emergency-service":
        return {
            "panelLabel": "Urgent request flow",
            "panelHeading": "A direct path when the issue cannot wait.",
            "servicesEyebrow": "Urgent services",
            "servicesHeading": f"Fast, clear {business_type} support across {service_area}.",
            "servicesIntro": "Visitors can identify the problem, call or send details, and understand what information helps the team respond.",
            "standardEyebrow": "Response standard",
            "standardHeading": "Reduce panic with a clear first step.",
            "standardBody": "Emergency pages need direct CTAs, plain-language service cards, and no invented claims about availability, licensing, or guaranteed response times.",
            "standardLink": "Start the urgent request →",
            "standardCards": [
                {"title": "Problem first", "description": "Visitors can quickly match their issue to the right request path."},
                {"title": "Low friction", "description": "The primary contact action stays obvious on mobile and desktop."},
                {"title": "No fake guarantees", "description": "The copy stays useful without inventing response times or credentials."},
            ],
            "processHeading": "From urgent issue to the next practical step.",
            "processIntro": "The page tells people what to share so the request can be understood quickly.",
            "confidenceHeading": "What customers can expect during the first contact.",
            "confidenceIntro": "The focus is speed, clarity, and practical information, not exaggerated promises.",
        }

    if vertical == "professional-advisory":
        return {
            "panelLabel": "Advisory path",
            "panelHeading": "A composed path from question to consultation.",
            "servicesEyebrow": "Advisory services",
            "servicesHeading": f"Clear {business_type} guidance for {service_area}.",
            "servicesIntro": "The page should help prospective clients understand the advisory fit, next step, and information needed for a useful first conversation.",
            "standardEyebrow": "Client standard",
            "standardHeading": "Build confidence before the first conversation.",
            "standardBody": "Professional service pages need precise language, restrained design, and credible explanations without inventing credentials, rankings, or results.",
            "standardLink": "Request a consultation →",
            "standardCards": [
                {"title": "Fit first", "description": "The visitor understands whether the service area matches their situation."},
                {"title": "Clear intake", "description": "The CTA tells clients what to send or book for a useful next step."},
                {"title": "Credible restraint", "description": "The page avoids exaggerated outcomes and focuses on process clarity."},
            ],
            "processHeading": "From question to a defined consultation path.",
            "processIntro": "The flow helps visitors share enough context for a practical next conversation.",
            "confidenceHeading": "What clients can expect before contacting the office.",
            "confidenceIntro": "Trust comes from specificity, restraint, and a clear first step.",
        }

    if vertical in {"clinical-wellness", "beauty-wellness"}:
        return {
            "panelLabel": "Appointment path",
            "panelHeading": "A calm path from question to appointment.",
            "servicesEyebrow": "Services",
            "servicesHeading": f"Thoughtful {business_type} services in {service_area}.",
            "servicesIntro": "Visitors can understand the service options, appointment path, and details worth sharing before they book.",
            "standardEyebrow": "Care standard",
            "standardHeading": "Make the first step feel simple and reassuring.",
            "standardBody": "Health, wellness, and beauty sites need calm structure, accessible copy, and practical booking information without inventing clinical claims or outcomes.",
            "standardLink": "Start an appointment request →",
            "standardCards": [
                {"title": "Clear fit", "description": "Visitors can identify the service that matches their goal or concern."},
                {"title": "Comfortable booking", "description": "The CTA makes the next action feel obvious and low-pressure."},
                {"title": "Useful preparation", "description": "The page explains what details help before the appointment."},
            ],
            "processHeading": "From question to appointment clarity.",
            "processIntro": "A simple process helps people book or inquire without uncertainty.",
            "confidenceHeading": "What clients can expect before booking.",
            "confidenceIntro": "The site should feel calm, transparent, and specific to the service.",
        }

    if vertical == "modern-growth":
        return {
            "panelLabel": "Growth path",
            "panelHeading": "A sharper path from interest to qualified lead.",
            "servicesEyebrow": "Capabilities",
            "servicesHeading": f"Focused {business_type} support for {service_area}.",
            "servicesIntro": "The page should make the offer, audience, and next step immediately clear without SaaS buzzword filler.",
            "standardEyebrow": "Execution standard",
            "standardHeading": "Make the offer specific enough to evaluate quickly.",
            "standardBody": "Modern growth pages need direct positioning, concrete capability cards, and a CTA that moves visitors toward a useful conversation.",
            "standardLink": "Start the conversation →",
            "standardCards": common_cards,
            "processHeading": "From interest to a focused next step.",
            "processIntro": "The flow helps visitors share the right context for a useful project or product conversation.",
            "confidenceHeading": "What prospects can evaluate before contacting the team.",
            "confidenceIntro": "Specificity beats buzzwords; the page should clarify the problem, offer, and contact path.",
        }

    return {
        "panelLabel": "Service flow",
        "panelHeading": "Clear scope, practical next steps, and careful follow-through.",
        "servicesEyebrow": "Services",
        "servicesHeading": f"Practical {business_type} support for {service_area}.",
        "servicesIntro": "Tell the team what is happening, where the work is needed, and the timing. The response can start with the right context instead of a long back-and-forth.",
        "standardEyebrow": "Service standard",
        "standardHeading": "Clear communication before the work starts.",
        "standardBody": f"Good service is not only the final result. It is also how the request is handled, scoped, explained, and followed through. {name} keeps the experience focused on practical next steps.",
        "standardLink": "Start with a clear request →",
        "standardCards": common_cards,
        "processHeading": "From first request to a defined next step.",
        "processIntro": "A simple process helps visitors act without guessing what information to send or what happens after contact.",
        "confidenceHeading": "What customers can expect.",
        "confidenceIntro": "Visitors get the information they need before choosing the next step.",
    }


def _vertical_defaults(vertical: str, name: str, business_type: str, service_area: str) -> dict[str, Any]:
    if vertical == "restaurant-hospitality":
        return {
            "primaryCta": "Request a reservation",
            "secondaryCta": "Explore the experience",
            "heroEyebrow": f"{business_type.title()} in {service_area}",
            "heroHeadline": f"{name} gives {service_area} guests a more considered {business_type} experience.",
            "heroSubheadline": "A polished page for guests to understand the dining style, ask the right questions, and take the next step toward a reservation.",
            "services": [
                {"title": "Omakase dining", "description": "A focused dining experience shaped around seasonality, pacing, and guest expectations."},
                {"title": "Reservation inquiries", "description": "A direct path for guests to ask about timing, party size, and availability."},
                {"title": "Private dining interest", "description": "A clearer way for groups to share occasion details and request the right next step."},
                {"title": "Guest details", "description": "A practical place to raise dietary notes, timing questions, or special-occasion context before booking."},
            ],
            "proofPoints": [
                "Reservation-focused contact path",
                "Dining details clarified before arrival",
                f"Experience presented for {service_area} guests",
                "No fake menu claims or ratings",
            ],
            "processSteps": [
                {"title": "Share the occasion", "description": "Send the preferred date, party size, and any dining details that matter."},
                {"title": "Confirm the path", "description": "The next step can be a reservation inquiry, private-dining question, or direct contact."},
                {"title": "Arrive with clarity", "description": "Guests understand the experience and the important details before arrival."},
            ],
            "faqs": [
                {"question": f"How do I contact {name} about a reservation?", "answer": "Use the main request button to share preferred timing, party size, and contact details."},
                {"question": "Can I ask about dietary restrictions or allergies?", "answer": "Yes. Share important dietary notes before booking so the team can explain what is possible."},
                {"question": "Do you handle private dining or special occasions?", "answer": "Send the group size, occasion, and preferred timing so the team can confirm the right next step."},
            ],
            "offer": "Start with a reservation or dining inquiry that includes the details guests actually need to share.",
            "guarantee": "A clear guest inquiry before the visit.",
        }

    if vertical == "emergency-service":
        return {
            "primaryCta": "Call now",
            "secondaryCta": "See urgent services",
            "heroEyebrow": f"Urgent {business_type} in {service_area}",
            "heroHeadline": f"{name} helps {service_area} customers take the next step when {business_type} issues cannot wait.",
            "heroSubheadline": "A phone-first service page built around fast understanding, direct contact, and practical information.",
            "services": [
                {"title": "Urgent assessment", "description": "Share what happened, where it is happening, and how quickly the issue is changing."},
                {"title": "Problem isolation", "description": "The request path focuses on the issue, location, and immediate next step."},
                {"title": "Repair path", "description": "The page guides visitors toward the right contact action without inflated promises."},
                {"title": "Follow-up details", "description": "Photos, access notes, and timing help the team understand the request."},
            ],
            "proofPoints": ["Phone-first CTA", "Issue and location captured clearly", "No fake response-time claims", f"Service context for {service_area}"],
            "processSteps": [
                {"title": "Call or send details", "description": "Share the location, issue, timing, and any safety concerns."},
                {"title": "Clarify the next step", "description": "The request is sorted into the most practical response path."},
                {"title": "Move toward resolution", "description": "The visitor understands what happens next without guessing."},
            ],
            "faqs": [
                {"question": "What should I include when I contact you?", "answer": "Share the address or area, a short description, photos if useful, and whether the issue is getting worse."},
                {"question": "Can I call instead of filling out a form?", "answer": "Yes. If a phone number is available, calling is the fastest first step for urgent issues."},
            ],
            "offer": "Get the urgent issue into a clear request path.",
            "guarantee": "Clear communication before the next step is set.",
        }

    if vertical == "professional-advisory":
        return {
            "primaryCta": "Request a consultation",
            "secondaryCta": "Review services",
            "heroEyebrow": f"{business_type.title()} in {service_area}",
            "heroHeadline": f"{name} helps {service_area} clients turn complex questions into a clearer next step.",
            "heroSubheadline": "A restrained, credible page built around fit, intake, and a practical consultation path.",
            "services": [
                {"title": "Initial consultation", "description": "Share the situation, goal, and timeline so the right next step can be identified."},
                {"title": "Advisory support", "description": "A practical path for questions that need context, judgment, and clear communication."},
                {"title": "Document or case review", "description": "Visitors can explain what they have and what they need help understanding."},
                {"title": "Ongoing guidance", "description": "A route for clients who need continued support after the first conversation."},
            ],
            "proofPoints": ["Consultation-focused CTA", "Clear intake expectations", "No invented credentials or outcomes", f"Client context for {service_area}"],
            "processSteps": [
                {"title": "Share the question", "description": "Send the main issue, timing, and any relevant context."},
                {"title": "Confirm fit", "description": "The next step is matched to the service area and available contact path."},
                {"title": "Start the consultation path", "description": "Move into a conversation with clearer expectations."},
            ],
            "faqs": [
                {"question": "What should I include in my inquiry?", "answer": "Share the general topic, timeline, location, and what outcome or answer you are looking for."},
                {"question": "Does contacting the office create a client relationship?", "answer": "No. A formal relationship should only be treated as started after the business confirms it directly."},
            ],
            "offer": "Request a consultation path based on your situation and timing.",
            "guarantee": "A clear first conversation path.",
        }

    if vertical in {"clinical-wellness", "beauty-wellness"}:
        return {
            "primaryCta": "Request an appointment",
            "secondaryCta": "View services",
            "heroEyebrow": f"{business_type.title()} in {service_area}",
            "heroHeadline": f"{name} helps {service_area} clients choose the right {business_type} next step with less guesswork.",
            "heroSubheadline": "A calm, appointment-focused page that explains services, preparation, and how to get started.",
            "services": [
                {"title": "Service consultation", "description": "Share the goal, concern, or preferred service so the right path can be suggested."},
                {"title": "Appointment booking", "description": "A direct route for clients ready to ask about timing and availability."},
                {"title": "Preparation guidance", "description": "The page explains what details are useful before a visit."},
                {"title": "Follow-up questions", "description": "A clear place to ask practical questions before booking."},
            ],
            "proofPoints": ["Appointment-focused CTA", "Calm service explanation", "No invented medical or outcome claims", f"Client context for {service_area}"],
            "processSteps": [
                {"title": "Share your goal", "description": "Send the service interest, timing, and any details that help prepare the visit."},
                {"title": "Confirm the appointment path", "description": "The next step can be a booking, consultation, or direct question."},
                {"title": "Arrive prepared", "description": "Clients know what information matters before the appointment."},
            ],
            "faqs": [
                {"question": "What should I share before booking?", "answer": "Send the service you are interested in, preferred timing, and any relevant questions or concerns."},
                {"question": "Can I ask questions before making an appointment?", "answer": "Yes. Use the contact path to ask what service or appointment type makes sense."},
            ],
            "offer": "Request an appointment path with the details needed to get started.",
            "guarantee": "A clear booking inquiry before the visit.",
        }

    return {
        "primaryCta": "Request a quote",
        "secondaryCta": "See services",
        "heroEyebrow": f"{business_type.title()} in {service_area}",
        "heroHeadline": f"{name} helps {service_area} customers get {business_type} work done with a clearer path from first contact to next step.",
        "heroSubheadline": "A focused service page that explains what to send, what happens next, and how to contact the business without extra friction.",
        "services": [
            {"title": "Assessment", "description": "Understand the issue, scope, and next step before work begins."},
            {"title": "Service work", "description": "Practical work completed with clear communication and tidy follow-through."},
            {"title": "Installation or setup", "description": "Planned work with attention to fit, finish, and long-term reliability."},
            {"title": "Maintenance", "description": "Preventive service that helps reduce surprise problems later."},
        ],
        "proofPoints": ["Clear scope before work starts", "Practical scheduling and communication", f"Service across {service_area}", "Straightforward next step"],
        "processSteps": [
            {"title": "Tell us what you need", "description": "Share the issue, location, and timing so the request can be scoped properly."},
            {"title": "Get a clear next step", "description": "Receive a practical recommendation, quote path, or booking option."},
            {"title": "Complete the work", "description": "The job is handled with clear communication from start to finish."},
        ],
        "faqs": [
            {"question": f"Do you serve {service_area}?", "answer": f"Yes. {name} works with customers across {service_area}. Contact the team with your address or project details to confirm availability."},
            {"question": "How do I get pricing?", "answer": "Send a few details about the work needed. The team can explain the next step and whether a quote, assessment, or booking makes the most sense."},
            {"question": "What should I prepare before contacting you?", "answer": "A short description, photos if available, the property location, and your preferred timing are usually enough to start."},
        ],
        "offer": "Request a practical quote path based on your project details.",
        "guarantee": "Clear communication before work begins.",
    }


def _public_image_url(value: Any) -> str:
    text = _string(value)
    if not text:
        return ""
    if not re.match(r"^https?://", text, flags=re.IGNORECASE):
        return ""
    if any(marker in text.lower() for marker in ("data:image", "base64,", "schema.org")):
        return ""
    return text


def _photo_list(raw: Mapping[str, Any], business_name: str) -> list[dict[str, str]]:
    """Return a small, safe list of public business photos.

    Photos should come from lead data, the business's own site, or another public
    source attached to that business. The generator should not invent stock photos
    or hotlink unrelated imagery just to make the page look rich.
    """

    sources: list[Any] = []
    for key in (
        "photos",
        "images",
        "photo_urls",
        "photoUrls",
        "image_urls",
        "imageUrls",
        "gallery",
        "business_photos",
        "businessPhotos",
        "website_images",
        "websiteImages",
        "scraped_images",
        "scrapedImages",
    ):
        sources.extend(_list(raw.get(key)))

    hero_candidates = _list(raw.get("hero_image") or raw.get("heroImage") or raw.get("cover_image") or raw.get("coverImage"))
    sources = hero_candidates + sources

    photos: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in sources:
        if isinstance(item, Mapping):
            url = _public_image_url(item.get("url") or item.get("src") or item.get("secure_url") or item.get("image"))
            alt = _string(item.get("alt") or item.get("caption") or item.get("title"), f"{business_name} photo")
            caption = _string(item.get("caption") or item.get("title"))
            kind = _string(item.get("kind") or item.get("type"), "business-photo")
            source = _string(item.get("source") or item.get("credit"))
        else:
            url = _public_image_url(item)
            alt = f"{business_name} photo"
            caption = ""
            kind = "business-photo"
            source = ""

        if not url or url in seen:
            continue
        seen.add(url)
        photo = {"url": url, "alt": alt, "kind": kind}
        if caption:
            photo["caption"] = caption
        if source:
            photo["source"] = source
        photos.append(photo)
        if len(photos) >= 8:
            break

    return photos


def normalize_business_profile(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize loose lead data into the schema consumed by the template.

    The template intentionally uses a small, stable schema so generated sites do
    not break when the lead data is incomplete. Never invent hard proof such as
    licences, awards, review counts, warranties, or years in business.
    """

    name = _string(raw.get("name") or raw.get("business_name"), "Local Service Company")
    business_type = _string(raw.get("business_type") or raw.get("businessType") or raw.get("category"), "local service")
    city = _string(raw.get("city") or raw.get("location"), "your area")
    service_area = _string(raw.get("service_area") or raw.get("serviceArea"), city)
    phone = _string(raw.get("phone") or raw.get("phone_number"))
    email = _string(raw.get("email"))
    website = _string(raw.get("website") or raw.get("url"))
    photos = _photo_list(raw, name)
    vertical = _string(raw.get("vertical") or raw.get("verticalProfile"), detect_vertical(raw))
    defaults = _vertical_defaults(vertical, name, business_type, service_area)
    page_copy = defaults | _page_copy_for_vertical(vertical, name, business_type, service_area)
    page_copy.update(raw.get("pageCopy") if isinstance(raw.get("pageCopy"), Mapping) else {})

    primary_cta = _string(raw.get("primary_cta") or raw.get("primaryCta"), defaults["primaryCta"])
    secondary_cta = _string(raw.get("secondary_cta") or raw.get("secondaryCta"), defaults["secondaryCta"])

    services = _list(raw.get("services")) or defaults["services"]
    proof_points = _list(raw.get("proof_points") or raw.get("proofPoints")) or defaults["proofPoints"]
    process_steps = _list(raw.get("process_steps") or raw.get("processSteps")) or defaults["processSteps"]
    faqs = _list(raw.get("faqs") or raw.get("faq")) or defaults["faqs"]
    reviews = _list(raw.get("reviews") or raw.get("testimonials"))

    return {
        "name": name,
        "slug": slugify(_string(raw.get("slug"), name)),
        "vertical": vertical,
        "businessType": business_type,
        "city": city,
        "serviceArea": service_area,
        "phone": phone,
        "email": email,
        "website": website,
        "primaryCta": primary_cta,
        "secondaryCta": secondary_cta,
        "hero": {
            "eyebrow": _string(raw.get("eyebrow"), defaults["heroEyebrow"]),
            "headline": _string(raw.get("headline"), defaults["heroHeadline"]),
            "subheadline": _string(raw.get("subheadline"), defaults["heroSubheadline"]),
        },
        "heroImage": photos[0] if photos else None,
        "photos": photos,
        "pageCopy": page_copy,
        "proofPoints": proof_points,
        "services": services,
        "processSteps": process_steps,
        "reviews": reviews,
        "faqs": faqs,
        "offer": _string(raw.get("offer"), defaults["offer"]),
        "guarantee": _string(raw.get("guarantee"), defaults["guarantee"]),
        "brandTone": _string(raw.get("brand_tone") or raw.get("brandTone"), "premium, direct, calm, trustworthy"),
    }


def render_site_from_template(
    raw_business: Mapping[str, Any],
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    overwrite: bool = True,
) -> GeneratedSite:
    """Copy the canonical template and write compact plan files.

    This still uses one canonical codebase, but it is no longer one visual
    template. `design.json` and `sections.json` select different patterns.
    """

    if not TEMPLATE_DIR.exists():
        raise SiteGenerationError(f"Missing canonical template folder: {TEMPLATE_DIR}")

    business = normalize_business_profile(raw_business)
    site_plan = build_site_plan(business)
    slug = slugify(business["slug"])
    target = Path(output_dir) / slug

    if target.exists():
        if not overwrite:
            raise SiteGenerationError(f"Target site already exists: {target}")
        shutil.rmtree(target)

    shutil.copytree(TEMPLATE_DIR, target)

    data_dir = target / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "business.json").write_text(
        json.dumps(business, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_site_plan(target, site_plan)

    return GeneratedSite(
        slug=slug,
        path=target,
        business_name=business["name"],
        design_system=site_plan.design["id"],
    )


def build_codex_instruction(raw_business: Mapping[str, Any]) -> str:
    """Build the exact instruction sent to Codex for optional refinement."""

    if not PROMPT_FILE.exists():
        raise SiteGenerationError(f"Missing prompt file: {PROMPT_FILE}")

    business = normalize_business_profile(raw_business)
    site_plan = build_site_plan(business)
    prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()
    return (
        f"{prompt}\n\n"
        "## Compact site plan JSON\n"
        "```json\n"
        f"{json.dumps(site_plan.as_dict(), ensure_ascii=False, separators=(',', ':'))}\n"
        "```\n\n"
        "Refine only where it materially improves quality, conversion, copy, responsiveness, performance, or maintainability. "
        "The baseline already contains vertical-specific copy; improve it, do not flatten it back into generic service copy. "
        "Use supplied business photos when present; never add unrelated stock photos or unverifiable claims. "
        "Do not invent awards, review counts, menu items, licences, response times, prices, or guarantees. "
        "After edits, preserve data/business.json, data/design.json, data/sections.json, and ensure the project builds.\n"
    )


def run_codex_refinement(site_path: Path, instruction: str, codex_command: str = "codex", timeout_seconds: int = 1800) -> None:
    """Optionally run Codex inside a generated site folder.

    `.env` and `.env.local` are loaded and forwarded to the Codex subprocess, so
    local OAuth/API variables can be used without hardcoding secrets.
    """

    if not site_path.exists():
        raise SiteGenerationError(f"Cannot refine missing site path: {site_path}")

    subprocess.run(
        [codex_command, "exec", instruction],
        cwd=site_path,
        check=True,
        text=True,
        env=load_local_env(),
        timeout=timeout_seconds,
    )


def _quality_checked_result(generated: GeneratedSite, minimum_quality_score: int, strict_quality: bool) -> GeneratedSite:
    try:
        report: QualityReport
        if strict_quality:
            report = assert_quality_gate(generated.path, minimum_score=minimum_quality_score)
        else:
            report = validate_generated_site(generated.path, minimum_score=minimum_quality_score)
            write_quality_report(generated.path, report)
    except ValueError as exc:
        raise SiteGenerationError(str(exc)) from exc

    return GeneratedSite(
        slug=generated.slug,
        path=generated.path,
        business_name=generated.business_name,
        design_system=generated.design_system,
        quality_score=report.score,
        quality_report_path=generated.path / "data" / "quality-report.json",
    )


def generate_site(
    raw_business: Mapping[str, Any],
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    refine_with_codex: bool = False,
    refine_with_claude: bool = False,
    minimum_quality_score: int = DEFAULT_MINIMUM_QUALITY_SCORE,
    strict_quality: bool = True,
) -> GeneratedSite:
    """Render a premium baseline website and optionally refine with agents."""

    business = normalize_business_profile(raw_business)
    site_plan = build_site_plan(business)
    generated = render_site_from_template(business, output_dir=output_dir)

    if refine_with_codex:
        instruction = build_codex_instruction(business)
        run_codex_refinement(generated.path, instruction)

    if refine_with_claude:
        run_claude_refinement(site_plan, generated.path)

    return _quality_checked_result(generated, minimum_quality_score=minimum_quality_score, strict_quality=strict_quality)


def build_claude_instruction_preview(raw_business: Mapping[str, Any], target_path: Path | str = "generated_sites/<slug>") -> str:
    """Return the compact Claude Code orchestration prompt without running it."""

    business = normalize_business_profile(raw_business)
    return build_claude_agent_prompt(build_site_plan(business), Path(target_path))
