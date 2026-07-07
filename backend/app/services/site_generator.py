from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

try:
    from .agentic_site_builder import build_site_plan, write_site_plan
    from .env_loader import load_local_env
    from .premium_seed import write_premium_seed_site
    from .scaffold_writer import assert_replaced, reset_dir, write_minimal_project
except ImportError:
    from agentic_site_builder import build_site_plan, write_site_plan
    from env_loader import load_local_env
    from premium_seed import write_premium_seed_site
    from scaffold_writer import assert_replaced, reset_dir, write_minimal_project

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_FILE = REPO_ROOT / "backend" / "app" / "prompts" / "website_generation_prompt.md"
PLAYBOOK_FILE = REPO_ROOT / "backend" / "app" / "prompts" / "premium_website_playbook.md"
SKILLS_DIR = REPO_ROOT / "backend" / "app" / "skills"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "generated_sites"
DEFAULT_CODEX_REASONING_EFFORT = "high"
CODEX_STAGE_SEQUENCE = ("plan", "foundation", "hero", "content", "interactions", "visual-director", "polish")


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


def _default_primary_cta(raw: Mapping[str, Any]) -> str:
    provided = _string(raw.get("primary_cta") or raw.get("primaryCta"))
    if provided:
        return provided
    if _string(raw.get("phone") or raw.get("phone_number")):
        return "Call now"
    if _string(raw.get("website") or raw.get("url")):
        return "Visit website"
    if _string(raw.get("email")):
        return "Email the team"
    return "Request information"


def normalize_business_profile(raw: Mapping[str, Any]) -> dict[str, Any]:
    name = _string(raw.get("name") or raw.get("business_name"), "Local Business")
    business_type = _string(raw.get("business_type") or raw.get("businessType") or raw.get("category"), "local business")
    city = _string(raw.get("city") or raw.get("location"))
    service_area = _string(raw.get("service_area") or raw.get("serviceArea"), city)
    photos = _photo_list(raw, name)
    logo = _public_image_url(raw.get("logo") or raw.get("logo_url") or raw.get("logoUrl"))
    brand_colors = raw.get("brand_colors") or raw.get("brandColors") or raw.get("colors") or []
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
        "primaryCta": _default_primary_cta(raw),
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
        "logo": logo,
        "brandColors": _list(brand_colors),
        "allowStockAssets": bool(raw.get("allow_stock_assets") or raw.get("allowStockAssets")),
        "heroImage": photos[0] if photos else None,
        "photos": photos,
        "rawLead": dict(raw),
    }


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def install_codex_skills(target: Path) -> None:
    dest = target / ".codex" / "skills"
    dest.mkdir(parents=True, exist_ok=True)
    if SKILLS_DIR.exists():
        for skill_dir in sorted(item for item in SKILLS_DIR.iterdir() if item.is_dir()):
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                _write_text(dest / skill_dir.name / "SKILL.md", skill_file.read_text(encoding="utf-8"))
    _write_text(dest / "README.md", "# Codex Skills\n\nFollow these persistent design skills before editing generated-site UI code.\n")


def write_design_briefs(target: Path, business: Mapping[str, Any]) -> None:
    install_codex_skills(target)
    _write_text(target / "AGENTS.md", """# Generated Site Instructions

Read `.codex/skills/design-taste-frontend/SKILL.md`, `.codex/skills/gpt-taste/SKILL.md`, and `LUXURY_BASELINE.md` before editing UI code.

Build in stages: plan, foundation, header/hero, content sections, interactions, visual-director, polish.

Start from the premium baseline. Improve it. Do not replace it with a generic card stack. Use factual JSON from `data/`. Use real business photos/logo/brand colours when supplied. Do not invent claims. Keep the site static, dependency-light, responsive, and Vercel-friendly.
""")
    _write_text(target / "DESIGN_STUDIO_BRIEF.md", f"""# Design Studio Brief

Business: {business.get('name')}
Type: {business.get('businessType')}
Market: {business.get('city') or business.get('serviceArea')}
Photos supplied: {'yes' if business.get('photos') else 'no'}
Logo supplied: {'yes' if business.get('logo') else 'no'}
Stock assets allowed: {'yes' if business.get('allowStockAssets') else 'no'}

The goal is a custom local-business website that looks intentionally designed, not a generic scaffold. Start with a plan/spec, then build component by component.
""")


