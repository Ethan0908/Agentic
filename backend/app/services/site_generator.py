"""Website generation service.

GitHub is the source of truth for this file. The Raspberry Pi should run a direct
copy of the repository instead of keeping separate local-only generator logic.

This service keeps the baseline website quality high even before Codex touches the
site: it copies the canonical Next.js template, writes a normalized business data
file, then optionally hands the generated site to Codex for tasteful customisation.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_FILE = REPO_ROOT / "backend" / "app" / "prompts" / "website_generation_prompt.md"
TEMPLATE_DIR = REPO_ROOT / "site-template"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "generated_sites"


@dataclass(frozen=True)
class GeneratedSite:
    """Result returned after rendering a website folder."""

    slug: str
    path: Path
    business_name: str


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


def normalize_business_profile(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize loose lead data into the schema consumed by the template.

    The template intentionally uses a small, stable schema so generated sites do
    not break when the lead data is incomplete. Never invent hard proof such as
    licences, awards, review counts, warranties, or years in business.
    """

    name = _string(raw.get("name") or raw.get("business_name"), "Local Service Company")
    business_type = _string(raw.get("business_type") or raw.get("category"), "local service")
    city = _string(raw.get("city") or raw.get("location"), "your area")
    service_area = _string(raw.get("service_area"), city)
    phone = _string(raw.get("phone") or raw.get("phone_number"))
    email = _string(raw.get("email"))
    website = _string(raw.get("website") or raw.get("url"))

    primary_cta = _string(raw.get("primary_cta"), "Request a quote")
    secondary_cta = _string(raw.get("secondary_cta"), "See services")

    services = _list(raw.get("services")) or [
        {"title": "Assessment", "description": "Understand the issue, scope, and next step before work begins."},
        {"title": "Repair and service", "description": "Practical work completed with clear communication and tidy follow-through."},
        {"title": "Installation", "description": "Planned installation with attention to fit, finish, and long-term reliability."},
        {"title": "Maintenance", "description": "Preventive service that helps reduce surprise problems later."},
    ]

    proof_points = _list(raw.get("proof_points")) or [
        "Clear scope before work starts",
        "Practical scheduling and communication",
        f"Service across {service_area}",
    ]

    process_steps = _list(raw.get("process_steps")) or [
        {"title": "Tell us what you need", "description": "Share the issue, location, and timing so the request can be scoped properly."},
        {"title": "Get a clear next step", "description": "Receive a practical recommendation, quote path, or booking option."},
        {"title": "Complete the work", "description": "The job is handled with clear communication from start to finish."},
    ]

    faqs = _list(raw.get("faqs") or raw.get("faq")) or [
        {
            "question": f"Do you serve {service_area}?",
            "answer": f"Yes. {name} works with customers across {service_area}. Contact the team with your address or project details to confirm availability.",
        },
        {
            "question": "How do I get pricing?",
            "answer": "Send a few details about the work needed. The team can explain the next step and whether a quote, assessment, or booking makes the most sense.",
        },
        {
            "question": "What should I prepare before contacting you?",
            "answer": "A short description, photos if available, the property location, and your preferred timing are usually enough to start.",
        },
    ]

    reviews = _list(raw.get("reviews") or raw.get("testimonials"))

    return {
        "name": name,
        "slug": slugify(_string(raw.get("slug"), name)),
        "businessType": business_type,
        "city": city,
        "serviceArea": service_area,
        "phone": phone,
        "email": email,
        "website": website,
        "primaryCta": primary_cta,
        "secondaryCta": secondary_cta,
        "hero": {
            "eyebrow": _string(raw.get("eyebrow"), f"{business_type.title()} in {service_area}"),
            "headline": _string(
                raw.get("headline"),
                f"{name} helps {service_area} customers get {business_type} work done clearly and reliably.",
            ),
            "subheadline": _string(
                raw.get("subheadline"),
                "Get a clear next step, practical communication, and a cleaner service experience from first contact to finish.",
            ),
        },
        "proofPoints": proof_points,
        "services": services,
        "processSteps": process_steps,
        "reviews": reviews,
        "faqs": faqs,
        "offer": _string(raw.get("offer"), "Request a practical quote path based on your project details."),
        "guarantee": _string(raw.get("guarantee"), "Clear communication before work begins."),
        "brandTone": _string(raw.get("brand_tone"), "premium, direct, calm, trustworthy"),
    }


def render_site_from_template(
    raw_business: Mapping[str, Any],
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    overwrite: bool = True,
) -> GeneratedSite:
    """Copy the canonical template and write `site-template/data/business.json`."""

    if not TEMPLATE_DIR.exists():
        raise SiteGenerationError(f"Missing canonical template folder: {TEMPLATE_DIR}")

    business = normalize_business_profile(raw_business)
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

    return GeneratedSite(slug=slug, path=target, business_name=business["name"])


def build_codex_instruction(raw_business: Mapping[str, Any]) -> str:
    """Build the exact instruction sent to Codex for optional refinement."""

    if not PROMPT_FILE.exists():
        raise SiteGenerationError(f"Missing prompt file: {PROMPT_FILE}")

    business = normalize_business_profile(raw_business)
    prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()
    return (
        f"{prompt}\n\n"
        "## Business profile JSON\n"
        "```json\n"
        f"{json.dumps(business, ensure_ascii=False, indent=2)}\n"
        "```\n\n"
        "Refine the generated site only where it improves quality, conversion, copy, responsiveness, performance, or maintainability. "
        "Do not add unverifiable claims. Do not change deployment assumptions. Ensure the project builds.\n"
    )


def run_codex_refinement(site_path: Path, instruction: str, codex_command: str = "codex") -> None:
    """Optionally run Codex inside a generated site folder.

    Keep this as a separate explicit step so the system still works without Codex.
    """

    if not site_path.exists():
        raise SiteGenerationError(f"Cannot refine missing site path: {site_path}")

    subprocess.run(
        [codex_command, "exec", instruction],
        cwd=site_path,
        check=True,
        text=True,
    )


def generate_site(
    raw_business: Mapping[str, Any],
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    refine_with_codex: bool = False,
) -> GeneratedSite:
    """Render a premium baseline website and optionally refine it with Codex."""

    generated = render_site_from_template(raw_business, output_dir=output_dir)

    if refine_with_codex:
        instruction = build_codex_instruction(raw_business)
        run_codex_refinement(generated.path, instruction)

    return generated
