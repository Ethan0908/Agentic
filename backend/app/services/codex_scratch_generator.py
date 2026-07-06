"""Codex-first website generator.

Python prepares a company brief, then Codex writes the one-page Next.js website
files inside the generated site folder from scratch. This is the path to use
when generated sites should not come from a fixed template.
"""

from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from .agentic_site_builder import build_site_plan
from .env_loader import load_local_env
from .industry_site_writer import brief_for
from .site_generator import DEFAULT_OUTPUT_DIR, GeneratedSite, normalize_business_profile, slugify

REQUIRED_FILES = [
    "package.json",
    "next.config.mjs",
    "tsconfig.json",
    "app/layout.tsx",
    "app/page.tsx",
    "app/globals.css",
]


def write_brief_files(target: Path, business: Mapping[str, Any]) -> dict[str, Any]:
    business = normalize_business_profile(business)
    site_plan = build_site_plan(business)
    creative = brief_for(business)
    data_dir = target / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "business.json").write_text(json.dumps(business, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (data_dir / "site-plan.json").write_text(json.dumps(site_plan.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (data_dir / "creative-brief.json").write_text(json.dumps(creative, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return creative


def build_codex_prompt(target: Path, business: Mapping[str, Any], creative: Mapping[str, Any]) -> str:
    industry = creative.get("industry", "custom")
    radius = creative.get("radius", "8px")
    card_radius = creative.get("cardRadius", "8px")
    hero = creative.get("images", {}).get("hero", "")
    secondary = creative.get("images", {}).get("secondary", "")
    return f"""You are inside an empty generated website folder: {target}.

Build a custom one-page Next.js App Router website from scratch for this company.
Read and use these data files:
- data/business.json
- data/site-plan.json
- data/creative-brief.json

Company: {business.get('name')}
Industry: {industry}
Service area: {business.get('serviceArea')}
Business type: {business.get('businessType')}
Main CTA: {business.get('primaryCta')}

Hard requirements:
- Create package.json, next.config.mjs, tsconfig.json, app/layout.tsx, app/page.tsx, app/globals.css.
- One page only.
- Do not use or copy any shared site-template folder.
- Do not make it look like a generic template.
- Make it appropriate for the industry.
- For plumbing/electrical/trade sites: use squared industrial geometry, dense practical service blocks, strong contrast, and minimal roundness.
- For clinics: use calmer spacing and softer geometry.
- For boutique/luxury: use image-led layout and more whitespace.
- For professional services: use serious editorial hierarchy.
- Use supplied photos or the creative brief image URLs.
- Hero image: {hero}
- Secondary image: {secondary}
- Border radius guidance: page radius {radius}, card radius {card_radius}.
- Do not invent awards, licenses, review counts, years in business, official certifications, guarantees, or availability.
- Avoid filler phrases like top-notch, best-in-class, world-class, trusted partner, and industry-leading.
- The first screen must show service, location, value, photo/media, and CTA.
- Build must pass with npm run build.

After creating the files, run npm run build if dependencies are installed. Fix any build errors you caused.
"""


def run_command(command: list[str], cwd: Path) -> None:
    print(f"\n▶ {' '.join(command)}\n  cwd: {cwd}")
    subprocess.run(command, cwd=cwd, check=True, text=True, env=load_local_env())


def run_codex(target: Path, prompt: str, codex_command: str = "codex") -> None:
    run_command([codex_command, "exec", prompt], cwd=target)


def verify_files(target: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (target / name).exists()]
    if missing:
        raise RuntimeError("Codex did not create required files: " + ", ".join(missing))


def detect_lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "<raspberry-pi-ip>"


def post_process(target: Path, install: bool, build: bool, quality: bool) -> None:
    if install:
        if (target / "package-lock.json").exists():
            run_command(["npm", "ci", "--no-audit", "--no-fund"], cwd=target)
        else:
            run_command(["npm", "install", "--no-audit", "--no-fund"], cwd=target)
    if build:
        run_command(["npm", "run", "build"], cwd=target)
    if quality:
        repo_root = Path(__file__).resolve().parents[3]
        run_command([sys.executable, str(repo_root / "scripts" / "validate_site_quality.py"), str(target)], cwd=repo_root)


def generate_site(raw_business: Mapping[str, Any], output_dir: Path | str = DEFAULT_OUTPUT_DIR, codex_command: str = "codex") -> GeneratedSite:
    business = normalize_business_profile(raw_business)
    slug = slugify(business["slug"])
    target = Path(output_dir) / slug
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    creative = write_brief_files(target, business)
    prompt = build_codex_prompt(target, business, creative)
    (target / "CODEX_WEBSITE_BRIEF.md").write_text(prompt, encoding="utf-8")
    run_codex(target, prompt, codex_command=codex_command)
    verify_files(target)
    return GeneratedSite(slug=slug, path=target, business_name=business["name"], design_system=f"codex-scratch:{creative.get('industry', 'custom')}")


def load_profiles(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(item for item in path.glob("*.json") if item.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate websites from scratch with Codex.")
    parser.add_argument("profile", type=Path, help="One lead JSON file or a folder of lead JSON files.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-quality", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default="3010")
    args = parser.parse_args()

    profile_path = args.profile if args.profile.is_absolute() else Path.cwd() / args.profile
    results: list[GeneratedSite] = []
    for item in load_profiles(profile_path):
        raw = json.loads(item.read_text(encoding="utf-8"))
        site = generate_site(raw, output_dir=args.output_dir, codex_command=args.codex_command)
        post_process(site.path, install=not args.skip_install, build=not args.skip_build, quality=not args.skip_quality)
        results.append(site)

    print(json.dumps([
        {"slug": site.slug, "path": str(site.path), "businessName": site.business_name, "designSystem": site.design_system}
        for site in results
    ], indent=2))

    if args.preview:
        if len(results) != 1:
            raise RuntimeError("Preview supports exactly one lead at a time.")
        print(f"Local URL:   http://localhost:{args.port}")
        print(f"Network URL: http://{detect_lan_ip()}:{args.port}")
        run_command(["npm", "run", "dev", "--", "--hostname", args.host, "--port", args.port], cwd=results[0].path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