def prepare_site_scaffold(raw_business: Mapping[str, Any], output_dir: Path | str = DEFAULT_OUTPUT_DIR, overwrite: bool = True) -> GeneratedSite:
    business = normalize_business_profile(raw_business)
    site_plan = build_site_plan(business)
    slug = slugify(business["slug"])
    target = Path(output_dir) / slug
    try:
        reset_dir(target, overwrite=overwrite)
    except FileExistsError as exc:
        raise SiteGenerationError(str(exc)) from exc
    write_minimal_project(target, business)
    write_site_plan(target, site_plan)
    write_premium_seed_site(target, business, site_plan.as_dict())
    write_design_briefs(target, business)
    design_system = _string(site_plan.design.get("id"), "agent-built")
    return GeneratedSite(slug=slug, path=target, business_name=business["name"], design_system=design_system)


render_site_from_template = prepare_site_scaffold


def _optional_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def _skill_text(name: str) -> str:
    path = SKILLS_DIR / name / "SKILL.md"
    return _optional_file(path)


def _business_and_plan_context(raw_business: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str]:
    business = normalize_business_profile(raw_business)
    site_plan = build_site_plan(business).as_dict()
    context = (
        "## Factual business data JSON\n```json\n"
        f"{json.dumps(business, ensure_ascii=False, indent=2)}\n```\n\n"
        "## Generated design plan JSON\n```json\n"
        f"{json.dumps(site_plan, ensure_ascii=False, indent=2)}\n```\n"
    )
    return business, site_plan, context


def build_codex_plan_instruction(raw_business: Mapping[str, Any]) -> str:
    _, _, context = _business_and_plan_context(raw_business)
    return (
        "You are in Plan Mode for a generated Next.js business website. Do not edit app/page.tsx or app/globals.css yet.\n\n"
        "Read AGENTS.md, DESIGN_STUDIO_BRIEF.md, LUXURY_BASELINE.md, data/style-signature.json, .codex/skills/design-taste-frontend/SKILL.md, and .codex/skills/gpt-taste/SKILL.md.\n\n"
        f"{context}\n\n"
        "Create two planning files only:\n"
        "1. DESIGN_SPEC.md with a detailed implementation spec covering site structure, component order, interactions, CTA map, colour scheme, typography, asset/branding plan, responsive behaviour, and QA risks.\n"
        "2. data/implementation-plan.json with keys: designRead, dials, colourScheme, typography, assetPlan, sections, components, interactions, ctaMap, mobilePlan, stagePlan, qaChecklist.\n\n"
        "The plan must explicitly explain how the premium baseline will be elevated into a more expensive-looking site. If an interaction such as FAQ accordion, contact drawer, service toggle, or pricing toggle does not fit the data, do not force it.\n"
    )


def build_codex_stage_instruction(raw_business: Mapping[str, Any], stage: str) -> str:
    if not PROMPT_FILE.exists():
        raise SiteGenerationError(f"Missing prompt file: {PROMPT_FILE}")
    prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()
    playbook = _optional_file(PLAYBOOK_FILE)
    _, _, context = _business_and_plan_context(raw_business)
    stage_guidance = {
        "foundation": "Audit the premium baseline. Refine component architecture, data helpers, CTA helpers, CSS variables, type scale, spacing scale, and responsive rules without making the design generic.",
        "hero": "Upgrade the header/navigation and hero. The first viewport must feel expensive: wide typography, disciplined negative space, intentional visual object/photo treatment, and a real CTA path.",
        "content": "Upgrade the body sections with varied rhythms: proof rail, service matrix, process timeline, photo ribbon, location/contact panel, FAQ, and final CTA as appropriate. Avoid repeated equal cards.",
        "interactions": "Add only useful interactions: FAQ accordion, service/category toggle, contact drawer, sticky mobile CTA, hover states, or modal if the plan supports them. Keep it dependency-light and build-safe.",
        "visual-director": "Act as a senior visual director. Ruthlessly remove 5/10 choices: weak gradients, cramped spacing, samey cards, narrow hero text, fake labels, low-contrast buttons, cheap shadows, and generic copy. Make it look more expensive while preserving facts.",
        "polish": "Perform final build-safety cleanup. Remove scaffold residue, improve mobile layout, contrast, CTA links, and generic copy. Run npm run build if dependencies are installed.",
    }[stage]
    return (
        f"{prompt}\n\n"
        f"## Premium website playbook\n{playbook}\n\n"
        f"## Persistent frontend skills\n{_skill_text('design-taste-frontend')}\n\n{_skill_text('gpt-taste')}\n\n"
        f"{context}\n\n"
        f"## Current stage: {stage}\n{stage_guidance}\n\n"
        "You must read DESIGN_SPEC.md, LUXURY_BASELINE.md, data/style-signature.json, and data/implementation-plan.json before editing. "
        "Work only on this stage's responsibilities, while preserving and improving earlier completed work. "
        "Do not output explanations. Implement the files.\n"
    )


