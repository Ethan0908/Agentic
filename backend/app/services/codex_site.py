from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from app.core.config import get_settings
from app.models import Business


def _codex_command() -> str | None:
    return shutil.which("codex")


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


async def improve_site_with_codex(site_dir: Path, business: Business, business_json: dict) -> dict:
    """Use the logged-in Codex CLI to improve one generated website folder.

    This expects the backend container to have the Codex CLI installed and the
    Pi's ~/.codex mounted into /root/.codex. It intentionally operates only in
    the generated website folder.
    """
    settings = get_settings()
    if not settings.codex_enabled:
        return {"codex_ran": False, "reason": "CODEX_ENABLED=false"}

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
- Improve the website so it looks like a premium, mobile-first business landing page.
- Use the existing business.json data and keep the site truthful.
- Keep it a simple Next.js app router project.
- Do not add new npm packages.
- Do not use external images that require scraping or downloading.
- Make the homepage polished, clear, and conversion-focused.
- Keep calls, directions/address, original website link, and email/phone visible when available.
- Preserve package.json, next.config.mjs, tsconfig.json, and business.json unless a small fix is required.
- Do not send emails, create GitHub repos, deploy to Vercel, or modify files outside this folder.
- Finish by leaving the edited files on disk.
""".strip()

    command = [codex, "exec", "--sandbox", "workspace-write"]
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

    return {
        "codex_ran": True,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }
