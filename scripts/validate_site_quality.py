#!/usr/bin/env python3
"""Validate a generated site folder.

Usage:
    python3 scripts/validate_site_quality.py generated_sites/<business-slug>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.site_quality import validate_generated_site, write_quality_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a generated site folder and write data/quality-report.json.")
    parser.add_argument("site_path", help="Path to generated site folder.")
    parser.add_argument("--min-score", type=int, default=75, help="Minimum score required for success.")
    args = parser.parse_args()

    report = validate_generated_site(args.site_path, minimum_score=args.min_score)
    write_quality_report(args.site_path, report)
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    if not report.passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
