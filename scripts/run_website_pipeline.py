"""One-command website generation pipeline.

This script is meant for the Raspberry Pi or any deployment machine. It removes
manual per-site steps by doing the whole local pipeline:

1. generate the site from one lead JSON file or every JSON file in a directory,
2. install npm dependencies inside each generated site,
3. run the Next.js build,
4. run the lightweight quality validator,
5. optionally start a local preview server for one generated site.

Usage:
    python3 scripts/run_website_pipeline.py leads/example-plumber.json
    python3 scripts/run_website_pipeline.py leads
    python3 scripts/run_website_pipeline.py leads --continue-on-error
    python3 scripts/run_website_pipeline.py leads/example-plumber.json --preview
    python3 scripts/run_website_pipeline.py leads/example-plumber.json --no-codex
"""

from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.site_generator import GeneratedSite, generate_site  # noqa: E402
from scripts.validate_site_quality import validate  # noqa: E402


class PipelineError(RuntimeError):
    """Raised when a required pipeline step fails."""


@dataclass(frozen=True)
class PipelineOptions:
    output_dir: Path
    claude: bool
    codex: bool
    skip_install: bool
    skip_build: bool
    skip_quality: bool


def run(command: Sequence[str], cwd: Path) -> None:
    printable = " ".join(command)
    print(f"\n▶ {printable}\n  cwd: {cwd}")
    subprocess.run(list(command), cwd=cwd, check=True, text=True)


def require_command(command: str, install_hint: str) -> None:
    if shutil.which(command):
        return
    raise PipelineError(f"Missing required command: {command}\n{install_hint}")


def detect_lan_ip() -> str:
    """Return the Pi's likely LAN IP for easier preview links."""

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "<raspberry-pi-ip>"


def resolve_profile_paths(profile_or_dir: Path) -> list[Path]:
    path = profile_or_dir if profile_or_dir.is_absolute() else REPO_ROOT / profile_or_dir
    if not path.exists():
        raise PipelineError(
            f"Lead file or folder not found: {path}\n"
            "Use `git pull origin main` to get the example lead, or put JSON lead files in `leads/`."
        )

    if path.is_file():
        if path.suffix.lower() != ".json":
            raise PipelineError(f"Lead file must be JSON: {path}")
        return [path]

    profiles = sorted(item for item in path.glob("*.json") if item.is_file())
    if not profiles:
        raise PipelineError(f"No .json lead files found in folder: {path}")
    return profiles


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


def run_one_profile(profile_path: Path, options: PipelineOptions) -> GeneratedSite:
    print(f"\n==============================")
    print(f"Generating from: {profile_path.relative_to(REPO_ROOT) if profile_path.is_relative_to(REPO_ROOT) else profile_path}")
    print(f"==============================")

    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    site = generate_site(
        profile,
        output_dir=options.output_dir,
        refine_with_claude=options.claude,
        refine_with_codex=options.codex,
    )

    print("\n✅ Site generated")
    print(json.dumps({
        "slug": site.slug,
        "path": str(site.path),
        "businessName": site.business_name,
        "designSystem": site.design_system,
        "refinedWithCodex": site.refined_with_codex,
        "refinedWithClaude": site.refined_with_claude,
    }, indent=2))

    if not options.skip_install:
        npm_install(site.path)

    if not options.skip_build:
        run(["npm", "run", "build"], cwd=site.path)

    if not options.skip_quality:
        run_quality_validator(site.path)

    print(f"\n✅ Complete: {site.slug}")
    return site


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate, install, build, and validate websites in one command.")
    parser.add_argument("profile", type=Path, help="Path to one JSON lead profile or a folder containing .json leads.")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "generated_sites")
    parser.add_argument("--claude", action="store_true", help="Run optional Claude Code subagent refinement after Codex generation.")
    parser.add_argument("--codex", action="store_true", help="Compatibility flag. Codex refinement is already on by default.")
    parser.add_argument("--no-codex", action="store_true", help="Disable Codex refinement for scaffold-only tests.")
    parser.add_argument("--skip-install", action="store_true", help="Skip npm install/ci.")
    parser.add_argument("--skip-build", action="store_true", help="Skip npm run build.")
    parser.add_argument("--skip-quality", action="store_true", help="Skip the Python quality validator.")
    parser.add_argument("--continue-on-error", action="store_true", help="When processing a folder, continue after one lead fails.")
    parser.add_argument("--preview", action="store_true", help="Start a generated-site preview server. Only allowed for one lead file.")
    parser.add_argument("--host", default="0.0.0.0", help="Preview host. Default exposes the preview on the local network.")
    parser.add_argument("--port", default="3010", help="Preview port. Default is 3010 so it does not collide with the app frontend on 3000.")
    args = parser.parse_args()

    try:
        require_command("npm", "Install Node.js 20+ on the Pi before running this pipeline.")
        profile_paths = resolve_profile_paths(args.profile)

        if args.preview and len(profile_paths) > 1:
            raise PipelineError("--preview can only be used with one lead JSON file, not a folder.")

        options = PipelineOptions(
            output_dir=args.output_dir,
            claude=args.claude,
            codex=not args.no_codex,
            skip_install=args.skip_install,
            skip_build=args.skip_build,
            skip_quality=args.skip_quality,
        )

        generated: list[GeneratedSite] = []
        failures: list[tuple[Path, str]] = []

        for profile_path in profile_paths:
            try:
                generated.append(run_one_profile(profile_path, options))
            except Exception as exc:  # noqa: BLE001 - batch mode should report and optionally continue.
                if not args.continue_on_error:
                    raise
                failures.append((profile_path, str(exc)))
                print(f"\n❌ Failed: {profile_path}\n{exc}", file=sys.stderr)

        print("\n==============================")
        print("Pipeline summary")
        print("==============================")
        print(f"Generated: {len(generated)}")
        for site in generated:
            print(f"- {site.slug}: {site.path}")

        if failures:
            print(f"\nFailed: {len(failures)}")
            for profile_path, error in failures:
                print(f"- {profile_path}: {error}")
            return 1

        if args.preview and generated:
            site = generated[0]
            lan_ip = detect_lan_ip()
            print("\nGenerated-site preview starting.")
            print(f"Local URL:   http://localhost:{args.port}")
            print(f"Network URL: http://{lan_ip}:{args.port}")
            print("Use this URL, not the app frontend on port 3000.")
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
