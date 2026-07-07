"""Generate a website from a JSON business profile.

Usage:
    python scripts/generate_site.py lead.json
    python scripts/generate_site.py lead.json --claude
    python scripts/generate_site.py lead.json --no-codex
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.site_generator import generate_site  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a premium local-business website.")
    parser.add_argument("profile", type=Path, help="Path to a JSON business profile.")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "generated_sites")
    parser.add_argument("--claude", action="store_true", help="Run optional Claude Code subagent refinement.")
    parser.add_argument("--codex", action="store_true", help="Compatibility flag. Codex refinement is already on by default.")
    parser.add_argument("--no-codex", action="store_true", help="Disable Codex refinement for scaffold-only tests.")
    args = parser.parse_args()

    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    site = generate_site(
        profile,
        output_dir=args.output_dir,
        refine_with_claude=args.claude,
        refine_with_codex=not args.no_codex,
    )

    print(json.dumps({
        "slug": site.slug,
        "path": str(site.path),
        "businessName": site.business_name,
        "designSystem": site.design_system,
        "refinedWithCodex": site.refined_with_codex,
        "refinedWithClaude": site.refined_with_claude,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