def build_codex_instruction(raw_business: Mapping[str, Any]) -> str:
    return build_codex_stage_instruction(raw_business, "polish")


def _codex_command(default_command: str = "codex") -> list[str]:
    env_command = os.environ.get("CODEX_COMMAND", "").strip()
    if env_command:
        return shlex.split(env_command)
    codex_path = shutil.which(default_command)
    if codex_path:
        return [codex_path]
    npx_path = shutil.which("npx")
    if npx_path:
        return [npx_path, "-y", "@openai/codex"]
    raise SiteGenerationError("Codex CLI was not found. Rebuild the frontend container or set CODEX_COMMAND.")


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _codex_config_args() -> list[str]:
    args: list[str] = []
    model = os.environ.get("CODEX_MODEL", "").strip()
    if model:
        args.extend(["--model", model])
    reasoning_effort = os.environ.get("CODEX_REASONING_EFFORT", DEFAULT_CODEX_REASONING_EFFORT).strip().lower()
    if reasoning_effort:
        if reasoning_effort not in {"low", "medium", "high"}:
            raise SiteGenerationError("CODEX_REASONING_EFFORT must be one of: low, medium, high")
        args.extend(["-c", f"model_reasoning_effort={_toml_string(reasoning_effort)}"])
    extra_args = os.environ.get("CODEX_EXTRA_ARGS", "").strip()
    if extra_args:
        args.extend(shlex.split(extra_args))
    return args


def _codex_exec_args() -> list[str]:
    sandbox = os.environ.get("CODEX_SANDBOX", "danger-full-access").strip()
    return ["exec", "--sandbox", sandbox, *_codex_config_args()]


def run_codex_refinement(site_path: Path, instruction: str, codex_command: str = "codex", timeout_seconds: int = 2400) -> None:
    if not site_path.exists():
        raise SiteGenerationError(f"Cannot run in missing site path: {site_path}")
    command = [*_codex_command(codex_command), *_codex_exec_args(), instruction]
    subprocess.run(command, cwd=site_path, check=True, text=True, env=load_local_env(), timeout=timeout_seconds)


def assert_plan_created(site_path: Path) -> None:
    missing = [
        str(path.relative_to(site_path))
        for path in (site_path / "DESIGN_SPEC.md", site_path / "data" / "implementation-plan.json")
        if not path.exists()
    ]
    if missing:
        raise SiteGenerationError("Codex plan stage did not create required file(s): " + ", ".join(missing))


def run_codex_site_pipeline(site_path: Path, raw_business: Mapping[str, Any]) -> None:
    run_codex_refinement(site_path, build_codex_plan_instruction(raw_business))
    assert_plan_created(site_path)
    for stage in CODEX_STAGE_SEQUENCE[1:]:
        run_codex_refinement(site_path, build_codex_stage_instruction(raw_business, stage))
    assert_replaced(site_path)


def generate_site(raw_business: Mapping[str, Any], output_dir: Path | str = DEFAULT_OUTPUT_DIR, refine_with_codex: bool = True, refine_with_claude: bool = False) -> GeneratedSite:
    generated = prepare_site_scaffold(raw_business, output_dir=output_dir)
    used_codex = False
    used_claude = False
    if refine_with_codex:
        run_codex_site_pipeline(generated.path, raw_business)
        used_codex = True
    if refine_with_claude:
        from .agentic_site_builder import run_claude_refinement
        business = normalize_business_profile(raw_business)
        run_claude_refinement(build_site_plan(business), generated.path)
        used_claude = True
    return GeneratedSite(
        slug=generated.slug,
        path=generated.path,
        business_name=generated.business_name,
        design_system=generated.design_system,
        refined_with_codex=used_codex,
        refined_with_claude=used_claude,
    )
