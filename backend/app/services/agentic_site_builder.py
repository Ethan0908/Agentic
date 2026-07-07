"""Token-efficient multi-agent planning for premium generated websites.

The builder should not rely on one generic template or one huge prompt. This
module creates a compact site plan that lets the template render different
visual systems and lets Claude Code subagents refine only the parts they own.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

try:
    from .env_loader import load_local_env
except ImportError:  # pragma: no cover - lets this file run as a direct script during local debugging.
    from env_loader import load_local_env


REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "backend" / "app" / "config"
DESIGN_SYSTEMS_FILE = CONFIG_DIR / "design_systems.json"
SECTION_REGISTRY_FILE = CONFIG_DIR / "section_registry.json"
TOKEN_BUDGET_FILE = CONFIG_DIR / "token_budget.json"


@dataclass(frozen=True)
class SitePlan:
    """Compact shared context passed between generator, template, and agents."""

    business: dict[str, Any]
    design: dict[str, Any]
    sections: dict[str, Any]
    agent_brief: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "business": self.business,
            "design": self.design,
            "sections": self.sections,
            "agentBrief": self.agent_brief,
        }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact_text(value: Any, max_chars: int) -> str:
    """Collapse whitespace and cap text for agent prompts."""

    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def compact_json(value: Mapping[str, Any], max_chars: int = 5000) -> str:
    """Return minified JSON capped for token-efficient prompt handoff."""

    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "}"


def _search_blob(business: Mapping[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "name", "businessType", "business_type", "category", "headline", "subheadline", "serviceArea",
        "service_area", "city", "description", "address",
    ):
        value = business.get(key)
        if value:
            parts.append(str(value))
    for key in ("services", "contentAngles", "visitorQuestions", "proofPoints"):
        for item in business.get(key, []) or []:
            if isinstance(item, Mapping):
                parts.extend(str(value) for value in item.values())
            else:
                parts.append(str(item))
    return " ".join(parts).lower()


def select_design_system(business: Mapping[str, Any]) -> dict[str, Any]:
    """Select a design system using deterministic keywords.

    This is intentionally cheap and predictable. Codex can later override the
    choice, but the baseline no longer looks identical for every business.
    """

    systems = load_json(DESIGN_SYSTEMS_FILE)
    blob = _search_blob(business)

    best_id = "premium-local-service"
    best_score = -1
    for system_id, system in systems.items():
        score = sum(1 for term in system.get("bestFor", []) if term.lower() in blob)
        if score > best_score:
            best_id = system_id
            best_score = score

    chosen = dict(systems[best_id])
    chosen["id"] = best_id
    return chosen


def detect_intent(business: Mapping[str, Any]) -> dict[str, bool]:
    blob = _search_blob(business)
    emergency_terms = ("emergency", "urgent", "24/7", "same day", "sewer", "leak", "water damage", "locksmith", "towing")
    appointment_terms = ("clinic", "dental", "dentist", "medical", "appointment", "therapy", "consultation", "spa", "salon", "barber")
    professional_terms = ("law", "legal", "finance", "accounting", "insurance", "mortgage", "advisory", "consulting")
    image_led_terms = ("restaurant", "bakery", "catering", "salon", "spa", "wedding", "photography", "interior", "design", "hotel", "fitness")
    photos = business.get("photos") or []
    return {
        "emergency": any(term in blob for term in emergency_terms),
        "appointment": any(term in blob for term in appointment_terms),
        "professional": any(term in blob for term in professional_terms),
        "imageLed": bool(photos) or any(term in blob for term in image_led_terms),
        "hasPhotos": bool(photos),
        "hasReviews": bool(business.get("reviews")) or bool(business.get("rating")) or bool(business.get("reviewCount")),
        "hasPhone": bool(business.get("phone")),
        "hasWebsite": bool(business.get("website")),
        "hasAddress": bool(business.get("address")),
    }


def build_image_strategy(business: Mapping[str, Any], design: Mapping[str, Any], intent: Mapping[str, bool]) -> dict[str, Any]:
    """Describe how the template and agents should use visuals.

    This keeps image handling explicit so Codex/Claude do not randomly add stock
    photos. If photos are missing, agents should improve composition with CSS and
    request/collect real business images upstream.
    """

    photos = business.get("photos") or []
    if photos:
        return {
            "mode": "use-supplied-business-photos",
            "heroPhoto": photos[0],
            "galleryCount": min(len(photos), 6),
            "rules": [
                "Use only photos supplied in data/business.json unless the user explicitly provides more.",
                "Do not add unrelated stock photography.",
                "Crop with object-fit cover; keep alt text descriptive and business-specific.",
                "If a photo is low quality, keep it smaller and rely more on typography/cards.",
            ],
        }

    fallback_mode = "graphic-editorial" if design.get("layoutPattern") != "gallery-bento" else "photo-requested"
    return {
        "mode": fallback_mode,
        "heroPhoto": None,
        "galleryCount": 0,
        "rules": [
            "No real business photos were supplied. Do not fabricate or hotlink stock photos.",
            "Use layout, typography, cards, gradients, and service-specific microcopy to create quality.",
            "If the scraper can collect public photos from the business's own website or profile, add them to business.photos before generation.",
        ],
    }


def _conversion_goal(intent: Mapping[str, bool]) -> str:
    if intent["emergency"] and intent["hasPhone"]:
        return "phone-first urgent contact"
    if intent["appointment"] and intent["hasPhone"]:
        return "call or book appointment"
    if intent["hasWebsite"] and not intent["hasPhone"]:
        return "official-website handoff"
    if intent["hasAddress"]:
        return "location and visit planning"
    if intent["hasPhone"]:
        return "phone-first inquiry"
    return "request information"


def build_section_plan(business: Mapping[str, Any], design: Mapping[str, Any]) -> dict[str, Any]:
    registry = load_json(SECTION_REGISTRY_FILE)
    intent = detect_intent(business)
    layout = str(design.get("layoutPattern", "split-panel"))
    image_strategy = build_image_strategy(business, design, intent)

    if intent["emergency"]:
        process = "rapid-response"
        final_cta = "call" if intent["hasPhone"] else "quote"
        proof = "phone-proof"
        services = "checklist"
    elif intent["professional"]:
        process = "consultative"
        final_cta = "consultation"
        proof = "trust-strip"
        services = "cards"
    elif intent["appointment"]:
        process = "consultative"
        final_cta = "booking"
        proof = "bento-proof"
        services = "cards"
    else:
        process = "three-step"
        final_cta = "quote"
        proof = "trust-strip"
        services = "cards"

    return {
        "heroVariant": layout if layout in registry["hero"] else "split-panel",
        "proofVariant": proof,
        "servicesVariant": services,
        "processVariant": process,
        "proofOrExpectation": "reviews" if intent["hasReviews"] else "expectations",
        "finalCtaVariant": final_cta,
        "conversionGoal": _conversion_goal(intent),
        "contentAngles": business.get("contentAngles", []),
        "visitorQuestions": business.get("visitorQuestions", []),
        "requiredSectionCount": 9,
        "imageStrategy": image_strategy,
        "sectionOrder": [
            "navigation",
            "hero",
            "credibilityStrip",
            "positioningThesis",
            "serviceArchitecture",
            "decisionGuide",
            "processOrVisitFlow",
            "proofOrExpectations",
            "locationOrServiceArea",
            "faqOrVisitorQuestions",
            "finalCta",
            "footer",
        ],
        "layoutRhythmRequirements": design.get("sectionRhythms", []),
        "componentRecipes": design.get("componentRecipes", []),
        "forbiddenPatterns": design.get("forbiddenPatterns", []),
        "intent": intent,
        "registryNotes": {
            "hero": registry["hero"].get(layout, registry["hero"]["split-panel"]),
            "proof": registry["proof"][proof],
            "services": registry["services"][services],
            "process": registry["process"][process],
            "finalCta": registry["finalCta"][final_cta],
        },
    }


def build_agent_brief(business: Mapping[str, Any], design: Mapping[str, Any], sections: Mapping[str, Any]) -> dict[str, Any]:
    token_budget = load_json(TOKEN_BUDGET_FILE)
    budget = token_budget["default"]
    image_strategy = sections.get("imageStrategy", {})
    return {
        "briefVersion": 3,
        "goal": "Create a premium, high-converting local business website without fake claims or generic AI copy.",
        "businessSummary": compact_text(
            {
                "name": business.get("name"),
                "type": business.get("businessType"),
                "area": business.get("serviceArea"),
                "address": business.get("address"),
                "rating": business.get("rating"),
                "reviewCount": business.get("reviewCount"),
                "cta": business.get("primaryCta"),
                "services": business.get("services", [])[:6],
                "contentAngles": business.get("contentAngles", [])[:6],
                "visitorQuestions": business.get("visitorQuestions", [])[:5],
                "proofPoints": business.get("proofPoints", [])[:6],
            },
            budget["briefMaxChars"],
        ),
        "designSummary": compact_text(
            {
                "system": design.get("id"),
                "label": design.get("label"),
                "visualLanguage": design.get("visualLanguage"),
                "layoutPattern": design.get("layoutPattern"),
                "fontPairing": design.get("fontPairing"),
                "heroPattern": design.get("heroPattern"),
                "sectionRhythms": design.get("sectionRhythms"),
                "componentRecipes": design.get("componentRecipes"),
                "forbiddenPatterns": design.get("forbiddenPatterns"),
                "imageStrategy": image_strategy,
            },
            budget["designPlanMaxChars"],
        ),
        "sectionSummary": compact_text(sections, budget["copyPlanMaxChars"]),
        "hardRules": [
            "Do not invent awards, licences, review counts, guarantees, years in business, or emergency availability.",
            "Use supplied business photos when present; do not use unrelated stock images.",
            "Use enriched contentAngles and visitorQuestions as editorial prompts, not fake factual claims.",
            "Prefer short specific copy over vague promotional copy.",
            "Produce at least 9 meaningful sections plus a footer.",
            "Use next/font/google and do not leave browser default font stacks as the visual identity.",
            "Preserve buildability and Vercel deployment assumptions.",
            "Fix mobile first: no horizontal overflow, readable text, obvious CTA.",
        ],
        "tokenPolicy": token_budget["principles"],
        "agentModels": token_budget["agentModels"],
    }


def build_site_plan(business: Mapping[str, Any]) -> SitePlan:
    design = select_design_system(business)
    sections = build_section_plan(business, design)
    agent_brief = build_agent_brief(business, design, sections)
    return SitePlan(dict(business), design, sections, agent_brief)


def write_site_plan(target: Path, site_plan: SitePlan) -> None:
    data_dir = target / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "design.json").write_text(json.dumps(site_plan.design, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (data_dir / "sections.json").write_text(json.dumps(site_plan.sections, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (data_dir / "site-plan.json").write_text(json.dumps(site_plan.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_claude_agent_prompt(site_plan: SitePlan, target_path: Path) -> str:
    """Create a compact Claude Code prompt that delegates to project subagents."""

    budget = load_json(TOKEN_BUDGET_FILE)["default"]
    plan_json = compact_json(site_plan.as_dict(), max_chars=budget["agentPromptMaxChars"])
    return f"""Improve this generated website using the project Claude agents.

Target folder: {target_path}
Compact site plan JSON: {plan_json}

Workflow:
1. Use @business-profiler to verify the brief, vertical, image availability, and safe claims.
2. Use @conversion-strategist to check the section order, CTA hierarchy, and objection handling.
3. Use @brand-director to refine the visual direction only if the selected design system is weak.
4. Use @copy-polisher to remove generic copy and improve CTA clarity.
5. Use @frontend-refiner to improve React/CSS only where it materially improves quality.
6. Use @visual-qa to review mobile/desktop quality and list fixes.

Constraints:
- Keep changes minimal and high leverage.
- Use supplied business photos when present; do not add unrelated stock photos.
- Do not paste whole files into agent prompts unless necessary.
- Do not invent claims.
- Run the build if dependencies are installed.
"""


def run_claude_refinement(site_plan: SitePlan, target_path: Path, claude_command: str = "claude") -> None:
    """Optional Claude Code refinement entrypoint.

    The repo contains `.claude/agents/` definitions. This function only launches
    Claude when the runtime has the CLI installed and the caller explicitly asks
    for it. `.env` and `.env.local` are forwarded to the subprocess so local
    OAuth/API variables can be used without hardcoding secrets.
    """

    prompt = build_claude_agent_prompt(site_plan, target_path)
    subprocess.run([claude_command, "-p", prompt], cwd=REPO_ROOT, check=True, text=True, env=load_local_env())
