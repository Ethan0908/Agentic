from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from app.core.config import get_settings
from app.models import Business


CODEX_OUTPUT_FILE = "codex-output.json"
ALLOWED_REASONING_EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}
ALLOWED_VERBOSITY = {"low", "medium", "high"}
STALE_RESTAURANT_TERMS = {"omakase", "nigiri", "sashimi", "maki", "izakaya", "ramen", "sushi"}


def _codex_command() -> str | None:
    return shutil.which("codex")


def normalise_repo_name(value: str | None, fallback: str = "generated-business-site") -> str:
    raw = (value or fallback).strip().lower()
    raw = raw.split("/", 1)[1] if "/" in raw else raw
    raw = re.sub(r"[^a-z0-9._-]+", "-", raw)
    raw = re.sub(r"[-_.]{2,}", "-", raw).strip("-._")
    return (raw or fallback)[:90]


def _business_context(business: Business, business_json: dict) -> str:
    return json.dumps(
        {
            "business": {
                "name": business.name,
                "city": business.city,
                "category": business.category,
                "phone": business.phone,
                "website_url": business.website_url,
                "address": business.address,
                "raw_data": business.raw_data,
            },
            "business_json": business_json,
        },
        indent=2,
    )


def read_codex_output(site_dir: Path, fallback_repo_name: str) -> dict:
    path = site_dir / CODEX_OUTPUT_FILE
    if not path.exists():
        return {"repo_name": normalise_repo_name(fallback_repo_name), "metadata_found": False}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"repo_name": normalise_repo_name(fallback_repo_name), "metadata_found": False, "metadata_error": "invalid_json"}

    return {
        "repo_name": normalise_repo_name(data.get("repo_name"), fallback=fallback_repo_name),
        "metadata_found": True,
        "site_title": data.get("site_title"),
        "business_type": data.get("business_type"),
        "design_style": data.get("design_style"),
        "primary_cta": data.get("primary_cta"),
        "short_description": data.get("short_description"),
        "research_summary": data.get("research_summary"),
    }


def _add_codex_config_overrides(command: list[str]) -> None:
    settings = get_settings()
    reasoning_effort = (settings.codex_reasoning_effort or "").strip().lower()
    verbosity = (settings.codex_verbosity or "").strip().lower()

    if reasoning_effort:
        if reasoning_effort not in ALLOWED_REASONING_EFFORTS:
            raise RuntimeError(f"Invalid CODEX_REASONING_EFFORT={reasoning_effort}. Use minimal, low, medium, high, or xhigh.")
        command.extend(["-c", f"model_reasoning_effort=\"{reasoning_effort}\""])

    if verbosity:
        if verbosity not in ALLOWED_VERBOSITY:
            raise RuntimeError(f"Invalid CODEX_VERBOSITY={verbosity}. Use low, medium, or high.")
        command.extend(["-c", f"model_verbosity=\"{verbosity}\""])


def _write_authoritative_business_json(site_dir: Path, business_json: dict) -> None:
    (site_dir / "business.json").write_text(json.dumps(business_json, indent=2), encoding="utf-8")


def _combined_site_text(site_dir: Path) -> str:
    chunks: list[str] = []
    allowed_suffixes = {".tsx", ".ts", ".jsx", ".js", ".json", ".css", ".html", ".md"}
    skipped_dirs = {"node_modules", ".next", ".git", ".vercel"}

    for path in site_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skipped_dirs for part in path.parts):
            continue
        if path.suffix.lower() not in allowed_suffixes:
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue

    return "\n".join(chunks).lower()


def _validate_no_stale_restaurant_copy(site_dir: Path, business_json: dict) -> None:
    context = " ".join(
        str(business_json.get(key) or "")
        for key in ["businessType", "category", "searchKeyword"]
    ).lower()

    sushi_allowed = any(term in context for term in ["sushi", "ramen", "izakaya", "japanese"])
    if sushi_allowed:
        return

    text = _combined_site_text(site_dir)
    found = sorted(term for term in STALE_RESTAURANT_TERMS if term in text)
    if found:
        raise RuntimeError(
            "Generated site still contains stale sushi/omakase wording for a non-sushi business. "
            f"Found: {', '.join(found)}. Stopped before GitHub/Vercel publish."
        )


