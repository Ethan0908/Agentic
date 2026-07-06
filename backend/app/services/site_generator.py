"""Prompt-driven website generation service.

GitHub owns the scaffold, prompts, and orchestration code. The Raspberry Pi runs
this repo and Codex performs the actual website build for each business.

Important design rule: Python should not lock a business into a hardcoded
vertical template. Python only normalizes factual business data, prepares a clean
Next.js scaffold, and gives Codex a strict build brief. Codex is responsible for
the unique design, layout, copy, component structure, and UI/UX improvements.
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
except ImportError:  # pragma: no cover - lets this file run as a direct script during local debugging.
    from agentic_site_builder import build_claude_agent_prompt, build_site_plan, run_claude_refinement, write_site_plan
    from env_loader import load_local_env


REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_FILE = REPO_ROOT / "backend" / "app" / "prompts" / "website_generation_prompt.md"
SCAFFOLD_DIR = REPO_ROOT / "site-template"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "generated_sites"


@dataclass(frozen=True)
class GeneratedSite:
    """Result returned after preparing and optionally building a generated site."""

    slug: str
    path: Path
    business_name: str
    design_system: str = "codex-owned"
    refined_with_codex: bool = False
    refined_with_claude: bool = False


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


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


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

    The backend only normalizes photos. It does not decide the final image layout;
    Codex decides how to use supplied images in the generated site.
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
        if len(photos) >= 12:
            break

    return photos


def normalize_business_profile(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize lead data without turning it into a fixed site template.

    Keep this factual. Do not generate vertical-specific sections, canned service
    cards, fake proof, fake reviews, fake awards, or fixed page structure here.
    Codex receives this JSON and creates the actual custom website.
    """

    name = _string(raw.get("name") or raw.get("business_name"), "Local Business")
    business_type = _string(raw.get("business_type") or raw.get("businessType") or raw.get("category"), "local business")
    city = _string(raw.get("city") or raw.get("location"))
    service_area = _string(raw.get("service_area") or raw.get("serviceArea"), city)
    photos = _photo_list(raw, name)

    return {
        "name": name,
        "slug": slugify(_string(raw.get("slug"), name)),
        "businessType": business_type,
        "city": city,
        "serviceArea": service_area,
        "phone": _string(raw.get("phone") or raw.get("phone_number")),
        "email": _string(raw.get("email")),
        "website": _string(raw.get("website") or raw.get("url")),
        "address": _string(raw.get("address")),
        "primaryCta": _string(raw.get("primary_cta") or raw.get("primaryCta")),
        "secondaryCta": _string(raw.get("secondary_cta") or raw.get("secondaryCta")),
        "headline": _string(raw.get("headline")),
        "subheadline": _string(raw.get("subheadline")),
        "description": _string(raw.get("description") or raw.get("notes")),
        "services": _list(raw.get("services")),
        "proofPoints": _list(raw.get("proof_points") or raw.get("proofPoints")),
        "processSteps": _list(raw.get("process_steps") or raw.get("processSteps")),
        "reviews": _list(raw.get("reviews") or raw.get("testimonials")),
        "faqs": _list(raw.get("faqs") or raw.get("faq")),
        "offer": _string(raw.get("offer")),
        "guarantee": _string(raw.get("guarantee")),
        "brandTone": _string(raw.get("brand_tone") or raw.get("brandTone")),
        "heroImage": photos[0] if photos else None,
        "photos": photos,
        "rawLead": dict(raw),
    }


