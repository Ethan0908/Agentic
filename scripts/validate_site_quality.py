"""Lightweight quality gate for generated sites.

This is not a replacement for visual QA, but it catches common failures before a
site is deployed: missing plan files, generic AI copy, fake proof claims, weak
CTA data, and oversized text blocks.

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


@dataclass
class Finding:
    severity: str
    message: str


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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

    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_site_quality.py <site-path>")
        return 2

    site_path = Path(sys.argv[1])
    findings = validate(site_path)
    if not findings:
        print("PASS: generated site data passed lightweight quality checks.")
        return 0

    for finding in findings:
        print(f"{finding.severity.upper()}: {finding.message}")

    return 1 if any(f.severity in {"blocker", "major"} for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
