"""Website generation service.

GitHub is the source of truth for this file. The Raspberry Pi should run a direct
copy of the repository instead of keeping separate local-only generator logic.

The generator now creates a strong baseline before Codex/Claude refinement:
1. normalize lead data,
2. detect the business vertical,
3. create vertical-specific copy defaults,
4. select a design system and section plan,
5. render the canonical template,
6. optionally run Codex/Claude,
7. write a deterministic quality report before the site is treated as ready.
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
    """Map loose lead data to a copy/design vertical."""

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


def _common_page_copy(name: str, business_type: str, service_area: str) -> dict[str, Any]:
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
        "standardCards": [
            {"title": "Clear next step", "description": "Visitors should know exactly what to send, ask, or book after reading the page."},
            {"title": "Specific details", "description": "The site should answer practical questions instead of relying on vague marketing language."},
            {"title": "Easy contact", "description": "The primary CTA stays visible and connected to the available contact method."},
        ],
        "processHeading": "From first request to a defined next step.",
        "processIntro": "A simple process helps visitors act without guessing what information to send or what happens after contact.",
        "confidenceHeading": "What customers can expect.",
        "confidenceIntro": "Visitors get the information they need before choosing the next step.",
    }


def _vertical_defaults(vertical: str, name: str, business_type: str, service_area: str) -> dict[str, Any]:
    """Return public-facing defaults for a vertical.

    Internal QA language stays in `site_quality.py`; customer-facing proof points
    must sound natural on a real business website.
    """

    base = {
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
        "pageCopy": _common_page_copy(name, business_type, service_area),
    }

    if vertical == "restaurant-hospitality":
        page_copy = _common_page_copy(name, business_type, service_area) | {
            "panelLabel": "Dining path",
            "panelHeading": "A polished path from interest to reservation.",
            "servicesEyebrow": "Experience",
            "servicesHeading": f"A focused {business_type} experience in {service_area}.",
            "servicesIntro": f"The page gives guests the dining style, reservation path, and practical details they need before choosing {name}.",
            "standardEyebrow": "Dining standard",
            "standardHeading": "Make the visit feel considered before guests arrive.",
            "standardBody": "A strong restaurant site sets expectations around the experience, timing, party details, and contact path without overpromising details that have not been provided.",
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
        return base | {
            "primaryCta": "Request a reservation",
            "secondaryCta": "Explore the experience",
            "heroHeadline": f"{name} gives {service_area} guests a more considered {business_type} experience.",
            "heroSubheadline": "A polished page for guests to understand the dining style, ask the right questions, and take the next step toward a reservation.",
            "services": [
                {"title": "Omakase dining", "description": "A focused dining experience shaped around seasonality, pacing, and guest expectations."},
                {"title": "Reservation inquiries", "description": "A direct path for guests to ask about timing, party size, and availability."},
                {"title": "Private dining interest", "description": "A clearer way for groups to share occasion details and request the right next step."},
                {"title": "Guest details", "description": "A practical place to raise dietary notes, timing questions, or special-occasion context before booking."},
            ],
            "proofPoints": ["Reservation-focused contact path", "Dining details clarified before arrival", f"Experience presented for {service_area} guests", "Honest details without inflated claims"],
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
            "pageCopy": page_copy,
        }

    if vertical == "emergency-service":
        page_copy = _common_page_copy(name, business_type, service_area) | {
            "panelLabel": "Urgent request flow",
            "panelHeading": "A direct path when the issue cannot wait.",
            "servicesEyebrow": "Urgent services",
            "servicesHeading": f"Fast, clear {business_type} support across {service_area}.",
            "servicesIntro": "Visitors can identify the problem, call or send details, and understand what information helps the team respond.",
            "standardEyebrow": "Response standard",
            "standardHeading": "Reduce panic with a clear first step.",
            "standardBody": "Emergency pages need direct CTAs, plain-language service cards, and realistic expectations about what happens after first contact.",
            "standardLink": "Start the urgent request →",
            "standardCards": [
                {"title": "Problem first", "description": "Visitors can quickly match their issue to the right request path."},
                {"title": "Low friction", "description": "The primary contact action stays obvious on mobile and desktop."},
                {"title": "Realistic expectations", "description": "The copy stays useful while keeping promises grounded in the provided information."},
            ],
            "processHeading": "From urgent issue to the next practical step.",
            "processIntro": "The page tells people what to share so the request can be understood quickly.",
        }
        return base | {
            "primaryCta": "Call now",
            "secondaryCta": "See urgent services",
            "heroEyebrow": f"Urgent {business_type} in {service_area}",
            "heroSubheadline": "A phone-first service page built around fast understanding, direct contact, and practical information.",
            "proofPoints": ["Phone-first CTA", "Issue and location captured clearly", "Clear expectations before next steps", f"Service context for {service_area}"],
            "pageCopy": page_copy,
        }

    if vertical == "professional-advisory":
        page_copy = _common_page_copy(name, business_type, service_area) | {
            "panelLabel": "Advisory path",
            "panelHeading": "A composed path from question to consultation.",
            "servicesEyebrow": "Advisory services",
            "servicesHeading": f"Clear {business_type} guidance for {service_area}.",
            "servicesIntro": "The page should help prospective clients understand the advisory fit, next step, and information needed for a useful first conversation.",
            "standardEyebrow": "Client standard",
            "standardHeading": "Build confidence before the first conversation.",
            "standardBody": "Professional service pages need precise language, restrained design, and credible explanations without exaggerated outcomes.",
            "standardLink": "Request a consultation →",
            "standardCards": [
                {"title": "Fit first", "description": "The visitor understands whether the service area matches their situation."},
                {"title": "Clear intake", "description": "The CTA tells clients what to send or book for a useful next step."},
                {"title": "Credible restraint", "description": "The page focuses on process clarity and avoids overstatement."},
            ],
        }
        return base | {
            "primaryCta": "Request a consultation",
            "secondaryCta": "Review services",
            "heroSubheadline": "A restrained, credible page built around fit, intake, and a practical consultation path.",
            "services": [
                {"title": "Initial consultation", "description": "Share the situation, goal, and timeline so the right next step can be identified."},
                {"title": "Advisory support", "description": "A practical path for questions that need context, judgment, and clear communication."},
                {"title": "Document or case review", "description": "Visitors can explain what they have and what they need help understanding."},
                {"title": "Ongoing guidance", "description": "A route for clients who need continued support after the first conversation."},
            ],
            "proofPoints": ["Consultation-focused CTA", "Clear intake expectations", "Credible language and restrained claims", f"Client context for {service_area}"],
            "processSteps": [
                {"title": "Share the question", "description": "Send the main issue, timing, and any relevant context."},
                {"title": "Confirm fit", "description": "The next step is matched to the service area and available contact path."},
                {"title": "Start the consultation path", "description": "Move into a conversation with clearer expectations."},
            ],
            "offer": "Request a consultation path based on your situation and timing.",
            "guarantee": "A clear first conversation path.",
            "pageCopy": page_copy,
        }

    if vertical in {"clinical-wellness", "beauty-wellness"}:
        page_copy = _common_page_copy(name, business_type, service_area) | {
            "panelLabel": "Appointment path",
            "panelHeading": "A calm path from question to appointment.",
            "servicesHeading": f"Thoughtful {business_type} services in {service_area}.",
            "servicesIntro": "Visitors can understand the service options, appointment path, and details worth sharing before they book.",
            "standardEyebrow": "Care standard",
            "standardHeading": "Make the first step feel simple and reassuring.",
            "standardBody": "Health, wellness, and beauty sites need calm structure, accessible copy, and practical booking information without overstating outcomes.",
            "standardLink": "Start an appointment request →",
            "standardCards": [
                {"title": "Clear fit", "description": "Visitors can identify the service that matches their goal or concern."},
                {"title": "Comfortable booking", "description": "The CTA makes the next action feel obvious and low-pressure."},
                {"title": "Useful preparation", "description": "The page explains what details help before the appointment."},
            ],
        }
        return base | {
            "primaryCta": "Request an appointment",
            "secondaryCta": "View services",
            "heroSubheadline": "A calm, appointment-focused page that explains services, preparation, and how to get started.",
            "services": [
                {"title": "Service consultation", "description": "Share the goal, concern, or preferred service so the right path can be suggested."},
                {"title": "Appointment booking", "description": "A direct route for clients ready to ask about timing and availability."},
                {"title": "Preparation guidance", "description": "The page explains what details are useful before a visit."},
                {"title": "Follow-up questions", "description": "A clear place to ask practical questions before booking."},
            ],
            "proofPoints": ["Appointment-focused CTA", "Calm service explanation", "Clear expectations before booking", f"Client context for {service_area}"],
            "offer": "Request an appointment path with the details needed to get started.",
            "guarantee": "A clear booking inquiry before the visit.",
            "pageCopy": page_copy,
        }

    return base


def _public_image_url(value: Any) -> str:
    text = _string(value)
    if not text or not re.match(r"^https?://", text, flags=re.IGNORECASE):
        return ""
    if any(marker in text.lower() for marker in ("data:image", "base64,", "schema.org")):
        return ""
    return text


def _photo_list(raw: Mapping[str, Any], business_name: str) -> list[dict[str, str]]:
    """Return a small, safe list of public business photos."""

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
    """Normalize loose lead data into the schema consumed by the template."""

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
    page_copy = dict(defaults["pageCopy"])
    page_copy.update(raw.get("pageCopy") if isinstance(raw.get("pageCopy"), Mapping) else {})

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
        "primaryCta": _string(raw.get("primary_cta") or raw.get("primaryCta"), defaults["primaryCta"]),
        "secondaryCta": _string(raw.get("secondary_cta") or raw.get("secondaryCta"), defaults["secondaryCta"]),
        "hero": {
            "eyebrow": _string(raw.get("eyebrow"), defaults["heroEyebrow"]),
            "headline": _string(raw.get("headline"), defaults["heroHeadline"]),
            "subheadline": _string(raw.get("subheadline"), defaults["heroSubheadline"]),
        },
        "heroImage": photos[0] if photos else None,
        "photos": photos,
        "pageCopy": page_copy,
        "proofPoints": _list(raw.get("proof_points") or raw.get("proofPoints")) or defaults["proofPoints"],
        "services": _list(raw.get("services")) or defaults["services"],
        "processSteps": _list(raw.get("process_steps") or raw.get("processSteps")) or defaults["processSteps"],
        "reviews": _list(raw.get("reviews") or raw.get("testimonials")),
        "faqs": _list(raw.get("faqs") or raw.get("faq")) or defaults["faqs"],
        "offer": _string(raw.get("offer"), defaults["offer"]),
        "guarantee": _string(raw.get("guarantee"), defaults["guarantee"]),
        "brandTone": _string(raw.get("brand_tone") or raw.get("brandTone"), "premium, direct, calm, trustworthy"),
    }


def render_site_from_template(
    raw_business: Mapping[str, Any],
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    overwrite: bool = True,
) -> GeneratedSite:
    """Copy the canonical template and write compact plan files."""

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
    (data_dir / "business.json").write_text(json.dumps(business, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_site_plan(target, site_plan)

    return GeneratedSite(slug=slug, path=target, business_name=business["name"], design_system=site_plan.design["id"])


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
    """Optionally run Codex inside a generated site folder."""

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
        run_codex_refinement(generated.path, build_codex_instruction(business))

    if refine_with_claude:
        run_claude_refinement(site_plan, generated.path)

    return _quality_checked_result(generated, minimum_quality_score=minimum_quality_score, strict_quality=strict_quality)


def build_claude_instruction_preview(raw_business: Mapping[str, Any], target_path: Path | str = "generated_sites/<slug>") -> str:
    """Return the compact Claude Code orchestration prompt without running it."""

    business = normalize_business_profile(raw_business)
    return build_claude_agent_prompt(build_site_plan(business), Path(target_path))
