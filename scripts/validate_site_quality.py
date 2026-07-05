"""Lightweight quality gate for generated sites."""

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
    "industry-leading",
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
        out: list[str] = []
        for item in value.values():
            out.extend(flatten_strings(item))
        return out
    return []


def validate(site_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    data_dir = site_path / "data"
    business_file = data_dir / "business.json"
    plan_file = data_dir / "site-plan.json"
    creative_file = data_dir / "creative-brief.json"

    for file_path in (business_file, plan_file):
        if not file_path.exists():
            findings.append(Finding("blocker", f"Missing {file_path.relative_to(site_path)}"))
    if findings:
        return findings

    business = load(business_file)
    plan = load(plan_file)
    creative = load(creative_file) if creative_file.exists() else {}
    all_text = "\n".join(flatten_strings({"business": business, "plan": plan, "creative": creative})).lower()

    if not business.get("primaryCta"):
        findings.append(Finding("blocker", "Missing primary CTA."))
    if not business.get("services") or len(business.get("services", [])) < 3:
        findings.append(Finding("major", "Fewer than three services. The page may feel thin."))
    if creative_file.exists() and not creative.get("archetype"):
        findings.append(Finding("major", "Custom site is missing creative archetype."))

    for phrase in BANNED_GENERIC:
        if phrase in all_text:
            findings.append(Finding("major", f"Generic copy found: {phrase}"))

    supplied_proof = " ".join(flatten_strings({
        "proofPoints": business.get("proofPoints", []),
        "reviews": business.get("reviews", []),
        "guarantee": business.get("guarantee", ""),
    })).lower()
    for claim in UNVERIFIED_CLAIMS:
        if claim in all_text and claim not in supplied_proof:
            findings.append(Finding("major", f"Potential unverifiable claim: {claim}"))

    long_blocks = [text for text in flatten_strings(business) if len(re.sub(r"\s+", " ", text).strip()) > 320]
    if long_blocks:
        findings.append(Finding("minor", f"{len(long_blocks)} copy block(s) may be too long."))
    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate_site_quality.py <site-path>")
        return 2
    findings = validate(Path(sys.argv[1]))
    if not findings:
        print("PASS: generated site passed lightweight quality checks.")
        return 0
    for finding in findings:
        print(f"{finding.severity.upper()}: {finding.message}")
    return 1 if any(f.severity in {"blocker", "major"} for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
