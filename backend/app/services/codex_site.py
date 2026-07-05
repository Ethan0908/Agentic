from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from app.core.config import get_settings
from app.models import Business


CODEX_OUTPUT_FILE = "codex-output.json"
PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "prompts" / "website_generation_prompt.md"
REQUIRED_SITE_FILES = ["package.json", "app/layout.tsx", "app/page.tsx", "app/globals.css"]
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
                "id": business.id,
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


def _metadata_shape() -> str:
    return json.dumps(
        {
            "repo_name": "lowercase-dash-separated-repo-name",
            "site_title": "short public site title",
            "business_type": "specific inferred type",
            "design_style": "specific design style",
            "primary_cta": "main conversion action",
            "short_description": "one sentence summary",
            "research_summary": "one sentence describing the design logic used",
        },
        indent=2,
    )


def _load_prompt_template() -> str:
    if not PROMPT_TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Codex prompt file not found: {PROMPT_TEMPLATE_PATH}")
    return PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")


def _render_prompt(site_dir: Path, business: Business, business_json: dict) -> str:
    return (
        _load_prompt_template()
        .replace("{{BUSINESS_CONTEXT}}", _business_context(business, business_json))
        .replace("{{CODEX_OUTPUT_FILE}}", CODEX_OUTPUT_FILE)
        .replace("{{METADATA_SHAPE}}", _metadata_shape())
        .replace("{{SITE_DIR}}", str(site_dir))
    ).strip()


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


def _write_business_json(site_dir: Path, business_json: dict) -> None:
    (site_dir / "business.json").write_text(json.dumps(business_json, indent=2), encoding="utf-8")


def _validate_required_files(site_dir: Path) -> None:
    missing = [path for path in REQUIRED_SITE_FILES if not (site_dir / path).exists()]
    if missing:
        raise RuntimeError(f"Generated site is incomplete. Missing required files: {', '.join(missing)}")


def _validate_business_json(site_dir: Path) -> None:
    path = site_dir / "business.json"
    if not path.exists():
        raise RuntimeError("Generated site is missing business.json")
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"business.json is invalid JSON: {exc}") from exc


async def improve_site_with_codex(
    site_dir: Path,
    business: Business,
    business_json: dict,
    fallback_repo_name: str | None = None,
) -> dict:
    """Run Codex against a copied website template."""
    settings = get_settings()
    fallback_repo_name = normalise_repo_name(fallback_repo_name or business.name)

    _write_business_json(site_dir, business_json)
    _validate_required_files(site_dir)

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

    prompt = _render_prompt(site_dir, business, business_json)

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

    _validate_required_files(site_dir)
    _validate_business_json(site_dir)

    metadata = read_codex_output(site_dir, fallback_repo_name)
    return {
        "codex_ran": True,
        **metadata,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }
