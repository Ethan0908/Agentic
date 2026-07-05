from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .agentic_site_builder import build_site_plan
from .custom_site_project import write_project_files
from .site_generator import DEFAULT_OUTPUT_DIR, GeneratedSite, normalize_business_profile, slugify


def generate_site(raw_business: Mapping[str, Any], output_dir: Path | str = DEFAULT_OUTPUT_DIR, refine_with_codex: bool = False, refine_with_claude: bool = False) -> GeneratedSite:
    business = normalize_business_profile(raw_business)
    plan = build_site_plan(business)
    slug = slugify(business["slug"])
    target = Path(output_dir) / slug
    target.mkdir(parents=True, exist_ok=True)
    brief = write_project_files(target, business, plan.as_dict())
    return GeneratedSite(slug=slug, path=target, business_name=business["name"], design_system=str(brief.get("archetype", "custom")))
