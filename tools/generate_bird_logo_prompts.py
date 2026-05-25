#!/usr/bin/env python3
"""Generate persona-isolated Adobe Express Bird logo prompts.

The generator intentionally avoids third-party dependencies so it can run in a
fresh Cursor Cloud or desktop checkout. It accepts flexible JSON structures,
maps persona behavior to Adobe Express capabilities, and writes HTML, DOCX, and
JSON deliverables.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence
from xml.sax.saxutils import escape as xml_escape


DEFAULT_WINDOWS_INPUT = (
    r"C:\Users\subash.b\OneDrive - Qualitest Group\Desktop"
    r"\persona_background_test_cases.json"
)
LOCAL_INPUT_NAME = "persona_background_test_cases.json"
FEATURE_SOURCE_URL = "https://www.adobe.com/in/express/feature"

EMBEDDED_FEATURES: List[Dict[str, str]] = [
    {
        "name": "Edit images, videos and PDFs in just a few clicks",
        "short_name": "Quick Actions",
        "description": (
            "Resize content, convert files, remove backgrounds, and add animated "
            "effects quickly."
        ),
    },
    {
        "name": "Make it all. All in one place",
        "short_name": "All-in-one editor",
        "description": (
            "Create marketing, social, video, photo, and PDF content in one editor."
        ),
    },
    {
        "name": "Design with AI",
        "short_name": "Firefly generative AI",
        "description": (
            "Use Adobe Firefly text-to-image and Generate Text Effect tools from "
            "natural language prompts."
        ),
    },
    {
        "name": "Make content that always stands out",
        "short_name": "Templates for logos and more",
        "description": (
            "Start from thousands of free templates, including business cards, "
            "social media graphics, posters, flyers, and logos."
        ),
    },
    {
        "name": "Get free Adobe Stock images, videos and music",
        "short_name": "Adobe Stock assets",
        "description": (
            "Use royalty-free Adobe Stock photos, videos, and audio assets when a "
            "licensed reference or supporting asset is needed."
        ),
    },
    {
        "name": "Take command of social content",
        "short_name": "Content scheduler",
        "description": (
            "Plan, schedule, preview, and publish social content from Adobe Express."
        ),
    },
    {
        "name": "Work better together",
        "short_name": "Collaboration and review",
        "description": (
            "Collaborate, co-edit, share templates, share brand identity, and review "
            "visual projects with a team."
        ),
    },
    {
        "name": "Make it move",
        "short_name": "Animation effects",
        "description": (
            "Add motion to text, images, icons, and other design elements."
        ),
    },
    {
        "name": "Apply your brand",
        "short_name": "Brand controls",
        "description": (
            "Upload and apply brand logos, fonts, and colors to keep designs "
            "consistent."
        ),
    },
    {
        "name": "Add amazing effects to any project",
        "short_name": "Effects, filters, textures, overlays",
        "description": (
            "Apply effects, filters, textures, and overlays to images or videos."
        ),
    },
    {
        "name": "Add design elements",
        "short_name": "Icons, backgrounds, and assets",
        "description": (
            "Search and add images, icons, backgrounds, videos, and mood-based "
            "curated design assets."
        ),
    },
    {
        "name": "Play with text",
        "short_name": "Adobe Fonts and text templates",
        "description": (
            "Use licensed Adobe Fonts, recommended font pairings, and text templates."
        ),
    },
    {
        "name": "Remix it",
        "short_name": "Template remixing",
        "description": "Customize premade templates, graphics, and text.",
    },
    {
        "name": "Create videos made for social",
        "short_name": "Social resizing",
        "description": (
            "Resize video and static social posts, then trim and crop in the editor."
        ),
    },
]


FIELD_ALIASES: Mapping[str, Sequence[str]] = {
    "persona_id": (
        "persona_id",
        "personaid",
        "id",
        "si_no",
        "sl_no",
        "serial",
        "test_case_id",
        "case_id",
    ),
    "persona_name": (
        "persona_name",
        "personaname",
        "persona",
        "name",
        "profile_name",
        "user_name",
        "title",
    ),
    "age": ("age", "persona_age"),
    "occupation": (
        "occupation",
        "job",
        "job_title",
        "role",
        "profession",
        "work",
        "industry",
    ),
    "technical_skill": (
        "technical_skill",
        "technicalskill",
        "tech_skill",
        "technical_proficiency",
        "digital_skill",
        "digital_literacy",
        "computer_skill",
    ),
    "prompt_style": (
        "prompt_style",
        "promptstyle",
        "communication_style",
        "instruction_style",
        "preferred_prompt_style",
        "tone",
        "writing_style",
    ),
    "ai_trust_level": (
        "ai_trust_level",
        "aitrustlevel",
        "ai_trust",
        "trust_ai",
        "trust_level",
        "ai_confidence",
        "ai_comfort",
    ),
    "accessibility": (
        "accessibility",
        "accessibility_needs",
        "accessibilityneed",
        "assistive_technology",
        "disability",
        "visual_needs",
    ),
    "locale": (
        "locale",
        "language",
        "region",
        "country",
        "market",
        "location",
    ),
    "privacy_posture": (
        "privacy_posture",
        "privacyposture",
        "privacy",
        "security_posture",
        "data_sensitivity",
        "compliance",
    ),
    "acceptance_criteria": (
        "acceptance_criteria",
        "acceptancecriteria",
        "success_criteria",
        "expected_result",
        "expected_results",
        "criteria",
        "goals",
        "goal",
    ),
    "avoid_list": (
        "avoid_list",
        "avoid",
        "avoidlist",
        "constraints",
        "do_not",
        "dont",
        "negative_prompt",
    ),
}


LOW_SKILL_SIGNALS = (
    "beginner",
    "basic",
    "low",
    "limited",
    "novice",
    "non-technical",
    "not technical",
    "new user",
)
HIGH_SKILL_SIGNALS = (
    "advanced",
    "expert",
    "designer",
    "developer",
    "technical",
    "power user",
    "high",
)
LOW_TRUST_SIGNALS = (
    "low",
    "skeptical",
    "sceptical",
    "cautious",
    "distrust",
    "manual",
    "verify",
)
HIGH_TRUST_SIGNALS = (
    "high",
    "trusting",
    "confident",
    "comfortable",
    "enthusiastic",
    "early adopter",
)
PRIVACY_SIGNALS = (
    "privacy",
    "private",
    "confidential",
    "restricted",
    "secure",
    "security",
    "compliance",
    "regulated",
    "enterprise",
    "legal",
)
ACCESSIBILITY_SIGNALS = (
    "accessibility",
    "screen reader",
    "low vision",
    "color blind",
    "colour blind",
    "dyslexia",
    "motor",
    "contrast",
    "large text",
)
SOCIAL_SIGNALS = (
    "social",
    "instagram",
    "facebook",
    "linkedin",
    "tiktok",
    "marketing",
    "campaign",
    "creator",
    "influencer",
)
COLLABORATION_SIGNALS = (
    "team",
    "review",
    "approval",
    "manager",
    "stakeholder",
    "collaboration",
    "co-edit",
    "enterprise",
)
STOCK_SIGNALS = (
    "stock",
    "photo",
    "image",
    "reference",
    "assets",
    "illustration",
    "inspiration",
)


def normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(stringify(item) for item in value if stringify(item))
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            text = stringify(item)
            if text:
                parts.append(f"{key}: {text}")
        return "; ".join(parts)
    return str(value).strip()


def flatten_record(record: Mapping[str, Any], prefix: str = "") -> Dict[str, str]:
    flattened: Dict[str, str] = {}
    for key, value in record.items():
        raw_key = f"{prefix}_{key}" if prefix else str(key)
        flattened[normalized_key(raw_key)] = stringify(value)
        if isinstance(value, Mapping):
            flattened.update(flatten_record(value, raw_key))
    return flattened


def find_field(flattened: Mapping[str, str], aliases: Sequence[str]) -> str:
    normalized_aliases = [normalized_key(alias) for alias in aliases]
    for alias in normalized_aliases:
        if flattened.get(alias):
            return flattened[alias]
    for key, value in flattened.items():
        if value and any(alias in key for alias in normalized_aliases):
            return value
    return ""


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def extract_persona_records(payload: Any) -> List[Mapping[str, Any]]:
    """Return persona-like records from common JSON export shapes."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, Mapping)]

    if not isinstance(payload, Mapping):
        raise ValueError("The persona JSON root must be an object or an array.")

    candidate_keys = (
        "personas",
        "test_cases",
        "testCases",
        "cases",
        "records",
        "items",
        "data",
        "profiles",
        "persona_background_test_cases",
    )
    for key in candidate_keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Mapping)]
        if isinstance(value, Mapping):
            return extract_persona_records(value)

    if all(isinstance(value, Mapping) for value in payload.values()):
        records = []
        for key, value in payload.items():
            enriched = dict(value)
            enriched.setdefault("persona_id", key)
            records.append(enriched)
        return records

    return [payload]


def profile_from_record(record: Mapping[str, Any], index: int) -> Dict[str, Any]:
    flattened = flatten_record(record)
    profile: Dict[str, Any] = {
        "serial": index,
        "raw": record,
        "raw_text": json.dumps(record, ensure_ascii=False, sort_keys=True),
    }
    for field_name, aliases in FIELD_ALIASES.items():
        profile[field_name] = find_field(flattened, aliases) or "Not specified"

    if profile["persona_id"] == "Not specified":
        profile["persona_id"] = f"P{index:03d}"
    if profile["persona_name"] == "Not specified":
        profile["persona_name"] = f"Persona {index:03d}"
    return profile


def has_any(text: str, signals: Iterable[str]) -> bool:
    haystack = text.lower()
    return any(signal in haystack for signal in signals)


def load_feature_catalog(path: Path) -> List[Dict[str, str]]:
    if path.exists():
        payload = load_json(path)
        if isinstance(payload, Mapping) and isinstance(payload.get("features"), list):
            return [dict(item) for item in payload["features"] if isinstance(item, Mapping)]
        if isinstance(payload, list):
            return [dict(item) for item in payload if isinstance(item, Mapping)]
        raise ValueError(f"Unsupported feature catalog structure: {path}")
    return EMBEDDED_FEATURES


def map_features(profile: Mapping[str, Any], features: Sequence[Mapping[str, str]]) -> List[Dict[str, str]]:
    feature_by_name = {feature["name"]: dict(feature) for feature in features}
    selected: MutableMapping[str, Dict[str, str]] = {}
    raw_text = str(profile["raw_text"]).lower()
    technical_skill = str(profile["technical_skill"]).lower()
    ai_trust = str(profile["ai_trust_level"]).lower()
    accessibility = str(profile["accessibility"]).lower()
    privacy = str(profile["privacy_posture"]).lower()
    occupation = str(profile["occupation"]).lower()
    criteria = str(profile["acceptance_criteria"]).lower()
    prompt_style = str(profile["prompt_style"]).lower()
    locale = str(profile["locale"]).lower()
    combined = " ".join(
        [raw_text, technical_skill, ai_trust, accessibility, privacy, occupation, criteria, prompt_style, locale]
    )

    def add(name: str, reason: str) -> None:
        if name not in feature_by_name:
            return
        if name in selected:
            existing = selected[name].setdefault("reason", "")
            if reason and reason not in existing:
                selected[name]["reason"] = f"{existing} {reason}".strip()
            return
        item = dict(feature_by_name[name])
        item["reason"] = reason
        selected[name] = item

    if has_any(ai_trust, LOW_TRUST_SIGNALS):
        add(
            "Design with AI",
            "The persona is cautious about AI, so Firefly should be used with explicit constraints, review checkpoints, and no unsupported claims.",
        )
    elif has_any(ai_trust, HIGH_TRUST_SIGNALS):
        add(
            "Design with AI",
            "The persona is comfortable with AI, so Firefly can accelerate initial Bird logo ideation from a detailed natural-language prompt.",
        )
    else:
        add(
            "Design with AI",
            "The shared Bird logo task benefits from Firefly ideation while still preserving persona-specific review instructions.",
        )

    add(
        "Make content that always stands out",
        "Logo templates provide a practical starting point for the Bird logo canvas and composition.",
    )
    add(
        "Add design elements",
        "Bird icons, simple shapes, backgrounds, and visual motifs are needed to build the logo mark.",
    )
    add(
        "Play with text",
        "The logo needs readable typography, licensed Adobe Fonts, and persona-appropriate font pairing.",
    )

    if has_any(technical_skill, LOW_SKILL_SIGNALS) or "simple" in prompt_style or "step" in prompt_style:
        add(
            "Remix it",
            "A low-friction template remix workflow reduces complexity for a persona that needs guided steps.",
        )
        add(
            "Edit images, videos and PDFs in just a few clicks",
            "Quick Actions keep resizing and background cleanup simple for a less technical workflow.",
        )

    if has_any(technical_skill, HIGH_SKILL_SIGNALS):
        add(
            "Add amazing effects to any project",
            "A higher-skill persona can tune filters, textures, and overlays for a more polished logo finish.",
        )

    if has_any(accessibility, ACCESSIBILITY_SIGNALS) or "older" in raw_text:
        add(
            "Play with text",
            "Accessibility needs require high-contrast type, larger readable letterforms, and a clear hierarchy.",
        )
        add(
            "Edit images, videos and PDFs in just a few clicks",
            "Quick resizing and cleanup support accessible contrast and legibility checks.",
        )

    if has_any(privacy, PRIVACY_SIGNALS) or has_any(combined, PRIVACY_SIGNALS):
        add(
            "Apply your brand",
            "Brand controls keep logo colors, fonts, and approved assets consistent for privacy-aware or enterprise use.",
        )
        add(
            "Work better together",
            "Review and shared brand identity controls support stakeholder approval without leaking persona assumptions.",
        )

    if has_any(occupation, SOCIAL_SIGNALS) or has_any(criteria, SOCIAL_SIGNALS):
        add(
            "Create videos made for social",
            "The Bird logo may need social post sizes and channel-ready exports.",
        )
        add(
            "Take command of social content",
            "A social or marketing persona benefits from previewing and scheduling logo launch assets.",
        )
        add(
            "Make it move",
            "Light animation can make the logo suitable for social intros or reels.",
        )

    if has_any(combined, COLLABORATION_SIGNALS):
        add(
            "Work better together",
            "The persona's team or approval context needs collaborative review and shared assets.",
        )

    if has_any(combined, STOCK_SIGNALS):
        add(
            "Get free Adobe Stock images, videos and music",
            "Licensed reference assets can guide the bird silhouette or supporting visual mood without using unapproved imagery.",
        )

    if locale != "not specified":
        add(
            "Play with text",
            f"The locale value ({profile['locale']}) should influence language, font readability, and culturally appropriate visual choices.",
        )

    return list(selected.values())


def background_recommendation(profile: Mapping[str, Any]) -> str:
    text = str(profile["raw_text"]).lower()
    if has_any(text, ACCESSIBILITY_SIGNALS):
        return "Use a high-contrast light yellow review background only if it passes accessibility contrast checks; export final logo with transparent and dark-background variants."
    if has_any(text, PRIVACY_SIGNALS):
        return "Use brand-approved neutral or yellow test backgrounds only from the approved palette; export a transparent master logo."
    if has_any(text, SOCIAL_SIGNALS):
        return "Prepare a transparent logo plus a cheerful yellow social-preview background for visibility in feeds."
    return "Use a transparent master logo and include an optional warm yellow preview background to check silhouette contrast."


def style_keywords(profile: Mapping[str, Any]) -> str:
    text = str(profile["raw_text"]).lower()
    keywords = ["clean vector", "recognizable bird silhouette", "balanced negative space"]
    if "education" in text or "teacher" in text or "student" in text:
        keywords.extend(["friendly", "approachable"])
    if "finance" in text or "legal" in text or "compliance" in text:
        keywords.extend(["trustworthy", "minimal", "formal"])
    if "marketing" in text or "creator" in text or "social" in text:
        keywords.extend(["bold", "memorable", "shareable"])
    if "health" in text or "medical" in text:
        keywords.extend(["calm", "reassuring"])
    if "luxury" in text or "premium" in text:
        keywords.extend(["elegant", "refined"])
    if has_any(text, ACCESSIBILITY_SIGNALS):
        keywords.extend(["high contrast", "simple outline"])
    return ", ".join(dict.fromkeys(keywords))


def concise_value(profile: Mapping[str, Any], key: str) -> str:
    value = str(profile.get(key, "Not specified")).strip()
    return value if value else "Not specified"


def prompt_variant(profile: Mapping[str, Any]) -> int:
    seed_text = "|".join(
        [
            concise_value(profile, "persona_id"),
            concise_value(profile, "persona_name"),
            concise_value(profile, "occupation"),
            concise_value(profile, "prompt_style"),
        ]
    )
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 4


def create_prompt(profile: Mapping[str, Any], mapped_features: Sequence[Mapping[str, str]]) -> str:
    feature_names = [feature["name"] for feature in mapped_features]
    variant = prompt_variant(profile)
    persona_label = f"{profile['persona_name']} ({profile['persona_id']})"
    keywords = style_keywords(profile)
    acceptance = concise_value(profile, "acceptance_criteria")
    avoid = concise_value(profile, "avoid_list")
    trust = concise_value(profile, "ai_trust_level")
    skill = concise_value(profile, "technical_skill")
    style = concise_value(profile, "prompt_style")
    accessibility = concise_value(profile, "accessibility")
    privacy = concise_value(profile, "privacy_posture")
    locale = concise_value(profile, "locale")
    occupation = concise_value(profile, "occupation")

    openings = [
        "Work as an Adobe Express design copilot inside ChatGPT.",
        "Guide Adobe Express like a careful logo production assistant.",
        "Use Adobe Express as a collaborative brand studio for this persona.",
        "Create the logo through a persona-specific Adobe Express workflow.",
    ]
    workflow_labels = [
        "Workflow checkpoints",
        "Build sequence",
        "Persona-aligned production steps",
        "Logo creation route",
    ]
    closing_labels = [
        "Final validation",
        "Acceptance pass",
        "Quality gate",
        "Before export",
    ]

    if has_any(str(profile["raw_text"]), LOW_SKILL_SIGNALS):
        guidance = "Keep instructions plain, sequential, and confirmation-driven."
    elif has_any(str(profile["raw_text"]), HIGH_SKILL_SIGNALS):
        guidance = "Allow advanced design control, concise rationale, and editable layer choices."
    else:
        guidance = "Balance guided steps with enough creative rationale to support confident edits."

    if has_any(str(profile["ai_trust_level"]), LOW_TRUST_SIGNALS):
        ai_rule = "Treat AI output as a draft; show the feature used, the reason for it, and a manual review option."
    elif has_any(str(profile["ai_trust_level"]), HIGH_TRUST_SIGNALS):
        ai_rule = "Use AI confidently for ideation, then refine the strongest direction in Adobe Express."
    else:
        ai_rule = "Use AI for options, but ask for approval before final export."

    feature_line = "; ".join(feature_names)
    mapped_reason_lines = "\n".join(
        f"- {feature['name']}: {feature.get('reason', feature.get('description', '')).strip()}"
        for feature in mapped_features
    )

    if variant == 0:
        steps = [
            f"Start with '{feature_names[1] if len(feature_names) > 1 else feature_names[0]}' to choose a logo canvas or remixable logo template.",
            f"Use 'Design with AI' to generate 3 Bird logo concepts described as: {keywords}.",
            "Use 'Add design elements' to refine the bird mark with simple wings, beak, and negative-space geometry.",
            "Use 'Play with text' for the brand name or placeholder wordmark, selecting fonts that match the persona's tone.",
            f"Apply this background rule: {background_recommendation(profile)}",
        ]
    elif variant == 1:
        steps = [
            "Create a compact logo brief from the persona profile before touching the canvas.",
            f"In 'Design with AI', request a Bird logo with {keywords}; reject cluttered or photorealistic outputs.",
            "Use 'Remix it' or templates only when they speed up the persona's preferred workflow.",
            "Use 'Apply your brand' if brand, privacy, or enterprise controls are relevant to this persona.",
            "Export transparent PNG/SVG-style artwork plus a yellow-background preview if useful for contrast review.",
        ]
    elif variant == 2:
        steps = [
            "Open an Adobe Express logo template and define the mark, typography, and color palette separately.",
            "Generate the bird silhouette with Firefly through 'Design with AI', then simplify it for logo scalability.",
            "Search 'Add design elements' for icons or geometric accents, using only assets that fit the persona's trust and privacy posture.",
            "Use 'Add amazing effects to any project' sparingly for polish; avoid effects that reduce recognizability.",
            "Use collaboration or review features when the persona expects approval before export.",
        ]
    else:
        steps = [
            f"Translate the persona's occupation ({occupation}) into a visual Bird logo mood before generating assets.",
            "Use Adobe Express templates for the first layout, then customize rather than accepting a generic bird mark.",
            "Use 'Design with AI' for visual exploration and 'Add design elements' for controlled icon cleanup.",
            f"Use 'Play with text' to localize typography for {locale} and preserve readable spacing.",
            "Return export notes covering transparent, light, dark, and optional yellow-background versions.",
        ]

    steps_text = "\n".join(f"{idx}. {step}" for idx, step in enumerate(steps, start=1))

    return (
        f"{openings[variant]}\n\n"
        f"Persona isolation: Use only this persona profile for the Bird logo task: {persona_label}. "
        "Do not borrow preferences, risks, or acceptance criteria from any other persona.\n\n"
        "Persona behavior to honor:\n"
        f"- Occupation/context: {occupation}\n"
        f"- Age: {concise_value(profile, 'age')}\n"
        f"- Technical skill: {skill}\n"
        f"- Prompt/communication style: {style}\n"
        f"- AI trust level: {trust}\n"
        f"- Accessibility needs: {accessibility}\n"
        f"- Locale: {locale}\n"
        f"- Privacy posture: {privacy}\n"
        f"- Avoid list: {avoid}\n\n"
        f"Adobe Express features to use by name: {feature_line}.\n"
        "Behavior-driven feature mapping:\n"
        f"{mapped_reason_lines}\n\n"
        f"{workflow_labels[variant]}:\n"
        f"{steps_text}\n\n"
        "Communication rules:\n"
        f"- {guidance}\n"
        f"- {ai_rule}\n"
        "- Keep the Bird logo unique, vector-like, legible at small sizes, and free of copyrighted brand references.\n"
        "- Ask for confirmation only at persona-critical risk points such as privacy, accessibility, or brand approval.\n\n"
        f"{closing_labels[variant]}:\n"
        f"- Acceptance criteria to satisfy: {acceptance}\n"
        "- Provide the final logo concept, palette, font choice, feature usage summary, and export checklist."
    )


def build_results(records: Sequence[Mapping[str, Any]], features: Sequence[Mapping[str, str]]) -> List[Dict[str, Any]]:
    results = []
    seen_prompts: Dict[str, int] = {}
    for index, record in enumerate(records, start=1):
        profile = profile_from_record(record, index)
        mapped = map_features(profile, features)
        prompt = create_prompt(profile, mapped)
        if prompt in seen_prompts:
            prompt += f"\n\nUniqueness marker: Persona serial {index} has its own source record and must be tested separately."
        seen_prompts[prompt] = index
        results.append(
            {
                "si_no": index,
                "persona_id": profile["persona_id"],
                "persona_name": profile["persona_name"],
                "summary": {
                    "age": profile["age"],
                    "occupation": profile["occupation"],
                    "technical_skill": profile["technical_skill"],
                    "prompt_style": profile["prompt_style"],
                    "ai_trust_level": profile["ai_trust_level"],
                    "accessibility": profile["accessibility"],
                    "locale": profile["locale"],
                    "privacy_posture": profile["privacy_posture"],
                    "acceptance_criteria": profile["acceptance_criteria"],
                    "avoid_list": profile["avoid_list"],
                },
                "mapped_features": mapped,
                "background_recommendation": background_recommendation(profile),
                "prompt": prompt,
            }
        )
    return results


def html_escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_html(results: Sequence[Mapping[str, Any]], source_file: Path) -> str:
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    cards = []
    rows = []
    for item in results:
        summary = item["summary"]
        feature_chips = "".join(
            f"<span class=\"chip\">{html_escape(feature['name'])}</span>"
            for feature in item["mapped_features"]
        )
        feature_reasons = "".join(
            "<li><strong>{}</strong>: {}</li>".format(
                html_escape(feature["name"]),
                html_escape(feature.get("reason", feature.get("description", ""))),
            )
            for feature in item["mapped_features"]
        )
        search_text = html_escape(
            " ".join(
                [
                    str(item["persona_id"]),
                    str(item["persona_name"]),
                    " ".join(str(value) for value in summary.values()),
                    item["prompt"],
                ]
            ).lower()
        )
        rows.append(
            "<tr>"
            f"<td>{item['si_no']}</td>"
            f"<td>{html_escape(item['persona_id'])}</td>"
            f"<td>{html_escape(item['persona_name'])}</td>"
            f"<td>{html_escape(summary['occupation'])}</td>"
            f"<td>{html_escape(summary['technical_skill'])}</td>"
            f"<td>{html_escape(summary['ai_trust_level'])}</td>"
            f"<td>{len(item['mapped_features'])}</td>"
            "</tr>"
        )
        cards.append(
            f"""
            <article class="card" data-search="{search_text}">
              <div class="card-header">
                <div>
                  <p class="eyebrow">SI.No {item['si_no']} - {html_escape(item['persona_id'])}</p>
                  <h2>{html_escape(item['persona_name'])}</h2>
                </div>
                <button class="copy" data-target="prompt-{item['si_no']}">Copy prompt</button>
              </div>
              <div class="summary-grid">
                <p><span>Age</span>{html_escape(summary['age'])}</p>
                <p><span>Occupation</span>{html_escape(summary['occupation'])}</p>
                <p><span>Technical skill</span>{html_escape(summary['technical_skill'])}</p>
                <p><span>Prompt style</span>{html_escape(summary['prompt_style'])}</p>
                <p><span>AI trust</span>{html_escape(summary['ai_trust_level'])}</p>
                <p><span>Accessibility</span>{html_escape(summary['accessibility'])}</p>
                <p><span>Locale</span>{html_escape(summary['locale'])}</p>
                <p><span>Privacy</span>{html_escape(summary['privacy_posture'])}</p>
              </div>
              <section>
                <h3>Mapped Adobe Express features</h3>
                <div class="chips">{feature_chips}</div>
                <ul>{feature_reasons}</ul>
              </section>
              <section class="recommendation">
                <h3>Background recommendation</h3>
                <p>{html_escape(item['background_recommendation'])}</p>
              </section>
              <section>
                <h3>Unique Bird logo prompt</h3>
                <pre id="prompt-{item['si_no']}">{html_escape(item['prompt'])}</pre>
              </section>
            </article>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Adobe Express Bird Logo Persona Test Cases</title>
  <style>
    :root {{
      --ink: #172033;
      --muted: #5f6b7a;
      --brand: #6c3df4;
      --brand-2: #ff6f61;
      --sun: #ffd84d;
      --mint: #2ec4b6;
      --paper: #ffffff;
      --bg: #f6f2ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, Arial, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(255,216,77,.45), transparent 34rem),
        radial-gradient(circle at top right, rgba(108,61,244,.23), transparent 32rem),
        linear-gradient(135deg, #fff8d8 0%, var(--bg) 44%, #e9fbf8 100%);
    }}
    header {{
      padding: 3rem clamp(1rem, 4vw, 4rem);
      color: white;
      background: linear-gradient(135deg, var(--brand), #1b85ff 55%, var(--mint));
    }}
    header h1 {{ margin: 0 0 .75rem; font-size: clamp(2rem, 5vw, 4rem); }}
    header p {{ max-width: 70rem; margin: .35rem 0; font-size: 1.05rem; }}
    main {{ padding: 2rem clamp(1rem, 4vw, 4rem) 4rem; }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 1;
      display: flex;
      gap: 1rem;
      align-items: center;
      margin: -1rem 0 1.5rem;
      padding: 1rem;
      background: rgba(255,255,255,.84);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(108,61,244,.18);
      border-radius: 1rem;
      box-shadow: 0 14px 38px rgba(23,32,51,.08);
    }}
    input[type="search"] {{
      width: 100%;
      padding: .9rem 1rem;
      border: 2px solid rgba(108,61,244,.22);
      border-radius: .85rem;
      font-size: 1rem;
    }}
    .summary-table, .card {{
      background: rgba(255,255,255,.94);
      border: 1px solid rgba(23,32,51,.08);
      border-radius: 1.2rem;
      box-shadow: 0 18px 48px rgba(23,32,51,.10);
    }}
    .summary-table {{ overflow: auto; margin-bottom: 1.5rem; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 760px; }}
    th, td {{ padding: .8rem 1rem; text-align: left; border-bottom: 1px solid #eceff5; }}
    th {{ background: #fff3a6; }}
    .cards {{ display: grid; gap: 1.25rem; }}
    .card {{ padding: clamp(1rem, 3vw, 2rem); }}
    .card-header {{ display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; }}
    .eyebrow {{ color: var(--brand); font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }}
    h2 {{ margin-top: 0; font-size: clamp(1.5rem, 3vw, 2.25rem); }}
    h3 {{ margin-bottom: .5rem; color: #28314a; }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: .75rem;
      margin: 1rem 0;
    }}
    .summary-grid p {{
      margin: 0;
      padding: .85rem;
      border-radius: .8rem;
      background: linear-gradient(135deg, #f7f9ff, #fff);
      border: 1px solid #edf0f7;
    }}
    .summary-grid span {{ display: block; color: var(--muted); font-size: .78rem; text-transform: uppercase; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: .5rem; }}
    .chip {{
      display: inline-flex;
      padding: .45rem .7rem;
      border-radius: 999px;
      background: #efe9ff;
      color: #4f2acb;
      font-weight: 700;
      font-size: .88rem;
    }}
    .recommendation {{
      padding: 1rem;
      border-radius: 1rem;
      background: linear-gradient(135deg, #fff3a6, #fff9d9);
      border: 1px solid #f0d760;
    }}
    pre {{
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      padding: 1rem;
      border-radius: 1rem;
      background: #121826;
      color: #f7fbff;
      line-height: 1.5;
    }}
    button.copy {{
      cursor: pointer;
      border: 0;
      border-radius: 999px;
      padding: .75rem 1rem;
      color: white;
      background: linear-gradient(135deg, var(--brand-2), var(--brand));
      font-weight: 800;
    }}
    .hidden {{ display: none; }}
  </style>
</head>
<body>
  <header>
    <p class="eyebrow">Adobe Express Enterprise + ChatGPT Persona Tests</p>
    <h1>Bird Logo Prompt Showcase</h1>
    <p>Generated from <strong>{html_escape(source_file)}</strong> on {generated}.</p>
    <p>Adobe Express feature source: <a href="{FEATURE_SOURCE_URL}" style="color:white">{FEATURE_SOURCE_URL}</a></p>
  </header>
  <main>
    <div class="toolbar">
      <input id="search" type="search" placeholder="Search personas, features, risks, locales, or prompt text">
      <strong id="count">{len(results)} personas</strong>
    </div>
    <section class="summary-table">
      <table>
        <thead>
          <tr><th>SI.No</th><th>ID</th><th>Persona</th><th>Occupation</th><th>Technical skill</th><th>AI trust</th><th>Feature count</th></tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>
    <section class="cards">{''.join(cards)}</section>
  </main>
  <script>
    const search = document.querySelector('#search');
    const count = document.querySelector('#count');
    const cards = [...document.querySelectorAll('.card')];
    search.addEventListener('input', () => {{
      const query = search.value.trim().toLowerCase();
      let visible = 0;
      cards.forEach(card => {{
        const match = !query || card.dataset.search.includes(query);
        card.classList.toggle('hidden', !match);
        if (match) visible += 1;
      }});
      count.textContent = `${{visible}} personas`;
    }});
    document.querySelectorAll('.copy').forEach(button => {{
      button.addEventListener('click', async () => {{
        const target = document.getElementById(button.dataset.target);
        await navigator.clipboard.writeText(target.innerText);
        const original = button.innerText;
        button.innerText = 'Copied';
        setTimeout(() => button.innerText = original, 1200);
      }});
    }});
  </script>
</body>
</html>
"""


def w_text(text: Any) -> str:
    return xml_escape(str(text))


def paragraph(text: Any = "", bold: bool = False) -> str:
    safe = w_text(text).replace("\n", "</w:t></w:r></w:p><w:p><w:r><w:t>")
    bold_xml = "<w:b/>" if bold else ""
    return f"<w:p><w:r><w:rPr>{bold_xml}</w:rPr><w:t>{safe}</w:t></w:r></w:p>"


def table(rows: Sequence[Sequence[Any]]) -> str:
    row_xml = []
    for row_index, row in enumerate(rows):
        cells = []
        for cell in row:
            cells.append(
                "<w:tc><w:tcPr><w:tcW w:w=\"2400\" w:type=\"dxa\"/></w:tcPr>"
                f"{paragraph(cell, bold=row_index == 0)}</w:tc>"
            )
        row_xml.append(f"<w:tr>{''.join(cells)}</w:tr>")
    return (
        "<w:tbl><w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/>"
        "<w:tblBorders><w:top w:val=\"single\" w:sz=\"4\"/>"
        "<w:left w:val=\"single\" w:sz=\"4\"/><w:bottom w:val=\"single\" w:sz=\"4\"/>"
        "<w:right w:val=\"single\" w:sz=\"4\"/><w:insideH w:val=\"single\" w:sz=\"4\"/>"
        "<w:insideV w:val=\"single\" w:sz=\"4\"/></w:tblBorders></w:tblPr>"
        f"{''.join(row_xml)}</w:tbl>"
    )


def render_docx(results: Sequence[Mapping[str, Any]], output_path: Path, source_file: Path) -> None:
    summary_rows: List[List[Any]] = [["SI.No", "Persona ID", "Persona", "Occupation", "AI trust", "Mapped features"]]
    body_parts = [
        paragraph("Adobe Express Bird Logo Persona Test Cases", bold=True),
        paragraph(f"Source persona file: {source_file}"),
        paragraph(f"Adobe Express feature source: {FEATURE_SOURCE_URL}"),
        paragraph(f"Generated: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"),
        paragraph("Summary Table", bold=True),
    ]
    for item in results:
        summary = item["summary"]
        summary_rows.append(
            [
                item["si_no"],
                item["persona_id"],
                item["persona_name"],
                summary["occupation"],
                summary["ai_trust_level"],
                ", ".join(feature["name"] for feature in item["mapped_features"]),
            ]
        )
    body_parts.append(table(summary_rows))

    for item in results:
        summary = item["summary"]
        body_parts.extend(
            [
                paragraph(""),
                paragraph(f"Test Case {item['si_no']}: {item['persona_name']}", bold=True),
                paragraph(f"Persona ID: {item['persona_id']}"),
                paragraph(f"Age: {summary['age']}"),
                paragraph(f"Occupation: {summary['occupation']}"),
                paragraph(f"Technical skill: {summary['technical_skill']}"),
                paragraph(f"Prompt style: {summary['prompt_style']}"),
                paragraph(f"AI trust level: {summary['ai_trust_level']}"),
                paragraph(f"Accessibility: {summary['accessibility']}"),
                paragraph(f"Locale: {summary['locale']}"),
                paragraph(f"Privacy posture: {summary['privacy_posture']}"),
                paragraph(f"Acceptance criteria: {summary['acceptance_criteria']}"),
                paragraph(f"Background recommendation: {item['background_recommendation']}"),
                paragraph("Mapped Features", bold=True),
            ]
        )
        for feature in item["mapped_features"]:
            body_parts.append(paragraph(f"- {feature['name']}: {feature.get('reason', '')}"))
        body_parts.extend([paragraph("Unique Prompt", bold=True), paragraph(item["prompt"])])

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body_parts)}"
        '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>'
        "</w:sectPr></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/document.xml", document_xml)


def write_outputs(results: Sequence[Mapping[str, Any]], output_dir: Path, source_file: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "Persona_Test_Cases_Bird_Logo_Demo.html"
    docx_path = output_dir / "Persona Test Cases Bird Logo.docx"
    json_path = output_dir / "bird_logo_persona_prompts.json"

    html_path.write_text(render_html(results, source_file), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "task": "Create a Bird logo",
                "source_persona_file": str(source_file),
                "feature_source_url": FEATURE_SOURCE_URL,
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "personas": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    render_docx(results, docx_path, source_file)
    return {"html": str(html_path), "docx": str(docx_path), "json": str(json_path)}


def resolve_input_path(argument: str | None) -> Path:
    candidates: List[Path] = []
    if argument:
        candidates.append(Path(argument))
    candidates.extend([Path(LOCAL_INPUT_NAME), Path(DEFAULT_WINDOWS_INPUT)])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    checked = "\n  - ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(
        "Persona JSON not found. Place the file in the workspace as "
        f"{LOCAL_INPUT_NAME} or pass --input.\nChecked:\n  - {checked}"
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Adobe Express Bird logo prompts from persona JSON."
    )
    parser.add_argument(
        "--input",
        help=(
            "Path to persona_background_test_cases.json. If omitted, the script "
            "checks the workspace file name and the original Windows Desktop path."
        ),
    )
    parser.add_argument(
        "--features",
        default=str(Path(__file__).resolve().parents[1] / "data" / "adobe_express_features.json"),
        help="Path to Adobe Express feature catalog JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default="generated",
        help="Directory for HTML, DOCX, and JSON deliverables.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    try:
        input_path = resolve_input_path(args.input)
        feature_catalog = load_feature_catalog(Path(args.features))
        payload = load_json(input_path)
        records = extract_persona_records(payload)
        if not records:
            raise ValueError("No persona records were found in the input JSON.")
        results = build_results(records, feature_catalog)
        outputs = write_outputs(results, Path(args.output_dir), input_path)
    except Exception as exc:  # pragma: no cover - command-line UX path
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {len(results)} persona prompt set(s):")
    for label, path in outputs.items():
        print(f"  {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
