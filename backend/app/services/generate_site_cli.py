"""CLI for testing generated websites on the Pi.

Example:
    python3 -m backend.app.services.generate_site_cli \
      --input examples/east-by-west-omakase.json \
      --codex
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .site_generator import DEFAULT_OUTPUT_DIR, generate_site
except ImportError:  # pragma: no cover - direct script fallback.
    from site_generator import DEFAULT_OUTPUT_DIR, generate_site


def _load_input(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Input JSON not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one local business website and write a quality report.")
    parser.add_argument("--input", required=True, help="Path to a lead/business JSON file.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR), help="Output folder for generated sites.")
    parser.add_argument("--codex", action="store_true", help="Run Codex refinement after the baseline template render.")
    parser.add_argument("--claude", action="store_true", help="Run Claude Code refinement after the baseline template render.")
    parser.add_argument("--min-score", type=int, default=75, help="Minimum quality score required for success.")
    parser.add_argument("--no-strict", action="store_true", help="Write quality report but do not fail on a low score.")
    args = parser.parse_args()

    lead = _load_input(Path(args.input))
    result = generate_site(
        lead,
        output_dir=Path(args.output),
        refine_with_codex=args.codex,
        refine_with_claude=args.claude,
        minimum_quality_score=args.min_score,
        strict_quality=not args.no_strict,
    )

    print(
        json.dumps(
            {
                "slug": result.slug,
                "business_name": result.business_name,
                "path": str(result.path),
                "design_system": result.design_system,
                "quality_score": result.quality_score,
                "quality_report_path": str(result.quality_report_path) if result.quality_report_path else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
