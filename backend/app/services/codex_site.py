from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from app.core.config import get_settings
from app.models import Business


CODEX_OUTPUT_FILE = "codex-output.json"


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
        "short_description": data.get("short_description"),
    }


async def improve_site_with_codex(
    site_dir: Path,
    business: Business,
    business_json: dict,
    fallback_repo_name: str | None = None,
) -> dict:
    """Use the logged-in Codex CLI to improve one generated website folder.

    Codex edits only the generated website folder and writes codex-output.json.
    The GitHub client reads that metadata file before creating the repo.
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
- Create a premium, mobile-first business landing page in this existing Next.js app.
- Use the supplied business_json and keep every claim truthful.
- Do not rely on the original business website URL to generate content. Treat it only as an optional outbound reference link if present.
- Keep the site self-contained, polished, fast, and conversion-focused.
- Keep calls, address/directions, email, phone, and original website link visible when available.
- Do not add new npm packages.
- Do not use external images that require scraping/downloading.
- Do not send emails, create GitHub repos, deploy to Vercel, or modify files outside this folder.
- Choose a clean GitHub/Vercel-safe repository name for this generated site.
- Write exactly one JSON metadata file named {CODEX_OUTPUT_FILE} in the project root with this shape:
  {{
    "repo_name": "lowercase-dash-separated-repo-name",
    "site_title": "short public site title",
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
