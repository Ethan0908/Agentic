"""One-command website generation pipeline.

This script is meant for the Raspberry Pi or any deployment machine. It removes
manual per-site steps by doing the whole local pipeline:

1. generate the site from a lead JSON file,
2. install npm dependencies inside the generated site,
3. run the Next.js build,
4. run the lightweight quality validator,
5. optionally start a local preview server.

Usage:
    python3 scripts/run_website_pipeline.py leads/example-plumber.json
    python3 scripts/run_website_pipeline.py leads/example-plumber.json --claude
    python3 scripts/run_website_pipeline.py leads/example-plumber.json --codex
    python3 scripts/run_website_pipeline.py leads/example-plumber.json --preview
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.site_generator import generate_site  # noqa: E402
from scripts.validate_site_quality import validate  # noqa: E402


class PipelineError(RuntimeError):
    """Raised when a required pipeline step fails."""


def run(command: Sequence[str], cwd: Path) -> None:
    printable = " ".join(command)
    print(f"\n▶ {printable}\n  cwd: {cwd}")
    subprocess.run(list(command), cwd=cwd, check=True, text=True)


def require_command(command: str, install_hint: str) -> None:
    if shutil.which(command):
        return
    raise PipelineError(f"Missing required command: {command}\n{install_hint}")


def npm_install(site_path: Path) -> None:
    package_json = site_path / "package.json"
    if not package_json.exists():
        raise PipelineError(f"Generated site is missing package.json: {package_json}")

    if (site_path / "package-lock.json").exists():
        run(["npm", "ci", "--no-audit", "--no-fund"], cwd=site_path)
    else:
        run(["npm", "install", "--no-audit", "--no-fund"], cwd=site_path)


def run_quality_validator(site_path: Path) -> None:
    findings = validate(site_path)
    if not findings:
        print("\n✅ Quality validator passed.")
        return

    for finding in findings:
        print(f"{finding.severity.upper()}: {finding.message}")

    if any(finding.severity in {"blocker", "major"} for finding in findings):
        raise PipelineError("Quality validator found blocker/major issues.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate, install, build, and validate a website in one command.")
    parser.add_argument("profile", type=Path, help="Path to a JSON business profile.")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "generated_sites")
    parser.add_argument("--claude", action="store_true", help="Run optional Claude Code subagent refinement after deterministic generation.")
    parser.add_argument("--codex", action="store_true", help="Run optional Codex refinement after deterministic generation.")
    parser.add_argument("--skip-install", action="store_true", help="Skip npm install/ci.")
    parser.add_argument("--skip-build", action="store_true", help="Skip npm run build.")
    parser.add_argument("--skip-quality", action="store_true", help="Skip the Python quality validator.")
    parser.add_argument("--preview", action="store_true", help="Start a dev preview server after generation/build. This command keeps running.")
    parser.add_argument("--host", default="0.0.0.0", help="Preview host. Default exposes the preview on the local network.")
    parser.add_argument("--port", default="3000", help="Preview port.")
    args = parser.parse_args()

    try:
        require_command("npm", "Install Node.js 20+ on the Pi before running this pipeline.")

        profile_path = args.profile if args.profile.is_absolute() else REPO_ROOT / args.profile
        if not profile_path.exists():
            raise PipelineError(f"Lead JSON file not found: {profile_path}")

        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        site = generate_site(
            profile,
            output_dir=args.output_dir,
            refine_with_claude=args.claude,
            refine_with_codex=args.codex,
        )

        print("\n✅ Site generated")
        print(json.dumps({
            "slug": site.slug,
            "path": str(site.path),
            "businessName": site.business_name,
            "designSystem": site.design_system,
        }, indent=2))

        if not args.skip_install:
            npm_install(site.path)

        if not args.skip_build:
            run(["npm", "run", "build"], cwd=site.path)

        if not args.skip_quality:
            run_quality_validator(site.path)

        print("\n✅ Pipeline complete.")
        print(f"Generated site folder: {site.path}")

        if args.preview:
            print(f"\nStarting preview on http://{args.host}:{args.port}")
            run(["npm", "run", "dev", "--", "--hostname", args.host, "--port", args.port], cwd=site.path)

        return 0
    except subprocess.CalledProcessError as exc:
        print(f"\n❌ Command failed with exit code {exc.returncode}.", file=sys.stderr)
        return exc.returncode or 1
    except Exception as exc:  # noqa: BLE001 - CLI should show clear error instead of traceback by default.
        print(f"\n❌ {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
