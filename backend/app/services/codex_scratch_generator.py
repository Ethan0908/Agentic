"""Codex-first website generator.

Python prepares a company brief, then Codex writes the one-page Next.js website
files inside the generated site folder from scratch. This is the path to use
when generated sites should not come from a fixed template.
"""

from __future__ import annotations

import argparse
import json
import os
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
    layout = creative.get("layout", "custom")
    density = creative.get("density", "balanced")
    hero = creative.get("images", {}).get("hero", "")
    secondary = creative.get("images", {}).get("secondary", "")
    return f"""You are inside an empty generated website folder: {target}.

You are not refining a template. Build a custom one-page Next.js App Router website from scratch for this exact company.

Read and use these files before writing code:
- data/business.json
- data/site-plan.json
- data/creative-brief.json

Company: {business.get('name')}
Industry: {industry}
Layout direction: {layout}
Density: {density}
Service area: {business.get('serviceArea')}
Business type: {business.get('businessType')}
Main CTA: {business.get('primaryCta')}

Required files to create:
- package.json
- next.config.mjs
- tsconfig.json
- app/layout.tsx
- app/page.tsx
- app/globals.css

Core rules:
- One page only.
- Do not use or copy site-template, variants, existing generated pages, or generic landing-page skeletons.
- Do not create a theme-switching system. Make one finished website for this company.
- Do not make a soft SaaS/bento/luxury template unless the industry brief actually calls for it.
- Use the creative brief as constraints, not as a layout template.
- The first screen must immediately show: service type, service area, value proposition, photo/media, and primary CTA.
- Use real image URLs from the brief or profile. Do not leave blank gray boxes.
- Hero image: {hero}
- Secondary image: {secondary}
- Build must pass with npm run build.

Industry execution rules:
- Plumbing/electrical/HVAC/trades: industrial, practical, squared, utility-first. Use tight spacing, straight edges, service tables/lists, job-intake panel, dark utility band, strong CTA. Avoid pill buttons except tiny labels. Avoid bubbly cards, luxury serif styling, soft gradients, and excessive roundness.
- Clinics/medical/wellness: calm, bright, accessible, reassuring, moderate softness, appointment-focused hierarchy.
- Law/finance/accounting/consulting: serious editorial layout, restrained color, strong typographic hierarchy, clear decision path.
- Spa/salon/interior/hospitality/boutique: visual-led, image-forward, generous whitespace, elegant but not fake luxury.
- Software/agency/AI: productized sections, proof of process, compact bento only when appropriate.

Geometry constraints:
- Page radius guidance: {radius}
- Card radius guidance: {card_radius}
- For trade industries, most cards should be 0-8px radius. No giant 24px/32px cards. No rounded-full buttons except small tags if useful.

Copy rules:
- Use specific services, location, and process from business.json.
- Do not invent awards, licenses, insurance, review counts, years in business, official certifications, guarantees, emergency availability, or same-day service.
- Avoid filler: top-notch, best-in-class, world-class, trusted partner, unparalleled, industry-leading, exceed expectations.
- Keep copy scannable. Avoid long paragraphs.
- Make CTAs practical: call, request service, send details, schedule, get quote path.

Visual quality bar:
- It should look like a paid local-agency one-page build, not an AI default landing page.
- Use strong composition: asymmetry, image crop, content hierarchy, responsive layout, and purposeful whitespace.
- Add visual specificity for the sector: plumbing can include pipe/worksite imagery, job-intake block, service checklist, urgency strip, and rougher industrial rhythm.
- Mobile must be clean and conversion-focused.

Implementation rules:
- Use plain React/Next and CSS. No Tailwind unless you fully configure it.
- Do not depend on external UI libraries.
- Use ordinary img tags for remote images unless you configure Next images correctly.
- Keep TypeScript valid.
- After writing files, run npm run build if dependencies are installed and fix any errors you caused.
"""


def codex_candidates(command: str) -> list[str]:
    if "/" in command:
        return [command]
    candidates = [
        shutil.which(command),
        str(Path.home() / ".npm-global" / "bin" / command),
        "/usr/bin/codex" if command == "codex" else None,
        "/bin/codex" if command == "codex" else None,
        str(Path.home() / ".local" / "bin" / command),
    ]
    seen: set[str] = set()
    out: list[str] = []
    for item in candidates:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def executable_works(path: str) -> tuple[bool, str]:
    if not Path(path).exists():
        return False, "not found"
    if not os.access(path, os.X_OK):
        return False, "not executable"
    try:
        result = subprocess.run([path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=12, env=load_local_env())
    except OSError as exc:
        return False, f"cannot execute: {exc}"
    except subprocess.TimeoutExpired:
        return False, "timed out running --version"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip().splitlines()[:2]
        return False, "; ".join(detail) or f"exit code {result.returncode}"
    return True, (result.stdout or result.stderr).strip()


def resolve_executable(command: str) -> str:
    failures: list[str] = []
    for candidate in codex_candidates(command):
        ok, detail = executable_works(candidate)
        if ok:
            if candidate != shutil.which(command):
                print(f"Using working Codex executable: {candidate}")
            return candidate
        failures.append(f"- {candidate}: {detail}")
    raise RuntimeError(
        f"No working executable found for {command}.\n"
        + "\n".join(failures)
        + "\n\nYour first PATH result may be a broken standalone binary for the Pi. "
        "Try rerunning with `--codex-command /usr/bin/codex`, or remove/rename the broken ~/.local/bin/codex symlink."
    )


def run_command(command: list[str], cwd: Path) -> None:
    if command[0] not in {sys.executable, "npm", "node"}:
        command[0] = resolve_executable(command[0])
    print(f"\n▶ {' '.join(command[:2])} ...\n  cwd: {cwd}")
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

    try:
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
    except Exception as exc:
        print(f"\n❌ {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
