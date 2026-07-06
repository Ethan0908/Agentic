from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

try:
    from .env_loader import load_local_env
    from .scaffold_writer import assert_replaced, reset_dir, write_minimal_project
except ImportError:
    from env_loader import load_local_env
    from scaffold_writer import assert_replaced, reset_dir, write_minimal_project

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_FILE = REPO_ROOT / "backend" / "app" / "prompts" / "website_generation_prompt.md"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "generated_sites"


@dataclass(frozen=True)
class GeneratedSite:
    slug: str
    path: Path
    business_name: str
    design_system: str = "agent-built"
    refined_with_codex: bool = False
    refined_with_claude: bool = False


class SiteGenerationError(RuntimeError):
    pass


def slugify(value: str, fallback: str = "generated-site") -> str:
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
    if not text or not re.match(r"^https?://", text, flags=re.IGNORECASE):
        return ""
    lowered = text.lower()
    if "data:image" in lowered or "base64," in lowered or "schema.org" in lowered:
        return ""
    return text


def _photo_list(raw: Mapping[str, Any], business_name: str) -> list[dict[str, str]]:
    sources: list[Any] = []
    for key in (
        "photos", "images", "photo_urls", "photoUrls", "image_urls", "imageUrls",
        "gallery", "business_photos", "businessPhotos", "website_images", "websiteImages",
        "scraped_images", "scrapedImages",
    ):
        sources.extend(_list(raw.get(key)))
    sources = _list(raw.get("hero_image") or raw.get("heroImage") or raw.get("cover_image") or raw.get("coverImage")) + sources

    photos: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in sources:
        if isinstance(item, Mapping):
            url = _public_image_url(item.get("url") or item.get("src") or item.get("secure_url") or item.get("image"))
            alt = _string(item.get("alt") or item.get("caption") or item.get("title"), f"{business_name} photo")
            caption = _string(item.get("caption") or item.get("title"))
        else:
            url = _public_image_url(item)
            alt = f"{business_name} photo"
            caption = ""
        if not url or url in seen:
            continue
        seen.add(url)
        photo = {"url": url, "alt": alt}
        if caption:
            photo["caption"] = caption
        photos.append(photo)
        if len(photos) >= 12:
            break
    return photos


def normalize_business_profile(raw: Mapping[str, Any]) -> dict[str, Any]:
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


def prepare_site_scaffold(raw_business: Mapping[str, Any], output_dir: Path | str = DEFAULT_OUTPUT_DIR, overwrite: bool = True) -> GeneratedSite:
    business = normalize_business_profile(raw_business)
    slug = slugify(business["slug"])
    target = Path(output_dir) / slug
    try:
        reset_dir(target, overwrite=overwrite)
    except FileExistsError as exc:
        raise SiteGenerationError(str(exc)) from exc
    write_minimal_project(target, business)
    return GeneratedSite(slug=slug, path=target, business_name=business["name"])


render_site_from_template = prepare_site_scaffold


def build_codex_instruction(raw_business: Mapping[str, Any]) -> str:
    if not PROMPT_FILE.exists():
        raise SiteGenerationError(f"Missing prompt file: {PROMPT_FILE}")
    business = normalize_business_profile(raw_business)
    prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()
    return (
        f"{prompt}\n\n"
        "## Factual business data JSON\n"
        "```json\n"
        f"{json.dumps(business, ensure_ascii=False, indent=2)}\n"
        "```\n\n"
        "You are inside a blank generated Next.js project folder. Build the real website from the business data. "
        "Remove every occurrence of AGENTIC_REPLACE_ME from the project. "
        "You may create components, rewrite app/page.tsx, rewrite CSS, and choose the full UI/UX. "
        "Use supplied business photos when present; never add unrelated stock photos or unverifiable claims. "
        "Finish with a buildable site.\n"
    )


def _codex_command(default_command: str = "codex") -> list[str]:
    env_command = os.environ.get("CODEX_COMMAND", "").strip()
    if env_command:
        return env_command.split()
    codex_path = shutil.which(default_command)
    if codex_path:
        return [codex_path]
    npx_path = shutil.which("npx")
    if npx_path:
        return [npx_path, "-y", "@openai/codex"]
    raise SiteGenerationError("Codex CLI was not found. Rebuild the frontend container or set CODEX_COMMAND.")


def _codex_exec_args() -> list[str]:
    sandbox = os.environ.get("CODEX_SANDBOX", "danger-full-access").strip()
    # Docker already isolates this process. danger-full-access avoids bubblewrap/user-namespace failures inside Raspberry Pi containers.
    return ["exec", "--sandbox", sandbox]


def run_codex_refinement(site_path: Path, instruction: str, codex_command: str = "codex", timeout_seconds: int = 1800) -> None:
    if not site_path.exists():
        raise SiteGenerationError(f"Cannot run in missing site path: {site_path}")
    command = [*_codex_command(codex_command), *_codex_exec_args(), instruction]
    subprocess.run(command, cwd=site_path, check=True, text=True, env=load_local_env(), timeout=timeout_seconds)


def generate_site(raw_business: Mapping[str, Any], output_dir: Path | str = DEFAULT_OUTPUT_DIR, refine_with_codex: bool = True, refine_with_claude: bool = False) -> GeneratedSite:
    generated = prepare_site_scaffold(raw_business, output_dir=output_dir)
    used_codex = False
    used_claude = False
    if refine_with_codex:
        run_codex_refinement(generated.path, build_codex_instruction(raw_business))
        try:
            assert_replaced(generated.path)
        except RuntimeError as exc:
            raise SiteGenerationError(str(exc)) from exc
        used_codex = True
    if refine_with_claude:
        from .agentic_site_builder import build_site_plan, run_claude_refinement
        business = normalize_business_profile(raw_business)
        run_claude_refinement(build_site_plan(business), generated.path)
        used_claude = True
    return GeneratedSite(slug=generated.slug, path=generated.path, business_name=generated.business_name, refined_with_codex=used_codex, refined_with_claude=used_claude)
