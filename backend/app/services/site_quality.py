"""Quality checks for generated websites.

The website builder can use Codex or Claude for refinement, but the repo still
needs a deterministic gate so bad, generic, or unsafe sites do not move forward
as if they are production-ready.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping

Severity = Literal["blocker", "major", "minor"]


@dataclass(frozen=True)
class QualityIssue:
    severity: Severity
    code: str
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.path:
            data["path"] = self.path
        return data


@dataclass(frozen=True)
class QualityReport:
    score: int
    passed: bool
    issues: list[QualityIssue] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "passed": self.passed,
            "issues": [issue.as_dict() for issue in self.issues],
            "summary": {
                "blockers": sum(1 for issue in self.issues if issue.severity == "blocker"),
                "majors": sum(1 for issue in self.issues if issue.severity == "major"),
                "minors": sum(1 for issue in self.issues if issue.severity == "minor"),
            },
        }


GENERIC_PHRASES = (
    "Local Service Company",
    "get local service work done clearly and reliably",
    "lorem ipsum",
    "best in class",
    "world-class",
    "award-winning",
    "trusted by thousands",
)

UNVERIFIED_CLAIMS = (
    "licensed and insured",
    "fully licensed",
    "certified experts",
    "guaranteed lowest price",
    "five-star rated",
    "#1",
    "number one",
    "best rated",
    "years of experience",
)

BAD_VERTICAL_DEFAULTS = {
    "restaurant-hospitality": ("Repair and service", "Installation", "Maintenance", "Assessment"),
    "professional-advisory": ("Repair and service", "Installation", "Maintenance"),
    "clinical-wellness": ("Repair and service", "Installation", "Maintenance"),
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _text_blob(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _issue(issues: list[QualityIssue], severity: Severity, code: str, message: str, path: str | None = None) -> None:
    issues.append(QualityIssue(severity=severity, code=code, message=message, path=path))


def _has_contact(business: Mapping[str, Any]) -> bool:
    return bool(business.get("phone") or business.get("email") or business.get("website"))


def _looks_like_public_image(url: Any) -> bool:
    if not isinstance(url, str):
        return False
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        return False
    lowered = url.lower()
    return not any(marker in lowered for marker in ("data:image", "base64,", "schema.org"))


def _service_titles(business: Mapping[str, Any]) -> list[str]:
    titles: list[str] = []
    for service in business.get("services", []) or []:
        if isinstance(service, Mapping):
            title = str(service.get("title", "")).strip()
        else:
            title = str(service).strip()
        if title:
            titles.append(title)
    return titles


def validate_generated_site(site_path: Path | str, minimum_score: int = 75) -> QualityReport:
    """Return a deterministic quality report for a generated site folder."""

    root = Path(site_path)
    issues: list[QualityIssue] = []

    business_path = root / "data" / "business.json"
    design_path = root / "data" / "design.json"
    sections_path = root / "data" / "sections.json"
    page_path = root / "app" / "page.tsx"
    package_path = root / "package.json"

    for required in (business_path, design_path, sections_path, page_path, package_path):
        if not required.exists():
            _issue(issues, "blocker", "missing-file", f"Missing required generated-site file: {required.relative_to(root)}", str(required))

    business: dict[str, Any] = {}
    sections: dict[str, Any] = {}
    if business_path.exists():
        try:
            business = _load_json(business_path)
        except json.JSONDecodeError as exc:
            _issue(issues, "blocker", "invalid-business-json", f"business.json is not valid JSON: {exc}", str(business_path))
    if sections_path.exists():
        try:
            sections = _load_json(sections_path)
        except json.JSONDecodeError as exc:
            _issue(issues, "blocker", "invalid-sections-json", f"sections.json is not valid JSON: {exc}", str(sections_path))

    if business:
        name = str(business.get("name", "")).strip()
        slug = str(business.get("slug", "")).strip()
        vertical = str(business.get("vertical", "")).strip()
        page_copy = business.get("pageCopy") or {}
        photos = business.get("photos") or []
        image_strategy = (sections.get("imageStrategy") or {}) if sections else {}

        if not name or name == "Local Service Company":
            _issue(issues, "blocker", "missing-business-name", "Generated site has no real business name.", str(business_path))
        if not slug:
            _issue(issues, "blocker", "missing-slug", "Generated site has no slug for output/repo naming.", str(business_path))
        if not str(business.get("businessType", "")).strip():
            _issue(issues, "major", "missing-business-type", "Business type is missing, so design/copy selection will be generic.", str(business_path))
        if not _has_contact(business):
            _issue(issues, "major", "missing-contact", "No phone, email, or website was provided; conversion CTA cannot point anywhere useful.", str(business_path))
        if len(_service_titles(business)) < 3:
            _issue(issues, "major", "thin-services", "Generated site should have at least three specific service/offer cards.", str(business_path))
        if len(business.get("faqs") or []) < 2:
            _issue(issues, "minor", "thin-faq", "Generated site should include at least two useful FAQ answers.", str(business_path))
        if not isinstance(page_copy, Mapping) or len(page_copy) < 4:
            _issue(issues, "major", "missing-page-copy", "Vertical-specific pageCopy is missing, so the template may fall back to generic copy.", str(business_path))

        blob = _text_blob(business)
        for phrase in GENERIC_PHRASES:
            if phrase.lower() in blob.lower():
                _issue(issues, "major", "generic-copy", f"Generic or low-trust phrase found: {phrase}", str(business_path))
        for claim in UNVERIFIED_CLAIMS:
            if claim.lower() in blob.lower():
                _issue(issues, "blocker", "unverified-claim", f"Unverified claim found: {claim}", str(business_path))

        for bad_title in BAD_VERTICAL_DEFAULTS.get(vertical, ()):  # vertical-specific sanity check
            if any(title.lower() == bad_title.lower() for title in _service_titles(business)):
                _issue(issues, "blocker", "wrong-vertical-default", f"{vertical} site still uses default service card: {bad_title}", str(business_path))

        if isinstance(photos, list):
            for index, photo in enumerate(photos[:8]):
                url = photo.get("url") if isinstance(photo, Mapping) else photo
                if not _looks_like_public_image(url):
                    _issue(issues, "major", "bad-photo-url", f"Photo {index + 1} is not a public http(s) image URL.", str(business_path))
        elif photos:
            _issue(issues, "major", "bad-photo-list", "business.photos must be a list.", str(business_path))

        if image_strategy.get("mode") == "photo-requested" and not photos:
            _issue(issues, "minor", "image-led-no-photos", "The vertical would benefit from real photos, but none were supplied.", str(business_path))

    penalty = 0
    for issue in issues:
        if issue.severity == "blocker":
            penalty += 35
        elif issue.severity == "major":
            penalty += 15
        else:
            penalty += 5

    score = max(0, 100 - penalty)
    passed = not any(issue.severity == "blocker" for issue in issues) and score >= minimum_score
    return QualityReport(score=score, passed=passed, issues=issues)


def write_quality_report(site_path: Path | str, report: QualityReport) -> Path:
    root = Path(site_path)
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    target = data_dir / "quality-report.json"
    target.write_text(json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def assert_quality_gate(site_path: Path | str, minimum_score: int = 75) -> QualityReport:
    report = validate_generated_site(site_path, minimum_score=minimum_score)
    write_quality_report(site_path, report)
    if not report.passed:
        summary = "; ".join(f"{issue.severity}:{issue.code}" for issue in report.issues[:6])
        raise ValueError(f"Generated site failed quality gate with score {report.score}: {summary}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a generated site folder and write data/quality-report.json.")
    parser.add_argument("site_path", help="Path to a generated site folder.")
    parser.add_argument("--min-score", type=int, default=75, help="Minimum score required for success.")
    args = parser.parse_args()

    report = validate_generated_site(args.site_path, minimum_score=args.min_score)
    write_quality_report(args.site_path, report)
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    if not report.passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