def _optional_file(site_dir: Path, name: str) -> str:
    path = site_dir / name
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _codex_metadata_shape() -> str:
    return json.dumps(
        {
            "repo_name": "lowercase-dash-separated-repo-name",
            "site_title": "short public site title",
            "business_type": "specific inferred type",
            "design_style": "specific design style",
            "primary_cta": "main conversion action",
            "short_description": "one sentence summary",
            "research_summary": "one sentence describing what research/design logic was used",
        },
        indent=2,
    )


def _build_prompt(site_dir: Path, business: Business, business_json: dict) -> str:
    custom_instructions = _optional_file(site_dir, "codex-instructions.md").strip()
    metadata_shape = _codex_metadata_shape()

    return f"""
You are a senior conversion-focused web designer, UX researcher, brand strategist, and Next.js frontend engineer.

You are creating a custom website from scratch for exactly one real local business. Do not reuse a previous generated website. Do not reuse a sushi, omakase, restaurant, contractor, dentist, SaaS, or generic landing-page concept unless the business data actually supports that category.

Business context:
{_business_context(business, business_json)}

Additional local instructions, if present:
{custom_instructions or "No extra instruction file was provided."}

Research and thinking phase:
1. Read business.json first. Treat it as the source of truth for business name, category, business type, search keyword, city, address, phone number, email, original website, and Google Places types.
2. Classify the business precisely. Use business name, category, search keyword, Places types, address, and original website URL. The original search keyword is strong evidence.
3. Decide the visitor's real intent. Emergency plumbers need fast phone CTA. Dentists need trust and appointment flow. Restaurants need menu/order/location. Salons need service/booking/visual tone. Fitness businesses need program/schedule inquiry. Professional services need credibility and contact flow.
4. If originalWebsite exists and the environment allows internet access, use it only to understand real services, tone, location, CTAs, and factual details. Do not copy text verbatim. Do not copy images.
5. Research or infer sector-specific UX patterns: above-the-fold needs, expected sections, CTA hierarchy, trust signals, contact flow, mobile behavior, visual tone, and accessibility needs.
6. Write research-notes.md with inferred business type, target customer, primary conversion goal, secondary conversion goal, recommended sections, visual direction, facts used, and facts not available.

Design strategy:
- Create a site that feels custom to this business, not template-generated.
- Define the user journey, primary CTA, trust-building moments, visual system, and page architecture before coding.
- Use a sector-specific layout and visual language.
- Make mobile UX excellent: readable type, large tap targets, no cramped cards, clear phone/contact actions.
- Use accessible contrast, semantic HTML, descriptive headings, keyboard-friendly links/buttons, and clean spacing.
- Avoid generic AI/SaaS styling unless the company is actually tech.

Industry rules:
- Blue-collar/service companies: strong rectangular sections, low-radius corners, bold typography, strong phone CTA, practical service cards, service-area language, emergency/contact urgency if appropriate. Avoid bubbly SaaS styling, pastel startup cards, excessive rounded pills, fake luxury gradients, and restaurant imagery.
- Restaurants: prioritize menu/order/location/reservation flow. Use food-appropriate warmth, but do not invent menu prices or specific dishes unless supplied. If it is not a Japanese/sushi business, do not use omakase, nigiri, sashimi, maki, ramen, izakaya, or sushi language.
- Dental/medical/clinic: prioritize appointment CTA, trust, services, insurance/location, calm design, clean spacing. Avoid aggressive sales tone.
- Salons/spas/beauty: prioritize booking, services, visual polish, pricing inquiry, stylist/service categories.
- Fitness: prioritize classes/training, schedule inquiry, membership CTA, energy, location.
- Professional/local services: prioritize credibility, clear services, contact, location, outcome-oriented copy.

Copy rules:
- Use the actual business name throughout.
- Use actual phone, email, address, city, and original website link when available.
- Keep claims truthful.
- Use placeholders only when necessary, such as Call for current hours.
- Do not write fake testimonials, fake reviews, fake awards, fake staff names, fake prices, or fake certifications.
- Do not use the same generic headline for every company.

Technical requirements:
- Build a complete deployable Next.js app in the current folder.
- Required files: package.json, app/layout.tsx, app/page.tsx, app/globals.css, research-notes.md, codex-output.json.
- Add next.config.js or next.config.mjs and tsconfig.json if needed.
- Do not add external npm packages.
- Do not use external images. Use CSS, layout, typography, gradients, SVG shapes, and structured sections instead.
- Do not send emails, create GitHub repos, deploy to Vercel, or modify files outside this folder.

Page structure guidance:
1. Hero: specific headline, specific subheadline, primary CTA, phone/contact CTA, location cue.
2. Trust/value section: why this business is relevant to the visitor.
3. Services/offers: sector-specific service cards.
4. Process or why choose us: explain the next step.
5. Location/contact section: phone, email, address, original website.
6. Footer: business name, city, contact links.
You may change this structure if your research shows a better flow for the sector.

Anti-repetition rules:
Before finishing, scan all generated text. Reject and rewrite the site if the business name is missing, the category does not match the website, stale copy from another business appears, a non-sushi business contains sushi/omakase/ramen/nigiri/sashimi/izakaya/maki language, a service business looks like a restaurant/spa/SaaS startup, service cards are generic, or the CTA is unclear.

Write exactly one JSON metadata file named {CODEX_OUTPUT_FILE} in the project root with this exact shape:
{metadata_shape}

repo_name must use only lowercase letters, numbers, dashes, underscores, or dots. No spaces. No owner prefix. No slash.

Final check:
- Confirm required files exist.
- Confirm page imports no missing packages.
- Confirm there is no unrelated stale business copy.
- Confirm the UI is sector-specific.
- Confirm mobile layout is usable.
- Confirm codex-output.json is valid JSON.
""".strip()