def prepare_site_scaffold(
    raw_business: Mapping[str, Any],
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    overwrite: bool = True,
) -> GeneratedSite:
    """Copy the neutral Next.js scaffold and write factual generation data.

    The copied scaffold is not the finished website. It exists so Codex has a
    buildable Next.js project to rewrite into a unique site.
    """

    if not SCAFFOLD_DIR.exists():
        raise SiteGenerationError(f"Missing site scaffold folder: {SCAFFOLD_DIR}")

    business = normalize_business_profile(raw_business)
    slug = slugify(business["slug"])
    target = Path(output_dir) / slug

    if target.exists():
        if not overwrite:
            raise SiteGenerationError(f"Target site already exists: {target}")
        shutil.rmtree(target)

    shutil.copytree(SCAFFOLD_DIR, target)

    # Existing scaffold files read these JSON files, but Codex is free to replace
    # the React/CSS structure and use them only as factual source data.
    site_plan = build_site_plan(business)
    data_dir = target / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "business.json").write_text(json.dumps(business, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_site_plan(target, site_plan)
    (data_dir / "generation-mode.json").write_text(
        json.dumps(
            {
                "mode": "prompt-driven-codex-build",
                "scaffoldIsFinal": False,
                "rules": [
                    "Do not preserve the scaffold layout unless it is truly the best option.",
                    "Codex owns the final design, copy, components, and responsive UX.",
                    "Business data is factual source material, not a fixed template.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return GeneratedSite(slug=slug, path=target, business_name=business["name"])


# Backward-compatible name used by older code paths.
render_site_from_template = prepare_site_scaffold


def build_codex_instruction(raw_business: Mapping[str, Any]) -> str:
    """Build the instruction sent to Codex for the real website build."""

    if not PROMPT_FILE.exists():
        raise SiteGenerationError(f"Missing prompt file: {PROMPT_FILE}")

    business = normalize_business_profile(raw_business)
    site_plan = build_site_plan(business)
    prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()
    return (
        f"{prompt}\n\n"
        "## Factual business data JSON\n"
        "```json\n"
        f"{json.dumps(business, ensure_ascii=False, indent=2)}\n"
        "```\n\n"
        "## Optional seed plan JSON\n"
        "This seed plan is only a starting hint. Do not treat it as a required template.\n"
        "```json\n"
        f"{json.dumps(site_plan.as_dict(), ensure_ascii=False, separators=(',', ':'))}\n"
        "```\n\n"
        "You are inside the generated Next.js project folder. Rebuild the site as a unique, production-quality website for this business. "
        "You may rewrite app/page.tsx, CSS, components, data usage, layout, typography, and UX. "
        "Do not keep generic scaffold sections just because they already exist. "
        "Use supplied business photos when present; never add unrelated stock photos or unverifiable claims. "
        "Finish with a buildable site.\n"
    )


def run_codex_refinement(site_path: Path, instruction: str, codex_command: str = "codex", timeout_seconds: int = 1800) -> None:
    """Run Codex inside the generated site folder."""

    if not site_path.exists():
        raise SiteGenerationError(f"Cannot run Codex in missing site path: {site_path}")

    subprocess.run(
        [codex_command, "exec", instruction],
        cwd=site_path,
        check=True,
        text=True,
        env=load_local_env(),
        timeout=timeout_seconds,
    )


def generate_site(
    raw_business: Mapping[str, Any],
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    refine_with_codex: bool = True,
    refine_with_claude: bool = False,
) -> GeneratedSite:
    """Prepare a scaffold, then let Codex build the actual custom website.

    `refine_with_codex` defaults to True because this system is intentionally
    prompt-driven. Setting it to False is only for debugging the scaffold/data.
    """

    generated = prepare_site_scaffold(raw_business, output_dir=output_dir)
    business = normalize_business_profile(raw_business)
    site_plan = build_site_plan(business)
    used_codex = False
    used_claude = False

    if refine_with_codex:
        run_codex_refinement(generated.path, build_codex_instruction(business))
        used_codex = True

    if refine_with_claude:
        run_claude_refinement(site_plan, generated.path)
        used_claude = True

    return GeneratedSite(
        slug=generated.slug,
        path=generated.path,
        business_name=generated.business_name,
        refined_with_codex=used_codex,
        refined_with_claude=used_claude,
    )


def build_claude_instruction_preview(raw_business: Mapping[str, Any], target_path: Path | str = "generated_sites/<slug>") -> str:
    """Return the compact Claude Code orchestration prompt without running it."""

    business = normalize_business_profile(raw_business)
    return build_claude_agent_prompt(build_site_plan(business), Path(target_path))
