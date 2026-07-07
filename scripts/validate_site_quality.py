"""Lightweight quality gate for generated sites.

This is not a replacement for visual QA, but it catches common failures before a
site is deployed: missing plan files, generic AI copy, fake proof claims, weak
CTA data, placeholder code, and very thin React/CSS output.

Usage:
    python scripts/validate_site_quality.py generated_sites/example-site
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BANNED_GENERIC = (
    "top-notch",
    "best in class",
    "your trusted partner",
    "exceed expectations",
    "unparalleled",
    "world-class",
    "cutting-edge solutions",
    "passionate about serving",
)

UNVERIFIED_CLAIMS = (
    "award-winning",
    "licensed",
    "insured",
    "certified",
    "#1",
    "number one",
    "five-star",
    "5-star",
    "trusted by thousands",
    "guaranteed",
    "24/7",
    "same-day",
)

PLACEHOLDER_MARKERS = (
    "AGENTIC_REPLACE_ME",
    "generation-placeholder",
    "Lorem ipsum",
    "TODO",
)


@dataclass
class Finding:
    severity: str
    message: str


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(flatten_strings(item))
        return out
    if isinstance(value, dict):
        out = []
        for item in value.values():
            out.extend(flatten_strings(item))
        return out
    return []


def validate_code_quality(site_path: Path, business: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    page_path = site_path / "app" / "page.tsx"
    css_path = site_path / "app" / "globals.css"
    page = read_optional(page_path)
    css = read_optional(css_path)
    combined = f"{page}\n{css}"

    if not page:
        findings.append(Finding("blocker", "Missing app/page.tsx"))
    if not css:
        findings.append(Finding("blocker", "Missing app/globals.css"))
    if findings:
        return findings

    for marker in PLACEHOLDER_MARKERS:
        if marker in combined:
            findings.append(Finding("blocker", f"Placeholder/scaffold marker remains: {marker}"))

    if len(page.strip()) < 3500:
        findings.append(Finding("major", "app/page.tsx is very thin; Codex likely produced a shallow/template-like page."))
    if len(css.strip()) < 3500:
        findings.append(Finding("major", "app/globals.css is very thin; visual system likely lacks premium responsive styling."))

    if "@media" not in css:
        findings.append(Finding("major", "CSS has no media query; mobile layout probably was not designed intentionally."))
    if "clamp(" not in css:
        findings.append(Finding("minor", "CSS does not use clamp(); responsive typography/spacing may be less polished."))
    if not re.search(r"--[a-zA-Z0-9-]+\s*:", css):
        findings.append(Finding("minor", "CSS has no custom properties; design system may be less coherent."))

    has_contact_data = bool(business.get("phone") or business.get("email") or business.get("website") or business.get("address"))
    if has_contact_data and "href=" not in page:
        findings.append(Finding("major", "Business has contact data but page has no linked CTA/contact path."))

    photos = business.get("photos") or []
    if photos and not any(token in page for token in ("heroImage", "photos", "<img", "Image")):
        findings.append(Finding("major", "Business photos are supplied but page does not appear to render them."))

    repeated_cards = len(re.findall(r"className=\{?['\"][^'\"]*card", page, flags=re.IGNORECASE))
    if repeated_cards >= 8:
        findings.append(Finding("minor", "Many repeated card classes found; check that the layout is not a generic card grid."))

    return findings


def validate(site_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    data_dir = site_path / "data"
    required = ["business.json", "design.json", "sections.json", "site-plan.json"]

    for filename in required:
        if not (data_dir / filename).exists():
            findings.append(Finding("blocker", f"Missing data/{filename}"))

    if findings:
        return findings

    business = load(data_dir / "business.json")
    design = load(data_dir / "design.json")
    sections = load(data_dir / "sections.json")
    all_text = "\n".join(flatten_strings(business)).lower()

    if not business.get("primaryCta"):
        findings.append(Finding("blocker", "Missing primary CTA."))

    if not business.get("services") or len(business.get("services", [])) < 3:
        findings.append(Finding("major", "Fewer than three services. The page may feel thin."))

    if not design.get("id") or not design.get("tokens"):
        findings.append(Finding("blocker", "Missing design system id or tokens."))

    if not sections.get("heroVariant"):
        findings.append(Finding("blocker", "Missing hero variant."))

    for phrase in BANNED_GENERIC:
        if phrase in all_text:
            findings.append(Finding("major", f"Generic AI copy found: {phrase}"))

    supplied_proof = " ".join(flatten_strings({
        "proofPoints": business.get("proofPoints", []),
        "reviews": business.get("reviews", []),
        "guarantee": business.get("guarantee", ""),
    })).lower()
    for claim in UNVERIFIED_CLAIMS:
        if claim in all_text and claim not in supplied_proof:
            findings.append(Finding("major", f"Potential unverifiable claim: {claim}"))

    long_blocks = [text for text in flatten_strings(business) if len(re.sub(r"\s+", " ", text).strip()) > 280]
    if long_blocks:
        findings.append(Finding("minor", f"{len(long_blocks)} copy block(s) are probably too long for a landing page."))

    findings.extend(validate_code_quality(site_path, business))
    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_site_quality.py <site-path>")
        return 2

    site_path = Path(sys.argv[1])
    findings = validate(site_path)
    if not findings:
        print("PASS: generated site passed lightweight quality checks.")
        return 0

    for finding in findings:
        print(f"{finding.severity.upper()}: {finding.message}")

    return 1 if any(f.severity in {"blocker", "major"} for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