async def improve_site_with_codex(
    site_dir: Path,
    business: Business,
    business_json: dict,
    fallback_repo_name: str | None = None,
) -> dict:
    """Use the logged-in Codex CLI to generate one business-specific website."""
    settings = get_settings()
    fallback_repo_name = normalise_repo_name(fallback_repo_name or business.name)

    _write_authoritative_business_json(site_dir, business_json)

    if not settings.codex_enabled:
        _validate_no_stale_restaurant_copy(site_dir, business_json)
        metadata = read_codex_output(site_dir, fallback_repo_name)
        return {"codex_ran": False, "reason": "CODEX_ENABLED=false", **metadata}

    codex = _codex_command()
    if not codex:
        raise RuntimeError("Codex CLI is not installed in the backend container")

    auth_path = Path("/root/.codex/auth.json")
    if not auth_path.exists():
        raise RuntimeError("Codex auth not found at /root/.codex/auth.json. Mount the Pi user's ~/.codex into the backend container.")

    if not site_dir.exists() or not site_dir.is_dir():
        raise FileNotFoundError(f"Generated site folder not found: {site_dir}")

    prompt = _build_prompt(site_dir, business, business_json)

    command = [
        codex,
        "exec",
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
    ]
    if settings.codex_default_model:
        command.extend(["--model", settings.codex_default_model])
    _add_codex_config_overrides(command)
    command.append(prompt)

    result = subprocess.run(
        command,
        cwd=site_dir,
        text=True,
        capture_output=True,
        timeout=settings.codex_timeout_seconds,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Codex failed while improving the site. "
            f"exit={result.returncode}\nSTDOUT:\n{result.stdout[-4000:]}\nSTDERR:\n{result.stderr[-4000:]}"
        )

    _write_authoritative_business_json(site_dir, business_json)
    _validate_no_stale_restaurant_copy(site_dir, business_json)

    metadata = read_codex_output(site_dir, fallback_repo_name)
    return {
        "codex_ran": True,
        **metadata,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }
