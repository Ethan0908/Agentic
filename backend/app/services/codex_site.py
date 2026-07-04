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
        "short_description": data.get("short_description"),
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


async def improve_site_with_codex(
    site_dir: Path,
    business: Business,
    business_json: dict,
    fallback_repo_name: str | None = None,
) -> dict:
    """Use the logged-in Codex CLI to generate one business-specific website.

    Codex edits only the generated website folder and writes codex-output.json.
    The backend reads that metadata before creating the GitHub repo/Vercel project.
    """
    settings = get_settings()
    fallback_repo_name = normalise_repo_name(fallback_repo_name or business.name)

    if not settings.codex_enabled:
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

    prompt = f"""
You are editing a generated Next.js business website in the current directory.

Business context:
{_business_context(business, business_json)}

Task:
- Decide what kind of website this business needs from the business name, Google Places category/types, the original Places search keyword, city, address, phone, email, and any supplied public data.
- The original Places search keyword is strong classification evidence. For example, if the search keyword is "sushi restaurant", build a sushi restaurant website unless the individual business data clearly contradicts it.
- Build the site for that exact business type. Examples:
  - Sushi restaurant: menu highlights, dine-in/takeout, reservations, catering/party trays, location, hours placeholder, phone CTA.
  - Dentist: appointments, dental services, emergency/cleaning/cosmetic sections, insurance/location CTAs.
  - Plumbing company: emergency plumbing, drain cleaning, water heater, service area, phone CTA.
  - Salon: services, booking, stylists, location, phone/email CTA.
- Never make a generic plumbing, dental, or contractor website unless the business context actually supports that category.
- Do not rely on the original business website URL to generate content. Treat it only as an optional outbound reference link if present.
- Rewrite business.json so headline, subheadline, services, cta, and category match the inferred business type.
- Keep every claim truthful. Use generic placeholders such as "Call for current hours" instead of inventing exact hours, awards, menu prices, staff names, or reviews.
- Keep the site self-contained, polished, mobile-first, fast, and conversion-focused.
- Keep calls, address/directions, email, phone, and original website link visible when available.
- Do not add new npm packages.
- Do not use external images that require scraping/downloading.
- Do not send emails, create GitHub repos, deploy to Vercel, or modify files outside this folder.
- Choose a clean GitHub/Vercel-safe repository name for this generated site, based on the business name and type/city.
- Write exactly one JSON metadata file named {CODEX_OUTPUT_FILE} in the project root with this shape:
  {{
    "repo_name": "lowercase-dash-separated-repo-name",
    "site_title": "short public site title",
    "business_type": "inferred type such as sushi restaurant, dental clinic, salon, plumber",
    "short_description": "one sentence summary"
  }}
- The repo_name must use only lowercase letters, numbers, dashes, underscores, or dots. No spaces. No owner prefix. No slash.
- Finish by leaving the edited files and {CODEX_OUTPUT_FILE} on disk.
""".strip()

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

    metadata = read_codex_output(site_dir, fallback_repo_name)
    return {
        "codex_ran": True,
        **metadata,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }
