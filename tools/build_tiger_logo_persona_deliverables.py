#!/usr/bin/env python3
"""Build Adobe Express persona prompt deliverables for a tiger logo task.

The cloud environment cannot read a Windows Desktop path directly. This script
therefore supports two modes:

1. If a local persona HTML file is supplied with --persona-html and contains a
   simple table, the table is parsed into persona rows.
2. Otherwise, a clearly labelled fallback persona set is used so reviewers can
   inspect the requested Adobe Express feature mapping and prompt format.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape


REQUESTED_SOURCE = (
    r"C:\Users\subash.b\OneDrive - Qualitest Group\Desktop\PERSONA FILE"
    r"\persona_behaviors.html"
)


@dataclass(frozen=True)
class Feature:
    name: str
    website_label: str
    description: str


FEATURES: dict[str, Feature] = {
    "quick_actions": Feature(
        "Quick Actions",
        "Edit images, videos and PDFs in just a few clicks",
        "Resize, convert, remove backgrounds, and apply fast one-click edits.",
    ),
    "design_ai": Feature(
        "Design with AI",
        "Design with AI",
        "Use Adobe Firefly text-to-image and Generate Text Effect capabilities.",
    ),
    "templates": Feature(
        "Templates and Remix",
        "Make content that always stands out / Remix it",
        "Start from logo templates and customise them for the persona workflow.",
    ),
    "stock": Feature(
        "Adobe Stock Assets",
        "Get free Adobe Stock images, videos and music",
        "Use licensed, royalty-free visual assets when a persona needs safe sourcing.",
    ),
    "brand": Feature(
        "Apply your brand",
        "Apply your brand",
        "Upload and apply approved logos, fonts, and colours for brand consistency.",
    ),
    "collaboration": Feature(
        "Work better together",
        "Work better together",
        "Invite reviewers, co-edit, share templates, and keep assets aligned.",
    ),
    "effects": Feature(
        "Effects, filters, textures and overlays",
        "Add amazing effects to any project",
        "Apply controlled visual treatments to the tiger image and background.",
    ),
    "elements": Feature(
        "Design elements",
        "Add design elements",
        "Search icons, backgrounds, shapes, badges, and other supporting assets.",
    ),
    "fonts": Feature(
        "Adobe Fonts",
        "Play with text",
        "Choose readable licensed fonts or recommended font pairings.",
    ),
    "animation": Feature(
        "Animated effects",
        "Make it move",
        "Create an optional animated logo variant for social content.",
    ),
    "resize": Feature(
        "Resize for social content",
        "Create videos made for social",
        "Export logo variants for profile, story, presentation, and post sizes.",
    ),
    "scheduler": Feature(
        "Content Scheduler",
        "Take command of social content",
        "Plan, preview, and schedule the finished logo announcement.",
    ),
    "qr": Feature(
        "QR code",
        "QR code",
        "Create a QR code variant for print, menus, events, or launch collateral.",
    ),
    "pdf": Feature(
        "PDF tools",
        "Learn the ABCs of PDFs",
        "Create a PDF handoff, approval sheet, or printable brand guide.",
    ),
}


def prompt(text: str) -> str:
    return re.sub(r"\n[ \t]+", "\n", text.strip())


FALLBACK_PERSONAS: list[dict[str, str | list[str]]] = [
    {
        "name": "Maya Srinivasan",
        "age": "29",
        "occupation": "Social media manager",
        "technical_skill": "Intermediate",
        "prompt_style": "Concise bullet points with campaign language",
        "ai_trust": "High",
        "accessibility": "Prefers mobile-friendly review",
        "locale": "en-IN",
        "privacy_posture": "Medium: avoids customer names and campaign secrets",
        "acceptance_criteria": "1:1 tiger logo, brand colours, reusable social exports",
        "behaviour": (
            "Fast-moving campaign creator who trusts AI for first drafts, wants "
            "brand-safe polish, and needs copyable social variants."
        ),
        "avoid_list": "No violent tiger, no competitor colours, no private launch data",
        "features": ["design_ai", "brand", "fonts", "resize", "scheduler"],
        "yellow_recommendation": (
            "Use a warm marigold yellow background with black stripes and white "
            "highlights so the tiger reads clearly in a social avatar."
        ),
        "full_prompt": prompt(
            """
            Create a 1:1 Adobe Express logo with a tiger image for a bold launch campaign.
            Persona rules: respond in short bullets, give quick choices, and keep the workflow social-media ready. Do not ask for customer names or confidential launch details.

            Workflow:
            1. Use Design with AI to generate a clean vector-style tiger head, confident but non-violent.
            2. Apply your brand using approved orange, black, white, and marigold yellow; avoid competitor palettes.
            3. Use Adobe Fonts to add a short optional wordmark with a heavy geometric sans font.
            4. Resize for social content into profile, square post, and story-safe variants.
            5. Prepare a Content Scheduler note for the logo reveal post.

            Acceptance checks: tiger is centred, yellow background is visible, the design works at small avatar size, and all elements remain editable.
            """
        ),
    },
    {
        "name": "David Chen",
        "age": "52",
        "occupation": "Enterprise procurement director",
        "technical_skill": "Low",
        "prompt_style": "Formal step-by-step instructions",
        "ai_trust": "Low",
        "accessibility": "Deuteranopia; avoid red-green dependent contrast",
        "locale": "en-US",
        "privacy_posture": "Strict: no confidential vendor, pricing, or contract data",
        "acceptance_criteria": "Auditable logo workflow, licensed assets, colour-safe review",
        "behaviour": (
            "Risk-aware business approver who wants explicit steps, licensing clarity, "
            "and minimal AI ambiguity."
        ),
        "avoid_list": "No unlicensed imagery, no red-green status coding, no vendor names",
        "features": ["templates", "stock", "quick_actions", "brand", "collaboration"],
        "yellow_recommendation": (
            "Choose a muted enterprise gold-yellow background and verify contrast in "
            "grayscale so the tiger outline is not colour-dependent."
        ),
        "full_prompt": prompt(
            """
            Please create a tiger image logo in Adobe Express using an auditable enterprise workflow.
            Persona rules: use numbered instructions, explain why each step is safe, and avoid confidential vendor, contract, or pricing details.

            Steps:
            1. Start from Templates and Remix only if the template licence is suitable for enterprise use.
            2. If an image asset is needed, use Adobe Stock Assets and confirm it is royalty-free for this context.
            3. Use Quick Actions to remove any unwanted background from the tiger image and keep the logo simple.
            4. Apply your brand with approved black, white, and muted gold-yellow colours; do not use red-green contrast as the only signal.
            5. Use Work better together to send the draft to procurement and brand reviewers before export.

            Final check: provide a short approval note listing source, licence-safe asset choice, colour contrast, and export size.
            """
        ),
    },
    {
        "name": "Sofia Martinez",
        "age": "34",
        "occupation": "Senior visual designer",
        "technical_skill": "Expert",
        "prompt_style": "Visual direction with precise design terminology",
        "ai_trust": "Medium",
        "accessibility": "No stated accessibility need",
        "locale": "es-MX / en-US",
        "privacy_posture": "IP cautious: no copying famous mascot styles",
        "acceptance_criteria": "Editable layered logo, premium composition, no derivative mascot",
        "behaviour": (
            "Experienced designer who uses AI as a concept partner, then expects "
            "manual control over composition, hierarchy, and finishing."
        ),
        "avoid_list": "No sports-team mascot imitation, no flattened final-only artwork",
        "features": ["design_ai", "elements", "effects", "fonts", "brand"],
        "yellow_recommendation": (
            "Use a saturated golden-yellow field with subtle paper grain, but keep "
            "the tiger head edge clean for vector-like scalability."
        ),
        "full_prompt": prompt(
            """
            Generate an Adobe Express tiger image logo concept with a premium editorial feel.
            Persona rules: give visual rationale, keep the file editable, and avoid copying any existing mascot or sports logo.

            Creative direction:
            1. Use Design with AI for three original tiger head concepts: geometric badge, minimal monoline, and bold negative-space mark.
            2. Add design elements such as a circular badge, angular stripe accents, and a controlled golden-yellow background plane.
            3. Apply Effects, filters, textures and overlays lightly so the mark feels crafted without becoming raster-heavy.
            4. Use Adobe Fonts for one refined wordmark option and one no-text icon option.
            5. Apply your brand only after the strongest composition is selected.

            Acceptance checks: no derivative mascot cues, editable layers are named logically, yellow background improves contrast, and the logo still works in one colour.
            """
        ),
    },
    {
        "name": "Aisha Khan",
        "age": "41",
        "occupation": "Nonprofit communications lead",
        "technical_skill": "Beginner",
        "prompt_style": "Warm, guided, plain-language instructions",
        "ai_trust": "Medium",
        "accessibility": "Dyslexia; prefers short lines and readable type",
        "locale": "en-GB",
        "privacy_posture": "Cautious: avoids beneficiary or donor details",
        "acceptance_criteria": "Friendly tiger logo, readable text, accessible contrast",
        "behaviour": (
            "Mission-led communicator who needs a calm, readable workflow and "
            "assurance that sensitive community data is not used."
        ),
        "avoid_list": "No donor names, no dense text, no aggressive tiger expression",
        "features": ["templates", "design_ai", "fonts", "quick_actions", "pdf"],
        "yellow_recommendation": (
            "Use a soft sunflower yellow background with a dark tiger outline and "
            "large spacing around any text for easier reading."
        ),
        "full_prompt": prompt(
            """
            Help me make a friendly tiger image logo in Adobe Express for a community project.
            Persona rules: keep instructions simple, use short lines, and do not include donor, beneficiary, or location-sensitive information.

            Please do this:
            1. Pick a simple logo layout from Templates and Remix.
            2. Use Design with AI to make a kind-looking tiger face, not an aggressive mascot.
            3. Use Quick Actions if the tiger needs background cleanup.
            4. Use Adobe Fonts with a highly readable font and generous spacing.
            5. Create a PDF tools handoff page that shows the final logo, colours, and one-line usage note.

            Check before finishing: the yellow background is soft, the text is easy to read, the logo has strong dark-light contrast, and no private community data appears.
            """
        ),
    },
    {
        "name": "Noah Williams",
        "age": "22",
        "occupation": "Student entrepreneur",
        "technical_skill": "Beginner",
        "prompt_style": "Casual, experimental, option-driven",
        "ai_trust": "High",
        "accessibility": "ADHD; prefers quick previews and visible checkpoints",
        "locale": "en-US",
        "privacy_posture": "Open for public brand ideas, but no personal phone/email",
        "acceptance_criteria": "Energetic tiger logo, startup-ready, fast comparison options",
        "behaviour": (
            "Energetic founder who wants rapid AI exploration, visual comparisons, "
            "and a logo that feels modern without many manual steps."
        ),
        "avoid_list": "No personal contact details, no overcomplicated instructions",
        "features": ["design_ai", "templates", "effects", "elements", "resize"],
        "yellow_recommendation": (
            "Use an electric yellow background with black tiger stripes for a high-energy "
            "startup look, then test it on light and dark mockups."
        ),
        "full_prompt": prompt(
            """
            Make me a punchy tiger image logo in Adobe Express for a new startup.
            Persona rules: keep it casual, show fast options, and avoid using my phone number, email, or school details.

            Quick build:
            1. Use Design with AI to create four tiger logo directions: esports, clean startup, streetwear badge, and minimal app icon.
            2. Drop the best two into Templates and Remix so I can compare them side by side.
            3. Add design elements like lightning shapes, badge rings, or stripe patterns only if they make the tiger easier to recognise.
            4. Use Effects, filters, textures and overlays for a bold glow or grain version.
            5. Resize for social content as app icon, website header mark, and square launch post.

            Final checkpoint: choose the strongest yellow-background version, keep the tiger readable at tiny size, and list what to tweak next.
            """
        ),
    },
    {
        "name": "Priya Raman",
        "age": "38",
        "occupation": "Brand compliance manager",
        "technical_skill": "Advanced",
        "prompt_style": "Policy-driven with pass/fail criteria",
        "ai_trust": "Low",
        "accessibility": "Screen-reader-aware review notes",
        "locale": "en-IN",
        "privacy_posture": "Strict: brand assets and unreleased slogans are confidential",
        "acceptance_criteria": "Brand-kit compliant, documented approvals, no policy drift",
        "behaviour": (
            "Governance-focused reviewer who accepts AI output only when brand controls, "
            "approvals, and accessibility notes are explicit."
        ),
        "avoid_list": "No unreleased slogan, no off-palette colours, no undocumented AI asset",
        "features": ["brand", "collaboration", "pdf", "fonts", "stock"],
        "yellow_recommendation": (
            "Use only the approved brand yellow token; if unavailable, pause and request "
            "brand approval instead of approximating the shade."
        ),
        "full_prompt": prompt(
            """
            Create a brand-compliant tiger image logo in Adobe Express Enterprise.
            Persona rules: use pass/fail language, protect unreleased brand assets, and document every source or AI-generated element.

            Required controls:
            1. Apply your brand first; use only approved logo lockups, fonts, and the approved yellow colour token.
            2. Use Adobe Stock Assets only when licensing is clear, or mark the tiger as AI-generated through Design with AI for review.
            3. Use Adobe Fonts only from the approved brand font list.
            4. Use Work better together to route the logo to brand, legal, and accessibility reviewers.
            5. Use PDF tools to create a one-page compliance record with alt text, source notes, and export versions.

            Pass criteria: no off-brand colours, no confidential slogan text, accessible contrast on yellow, and documented reviewer approval before release.
            """
        ),
    },
    {
        "name": "Liam O'Connor",
        "age": "45",
        "occupation": "Sales enablement lead",
        "technical_skill": "Intermediate",
        "prompt_style": "Outcome-focused and presentation-ready",
        "ai_trust": "Medium",
        "accessibility": "Low vision; needs large preview and strong contrast",
        "locale": "en-IE",
        "privacy_posture": "Confidential: no customer pipeline or deal names",
        "acceptance_criteria": "Readable in slides, high contrast, exportable for decks",
        "behaviour": (
            "Practical business user who needs a logo that works in presentations and "
            "can be approved without revealing customer opportunities."
        ),
        "avoid_list": "No customer logos, no pipeline names, no tiny low-contrast text",
        "features": ["quick_actions", "brand", "fonts", "resize", "pdf"],
        "yellow_recommendation": (
            "Use a high-contrast yellow background with a thick black tiger silhouette "
            "so the mark stays visible from the back of a room."
        ),
        "full_prompt": prompt(
            """
            Build a presentation-ready tiger image logo in Adobe Express for a sales enablement theme.
            Persona rules: focus on business outcomes, use large-preview checks, and do not include customer names, pipeline labels, or deal details.

            Workflow:
            1. Use Quick Actions to clean up the tiger image and remove clutter.
            2. Apply your brand for the approved yellow, black, and white palette.
            3. Use Adobe Fonts for a large, bold wordmark that remains readable on slides.
            4. Resize for social content and presentation use: 1:1 icon, 16:9 title slide, and transparent PNG.
            5. Use PDF tools to export a one-page logo sheet for sales teams.

            Done means: the tiger is clear at slide distance, the yellow background passes contrast review, and no customer information appears anywhere.
            """
        ),
    },
    {
        "name": "Hana Tanaka",
        "age": "31",
        "occupation": "Independent cafe owner",
        "technical_skill": "Beginner",
        "prompt_style": "Polite, compact, and practical",
        "ai_trust": "Medium",
        "accessibility": "Prefers minimal steps due to limited design time",
        "locale": "ja-JP / en",
        "privacy_posture": "Medium: no staff personal details or private supplier info",
        "acceptance_criteria": "Warm cafe logo, print-friendly, QR variant for menu",
        "behaviour": (
            "Small-business owner who needs an approachable tiger logo that can work "
            "on signs, menu cards, and social posts with limited editing time."
        ),
        "avoid_list": "No staff names, no supplier details, no scary tiger face",
        "features": ["templates", "elements", "fonts", "qr", "quick_actions"],
        "yellow_recommendation": (
            "Use a creamy honey-yellow background, like cafe lighting, and pair it "
            "with softened tiger stripes for a welcoming tone."
        ),
        "full_prompt": prompt(
            """
            Please make a warm tiger image logo in Adobe Express for a neighbourhood cafe.
            Persona rules: keep the steps short, practical, and polite. Do not include staff names or supplier information.

            Simple workflow:
            1. Start with Templates and Remix for a cafe-friendly badge logo.
            2. Add design elements such as a soft circle, small leaf, cup outline, or gentle stripe pattern.
            3. Use Adobe Fonts for a friendly rounded wordmark.
            4. Use Quick Actions to clean the tiger image if needed.
            5. Add a QR code version for a menu or loyalty card.

            Please finish with a honey-yellow background recommendation, a print-safe version, and a square social profile version.
            """
        ),
    },
    {
        "name": "Grace Okafor",
        "age": "27",
        "occupation": "Video-first content creator",
        "technical_skill": "Advanced",
        "prompt_style": "Energetic, trend-aware, direct",
        "ai_trust": "High",
        "accessibility": "Needs captions or text alternatives for motion concepts",
        "locale": "en-NG",
        "privacy_posture": "Public persona, but keeps sponsorship terms private",
        "acceptance_criteria": "Static and animated logo variants, social-ready exports",
        "behaviour": (
            "Creator who wants motion, shareability, and fast social publishing while "
            "keeping sponsorship details out of the creative prompt."
        ),
        "avoid_list": "No private sponsorship rates, no inaccessible motion-only meaning",
        "features": ["design_ai", "animation", "effects", "resize", "scheduler"],
        "yellow_recommendation": (
            "Use a bright sunshine yellow background with an optional animated stripe "
            "sweep, but ensure the static frame communicates the full logo."
        ),
        "full_prompt": prompt(
            """
            Create a scroll-stopping tiger image logo in Adobe Express for a creator brand.
            Persona rules: be energetic and direct, include static accessibility notes, and do not mention private sponsorship terms.

            Build it like this:
            1. Use Design with AI to generate a fierce-but-stylish tiger head that feels original.
            2. Add Effects, filters, textures and overlays for a punchy creator-brand finish.
            3. Use Animated effects to make the tiger stripes slide in for a short logo sting.
            4. Resize for social content: profile icon, reel cover, story sticker, and transparent overlay.
            5. Use Content Scheduler to draft a launch caption placeholder without sponsor details.

            Final checks: bright yellow background works in the first frame, the static version stands alone, and motion is decorative rather than required for meaning.
            """
        ),
    },
    {
        "name": "Omar Al-Farsi",
        "age": "56",
        "occupation": "Legal operations manager",
        "technical_skill": "Low",
        "prompt_style": "Precise, cautious, and verification-oriented",
        "ai_trust": "Very low",
        "accessibility": "Motor impairment; prefers fewer manual adjustments",
        "locale": "ar-SA / en",
        "privacy_posture": "Highly strict: no legal matter data or client identifiers",
        "acceptance_criteria": "Minimal manual edits, source record, legally safe assets",
        "behaviour": (
            "Cautious legal operator who needs a controlled, low-effort workflow with "
            "source verification and no client or matter information."
        ),
        "avoid_list": "No client identifiers, no legal matter references, no ambiguous asset rights",
        "features": ["stock", "quick_actions", "brand", "collaboration", "pdf"],
        "yellow_recommendation": (
            "Use a conservative ochre-yellow background with strong black linework; "
            "record the exact colour value in the approval document."
        ),
        "full_prompt": prompt(
            """
            Create a legally safe tiger image logo in Adobe Express with as few manual edits as possible.
            Persona rules: be precise, cautious, and verification-oriented. Do not include client identifiers, legal matter names, or confidential case details.

            Controlled workflow:
            1. Use Adobe Stock Assets for the tiger image only if the licence is clear for the intended use; otherwise stop and ask for an approved asset.
            2. Use Quick Actions to remove the background and crop the tiger into a simple logo badge.
            3. Apply your brand with approved black, white, and ochre-yellow values.
            4. Use Work better together to send the draft to legal and brand reviewers.
            5. Use PDF tools to export an approval record with asset source, colour values, and final file names.

            Completion criteria: no confidential information, documented asset rights, readable yellow-background version, and a transparent export for controlled reuse.
            """
        ),
    },
]


class TableParser(HTMLParser):
    """Extract simple HTML table cells without external dependencies."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "tr":
            self._row = []
        elif tag.lower() in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"td", "th"} and self._cell is not None and self._row is not None:
            cell = " ".join("".join(self._cell).split())
            self._row.append(cell)
            self._cell = None
        elif tag.lower() == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None


def parse_persona_html(path: Path) -> list[dict[str, str | list[str]]]:
    """Best-effort parsing for simple persona HTML tables."""

    if not path.exists():
        return []

    parser = TableParser()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    if len(parser.rows) < 2:
        return []

    header = [slug(cell) for cell in parser.rows[0]]
    personas: list[dict[str, str | list[str]]] = []
    for row in parser.rows[1:]:
        record = {header[i]: row[i] for i in range(min(len(header), len(row)))}
        name = first(record, "persona", "name", "persona_name") or f"Persona {len(personas) + 1}"
        behaviour = first(record, "behaviour", "behavior", "profile", "behaviour_profile") or "Persona behaviour imported from HTML table."
        technical_skill = first(record, "technical_skill", "skill", "technical") or "Not specified"
        prompt_style = first(record, "prompt_style", "communication_style", "style") or "Persona-consistent"
        ai_trust = first(record, "ai_trust", "trust") or "Not specified"
        privacy_posture = first(record, "privacy", "privacy_posture") or "Not specified"
        accessibility = first(record, "accessibility", "accessibility_needs") or "Not specified"
        occupation = first(record, "occupation", "role", "job") or "Not specified"
        age = first(record, "age") or "Not specified"
        locale = first(record, "locale", "region", "language") or "Not specified"
        acceptance = first(record, "acceptance_criteria", "criteria") or "Tiger logo satisfies persona behaviour constraints."
        features = infer_features(" ".join([behaviour, technical_skill, prompt_style, ai_trust, privacy_posture, accessibility, occupation]))
        personas.append(
            {
                "name": name,
                "age": age,
                "occupation": occupation,
                "technical_skill": technical_skill,
                "prompt_style": prompt_style,
                "ai_trust": ai_trust,
                "accessibility": accessibility,
                "locale": locale,
                "privacy_posture": privacy_posture,
                "acceptance_criteria": acceptance,
                "behaviour": behaviour,
                "avoid_list": first(record, "avoid", "avoid_list") or "Avoid persona-inappropriate wording or private information.",
                "features": features,
                "yellow_recommendation": yellow_recommendation(" ".join([behaviour, occupation, accessibility])),
                "full_prompt": imported_prompt(name, behaviour, prompt_style, privacy_posture, accessibility, acceptance, features),
            }
        )
    return personas


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def first(record: dict[str, str], *keys: str) -> str:
    for key in keys:
        if record.get(key):
            return record[key]
    return ""


def infer_features(text: str) -> list[str]:
    text_l = text.lower()
    selected: list[str] = []
    if any(term in text_l for term in ["beginner", "low", "novice", "simple", "step"]):
        selected += ["templates", "quick_actions"]
    if any(term in text_l for term in ["ai", "creative", "generate", "experimental", "high trust"]):
        selected.append("design_ai")
    if any(term in text_l for term in ["brand", "enterprise", "compliance", "approved"]):
        selected.append("brand")
    if any(term in text_l for term in ["privacy", "strict", "legal", "review", "approval"]):
        selected += ["collaboration", "pdf"]
    if any(term in text_l for term in ["social", "campaign", "creator", "marketing"]):
        selected += ["resize", "scheduler"]
    if any(term in text_l for term in ["video", "motion", "animated"]):
        selected.append("animation")
    if any(term in text_l for term in ["accessibility", "vision", "dyslexia", "readable"]):
        selected.append("fonts")
    if any(term in text_l for term in ["licence", "license", "stock", "asset"]):
        selected.append("stock")
    selected += ["elements", "effects"]

    result: list[str] = []
    for key in selected:
        if key not in result:
            result.append(key)
    return result[:6] if len(result) >= 4 else (result + ["brand", "fonts", "resize"])[:6]


def yellow_recommendation(text: str) -> str:
    text_l = text.lower()
    if "legal" in text_l or "strict" in text_l:
        return "Use a conservative ochre-yellow background and document the exact colour value."
    if "vision" in text_l or "accessibility" in text_l:
        return "Use a high-contrast yellow background with dark tiger linework and large clear text."
    if "cafe" in text_l or "friendly" in text_l:
        return "Use a creamy honey-yellow background for a warm, approachable tiger logo."
    return "Use a rich golden-yellow background to support tiger recognition and strong contrast."


def imported_prompt(
    name: str,
    behaviour: str,
    prompt_style: str,
    privacy: str,
    accessibility: str,
    acceptance: str,
    features: Iterable[str],
) -> str:
    feature_names = ", ".join(FEATURES[key].name for key in features if key in FEATURES)
    return prompt(
        f"""
        Create a tiger image logo in Adobe Express for {name}.
        Persona behaviour: {behaviour}
        Communication style: {prompt_style}
        Privacy posture: {privacy}
        Accessibility needs: {accessibility}

        Use these Adobe Express features by name: {feature_names}.
        Build the logo with a yellow or golden background, a clear tiger image, editable text, and export-ready variants.
        Keep the workflow aligned to the persona behaviour and do not introduce private or persona-inappropriate details.

        Acceptance criteria: {acceptance}
        """
    )


def feature_rationale(persona: dict[str, str | list[str]], feature_key: str) -> str:
    text = " ".join(
        str(persona.get(key, ""))
        for key in [
            "behaviour",
            "technical_skill",
            "prompt_style",
            "ai_trust",
            "accessibility",
            "privacy_posture",
            "occupation",
        ]
    ).lower()
    feature = FEATURES[feature_key]
    if feature_key == "quick_actions":
        return "Selected because this persona benefits from fast cleanup, resizing, or low-manual-effort image edits."
    if feature_key == "design_ai":
        return "Selected because the tiger image can be generated or varied quickly while preserving the persona's creative control level."
    if feature_key == "templates":
        return "Selected because templates reduce design complexity and help the persona start from a proven logo layout."
    if feature_key == "stock":
        return "Selected because the persona needs licensed or source-verifiable assets."
    if feature_key == "brand":
        return "Selected because brand colours, fonts, or enterprise controls are important to this persona."
    if feature_key == "collaboration":
        return "Selected because review, approval, or co-editing is part of the persona's risk posture."
    if feature_key == "effects":
        return "Selected because visual polish is needed without leaving Adobe Express."
    if feature_key == "elements":
        return "Selected because badges, shapes, icons, or backgrounds support the tiger logo composition."
    if feature_key == "fonts":
        if any(term in text for term in ["dyslexia", "vision", "readable", "accessibility"]):
            return "Selected because readable licensed typography supports the persona's accessibility needs."
        return "Selected because the logo may need a licensed wordmark or font pairing."
    if feature_key == "animation":
        return "Selected because this persona needs an optional motion or creator-facing variant."
    if feature_key == "resize":
        return "Selected because the logo must be adapted for social, slide, or multi-channel placements."
    if feature_key == "scheduler":
        return "Selected because the persona works with social publishing or campaign launch planning."
    if feature_key == "qr":
        return "Selected because the persona needs a print or local-business touchpoint."
    if feature_key == "pdf":
        return "Selected because the persona needs a formal handoff, approval record, or printable guide."
    return feature.description


def image_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def build_svg(path: Path) -> None:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-labelledby="title desc">
  <title id="title">Tiger logo reference</title>
  <desc id="desc">Editable tiger head badge on a yellow background.</desc>
  <rect width="512" height="512" rx="96" fill="#ffc928"/>
  <circle cx="256" cy="258" r="168" fill="#f58220" stroke="#111111" stroke-width="18"/>
  <path d="M117 130l77 35-55 42zM395 130l-77 35 55 42z" fill="#111111"/>
  <path d="M160 198l64 26-78 16zM352 198l-64 26 78 16zM187 294l46 12-58 43zM325 294l-46 12 58 43z" fill="#111111"/>
  <path d="M217 250c16-17 62-17 78 0-9 37-25 64-39 64s-30-27-39-64z" fill="#ffffff"/>
  <path d="M208 258c21 14 75 14 96 0" fill="none" stroke="#111111" stroke-width="12" stroke-linecap="round"/>
  <circle cx="207" cy="242" r="15" fill="#111111"/>
  <circle cx="305" cy="242" r="15" fill="#111111"/>
  <path d="M256 273l-22 24h44z" fill="#111111"/>
  <path d="M222 331c22 18 46 18 68 0" fill="none" stroke="#111111" stroke-width="12" stroke-linecap="round"/>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def build_html(
    personas: list[dict[str, str | list[str]]],
    output_path: Path,
    source_status: str,
    logo_uri: str,
) -> None:
    cards = []
    for index, persona in enumerate(personas, start=1):
        feature_keys = [key for key in persona["features"] if key in FEATURES]  # type: ignore[index]
        feature_rows = "\n".join(
            f"""
            <li>
              <strong>{html.escape(FEATURES[key].name)}</strong>
              <span>{html.escape(FEATURES[key].website_label)}</span>
              <p>{html.escape(feature_rationale(persona, key))}</p>
            </li>
            """
            for key in feature_keys
        )
        chips = " ".join(f"<span>{html.escape(FEATURES[key].name)}</span>" for key in feature_keys)
        prompt_text = str(persona["full_prompt"])
        cards.append(
            f"""
            <article class="card" data-search="{html.escape(json.dumps(persona).lower())}">
              <div class="card-head">
                <div>
                  <p class="eyebrow">SI.No {index:02d}</p>
                  <h2>{html.escape(str(persona["name"]))}</h2>
                  <p class="role">{html.escape(str(persona["occupation"]))} | Age {html.escape(str(persona["age"]))} | {html.escape(str(persona["locale"]))}</p>
                </div>
                <button data-copy="prompt-{index}">Copy prompt</button>
              </div>
              <div class="summary-grid">
                <div><b>Technical skill</b><span>{html.escape(str(persona["technical_skill"]))}</span></div>
                <div><b>Prompt style</b><span>{html.escape(str(persona["prompt_style"]))}</span></div>
                <div><b>AI trust</b><span>{html.escape(str(persona["ai_trust"]))}</span></div>
                <div><b>Accessibility</b><span>{html.escape(str(persona["accessibility"]))}</span></div>
                <div><b>Privacy posture</b><span>{html.escape(str(persona["privacy_posture"]))}</span></div>
                <div><b>Acceptance criteria</b><span>{html.escape(str(persona["acceptance_criteria"]))}</span></div>
              </div>
              <section class="behaviour">
                <h3>Behaviour profile</h3>
                <p>{html.escape(str(persona["behaviour"]))}</p>
                <p><strong>Avoid-list:</strong> {html.escape(str(persona["avoid_list"]))}</p>
              </section>
              <section>
                <h3>Mapped Adobe Express features</h3>
                <div class="chips">{chips}</div>
                <ul class="features">{feature_rows}</ul>
              </section>
              <section class="yellow">
                <h3>Yellow-background recommendation</h3>
                <p>{html.escape(str(persona["yellow_recommendation"]))}</p>
              </section>
              <section>
                <h3>Persona-isolated prompt</h3>
                <pre id="prompt-{index}">{html.escape(prompt_text)}</pre>
              </section>
            </article>
            """
        )

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Adobe Express Persona Test Cases - Tiger Logo</title>
  <style>
    :root {{
      --ink: #152033;
      --muted: #5f6b7a;
      --card: #ffffff;
      --yellow: #ffd23f;
      --orange: #f47b20;
      --purple: #6d4aff;
      --blue: #0974f1;
      --green: #00a878;
      --shadow: 0 20px 45px rgba(21, 32, 51, .14);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(255, 210, 63, .55), transparent 32rem),
        radial-gradient(circle at 85% 12%, rgba(109, 74, 255, .2), transparent 28rem),
        linear-gradient(135deg, #fff9e8 0%, #eef5ff 48%, #fff 100%);
      min-height: 100vh;
    }}
    header {{
      padding: 48px min(6vw, 72px) 30px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 240px;
      gap: 32px;
      align-items: center;
    }}
    h1 {{ font-size: clamp(2rem, 5vw, 4.7rem); line-height: .94; margin: 0 0 18px; letter-spacing: -0.06em; }}
    h2 {{ margin: 0; font-size: 1.65rem; }}
    h3 {{ margin: 0 0 10px; }}
    p {{ line-height: 1.55; }}
    .hero-card {{
      background: rgba(255, 255, 255, .72);
      border: 1px solid rgba(255,255,255,.88);
      backdrop-filter: blur(16px);
      box-shadow: var(--shadow);
      border-radius: 30px;
      padding: 24px;
      text-align: center;
    }}
    .hero-card img {{ width: 100%; border-radius: 24px; background: var(--yellow); }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}
    .meta span, .chips span {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 8px 12px;
      background: #fff;
      color: #25324a;
      border: 1px solid rgba(21, 32, 51, .12);
      font-weight: 700;
      font-size: .82rem;
    }}
    .notice {{
      margin: 0 min(6vw, 72px) 24px;
      padding: 18px 20px;
      border-left: 6px solid var(--orange);
      background: #fff6d6;
      border-radius: 18px;
      box-shadow: 0 10px 25px rgba(244, 123, 32, .12);
    }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 5;
      padding: 14px min(6vw, 72px);
      background: rgba(255, 255, 255, .82);
      backdrop-filter: blur(18px);
      border-block: 1px solid rgba(21,32,51,.08);
    }}
    input[type="search"] {{
      width: 100%;
      border: 2px solid rgba(9, 116, 241, .18);
      border-radius: 18px;
      padding: 16px 18px;
      font-size: 1rem;
      outline: none;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.7);
    }}
    main {{
      display: grid;
      gap: 28px;
      padding: 28px min(6vw, 72px) 64px;
    }}
    .card {{
      background: var(--card);
      border-radius: 28px;
      box-shadow: var(--shadow);
      overflow: hidden;
      border: 1px solid rgba(21,32,51,.08);
    }}
    .card-head {{
      display: flex;
      justify-content: space-between;
      gap: 24px;
      padding: 26px;
      color: #fff;
      background: linear-gradient(135deg, var(--ink), var(--purple));
    }}
    .eyebrow {{ margin: 0 0 6px; color: var(--yellow); font-weight: 900; letter-spacing: .12em; text-transform: uppercase; font-size: .75rem; }}
    .role {{ margin: 8px 0 0; color: rgba(255,255,255,.78); }}
    button {{
      align-self: start;
      border: 0;
      border-radius: 999px;
      background: var(--yellow);
      color: #111;
      font-weight: 900;
      padding: 11px 16px;
      cursor: pointer;
      box-shadow: 0 8px 18px rgba(0,0,0,.2);
    }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 1px;
      background: rgba(21,32,51,.08);
    }}
    .summary-grid div {{
      background: #fbfcff;
      padding: 18px;
      min-height: 96px;
    }}
    .summary-grid b {{ display: block; color: var(--blue); margin-bottom: 7px; }}
    .summary-grid span {{ color: var(--muted); }}
    section {{ padding: 22px 26px; border-top: 1px solid rgba(21,32,51,.08); }}
    .behaviour {{ background: #f7fbff; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 14px; }}
    .chips span {{ background: #eff6ff; border-color: #d7e9ff; color: #075ebd; }}
    .features {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; list-style: none; margin: 0; padding: 0; }}
    .features li {{ padding: 15px; border-radius: 18px; background: #fff; border: 1px solid rgba(21,32,51,.1); }}
    .features span {{ display: block; color: var(--green); font-size: .82rem; font-weight: 800; margin-top: 4px; }}
    .features p {{ margin: 8px 0 0; color: var(--muted); }}
    .yellow {{ background: linear-gradient(135deg, rgba(255,210,63,.3), rgba(244,123,32,.08)); }}
    pre {{
      white-space: pre-wrap;
      margin: 0;
      background: #121a2a;
      color: #eff6ff;
      border-radius: 18px;
      padding: 20px;
      line-height: 1.55;
      overflow-x: auto;
    }}
    footer {{ padding: 0 min(6vw,72px) 50px; color: var(--muted); }}
    @media (max-width: 860px) {{
      header {{ grid-template-columns: 1fr; }}
      .summary-grid, .features {{ grid-template-columns: 1fr; }}
      .card-head {{ flex-direction: column; }}
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <p class="eyebrow">Adobe Express Enterprise x ChatGPT</p>
      <h1>Persona-isolated tiger logo prompt showcase</h1>
      <p>Shared task: create a logo with a tiger image. Each test case maps persona behaviour to Adobe Express features listed on the Adobe Express feature page and provides a unique prompt for the integrated workflow.</p>
      <div class="meta">
        <span>{len(personas)} personas</span>
        <span>Searchable</span>
        <span>Copy-enabled prompts</span>
        <span>Yellow-background recommendations</span>
      </div>
    </div>
    <div class="hero-card">
      {'<img src="' + logo_uri + '" alt="Generated tiger logo reference">' if logo_uri else '<strong>Tiger logo reference image included separately.</strong>'}
      <p>Generated tiger logo reference image included with deliverables.</p>
    </div>
  </header>
  <div class="notice">
    <strong>Source status:</strong> {html.escape(source_status)}
  </div>
  <div class="toolbar">
    <input id="search" type="search" placeholder="Search persona, behaviour, feature, privacy posture, or prompt wording...">
  </div>
  <main id="cards">
    {''.join(cards)}
  </main>
  <footer>
    Adobe Express feature references were curated from https://www.adobe.com/in/express/feature. The supplied local Windows persona path was {html.escape(REQUESTED_SOURCE)}.
  </footer>
  <script>
    const search = document.querySelector('#search');
    const cards = [...document.querySelectorAll('.card')];
    search.addEventListener('input', () => {{
      const term = search.value.trim().toLowerCase();
      cards.forEach(card => {{
        card.style.display = !term || card.dataset.search.includes(term) ? '' : 'none';
      }});
    }});
    document.querySelectorAll('[data-copy]').forEach(button => {{
      button.addEventListener('click', async () => {{
        const id = button.getAttribute('data-copy');
        const text = document.getElementById(id).innerText;
        await navigator.clipboard.writeText(text);
        const original = button.innerText;
        button.innerText = 'Copied';
        setTimeout(() => button.innerText = original, 1200);
      }});
    }});
  </script>
</body>
</html>
"""
    output_path.write_text(html_doc, encoding="utf-8")


def paragraph(text: str) -> str:
    runs = []
    for line in text.splitlines() or [""]:
        if runs:
            runs.append("<w:br/>")
        runs.append(f"<w:t xml:space=\"preserve\">{escape(line)}</w:t>")
    return f"<w:p><w:r>{''.join(runs)}</w:r></w:p>"


def heading(text: str, level: int = 1) -> str:
    size = "32" if level == 1 else "26"
    return (
        "<w:p><w:pPr><w:spacing w:after=\"160\"/></w:pPr>"
        f"<w:r><w:rPr><w:b/><w:sz w:val=\"{size}\"/></w:rPr>"
        f"<w:t>{escape(text)}</w:t></w:r></w:p>"
    )


def table(rows: list[list[str]]) -> str:
    row_xml = []
    for row in rows:
        cells = []
        for cell in row:
            cells.append(
                "<w:tc><w:tcPr><w:tcW w:w=\"2400\" w:type=\"dxa\"/></w:tcPr>"
                f"{paragraph(cell)}</w:tc>"
            )
        row_xml.append(f"<w:tr>{''.join(cells)}</w:tr>")
    return (
        "<w:tbl><w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/>"
        "<w:tblBorders><w:top w:val=\"single\" w:sz=\"4\" w:color=\"D9E2F3\"/>"
        "<w:left w:val=\"single\" w:sz=\"4\" w:color=\"D9E2F3\"/>"
        "<w:bottom w:val=\"single\" w:sz=\"4\" w:color=\"D9E2F3\"/>"
        "<w:right w:val=\"single\" w:sz=\"4\" w:color=\"D9E2F3\"/>"
        "<w:insideH w:val=\"single\" w:sz=\"4\" w:color=\"D9E2F3\"/>"
        "<w:insideV w:val=\"single\" w:sz=\"4\" w:color=\"D9E2F3\"/></w:tblBorders></w:tblPr>"
        + "".join(row_xml)
        + "</w:tbl>"
    )


def build_docx(
    personas: list[dict[str, str | list[str]]],
    output_path: Path,
    source_status: str,
) -> None:
    summary_rows = [["SI.No", "Persona", "Behaviour summary", "Mapped features"]]
    for index, persona in enumerate(personas, start=1):
        feature_names = ", ".join(FEATURES[key].name for key in persona["features"] if key in FEATURES)  # type: ignore[index]
        summary_rows.append(
            [
                str(index),
                f"{persona['name']} - {persona['occupation']}",
                str(persona["behaviour"]),
                feature_names,
            ]
        )

    body = [
        heading("Persona Test Cases from Adobe - Tiger Logo", 1),
        paragraph("Shared creative task: create a logo with a tiger image using Adobe Express Enterprise integrated with ChatGPT."),
        paragraph(f"Source status: {source_status}"),
        paragraph("Feature source: https://www.adobe.com/in/express/feature"),
        heading("Summary table", 2),
        table(summary_rows),
    ]

    for index, persona in enumerate(personas, start=1):
        feature_lines = []
        for key in persona["features"]:  # type: ignore[index]
            if key in FEATURES:
                feature_lines.append(f"- {FEATURES[key].name}: {feature_rationale(persona, key)}")
        body.extend(
            [
                heading(f"SI.No {index:02d}: {persona['name']}", 2),
                table(
                    [
                        ["Field", "Value"],
                        ["Age", str(persona["age"])],
                        ["Occupation", str(persona["occupation"])],
                        ["Technical skill", str(persona["technical_skill"])],
                        ["Prompt style", str(persona["prompt_style"])],
                        ["AI trust level", str(persona["ai_trust"])],
                        ["Accessibility", str(persona["accessibility"])],
                        ["Locale", str(persona["locale"])],
                        ["Privacy posture", str(persona["privacy_posture"])],
                        ["Acceptance criteria", str(persona["acceptance_criteria"])],
                    ]
                ),
                heading("Behaviour-to-feature mapping", 2),
                paragraph("\n".join(feature_lines)),
                heading("Yellow-background recommendation", 2),
                paragraph(str(persona["yellow_recommendation"])),
                heading("Persona-isolated prompt", 2),
                paragraph(str(persona["full_prompt"])),
            ]
        )

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {''.join(body)}
    <w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720" w:header="360" w:footer="360" w:gutter="0"/></w:sectPr>
  </w:body>
</w:document>
"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/document.xml", document_xml)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persona-html", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("Desktop"))
    parser.add_argument("--logo-image", type=Path, default=Path("Desktop/tiger-logo.png"))
    args = parser.parse_args()

    personas: list[dict[str, str | list[str]]] = []
    source_status: str
    if args.persona_html:
        personas = parse_persona_html(args.persona_html)
        if personas:
            source_status = f"Loaded {len(personas)} personas from {args.persona_html}."
        else:
            source_status = (
                f"Could not parse persona rows from {args.persona_html}; used labelled fallback personas. "
                f"Original requested source was {REQUESTED_SOURCE}."
            )
    else:
        source_status = (
            "The requested Windows Desktop persona file is not accessible from this Linux cloud workspace; "
            "used labelled fallback personas to demonstrate the required behaviour-to-feature mapping. "
            f"Requested source: {REQUESTED_SOURCE}."
        )
    if not personas:
        personas = FALLBACK_PERSONAS

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    logo_target = output_dir / "tiger-logo.png"
    if args.logo_image.exists() and args.logo_image.resolve() != logo_target.resolve():
        shutil.copyfile(args.logo_image, logo_target)

    build_svg(output_dir / "tiger-logo.svg")
    build_html(
        personas,
        output_dir / "Persona_Test_Cases_from_adobe_Demo.html",
        source_status,
        image_data_uri(logo_target),
    )
    build_docx(personas, output_dir / "Persona Test Cases from adobe.docx", source_status)

    manifest = {
        "task": "Create a logo with tiger image",
        "requested_persona_source": REQUESTED_SOURCE,
        "source_status": source_status,
        "adobe_feature_source": "https://www.adobe.com/in/express/feature",
        "outputs": [
            "Persona_Test_Cases_from_adobe_Demo.html",
            "Persona Test Cases from adobe.docx",
            "tiger-logo.png",
            "tiger-logo.svg",
        ],
        "personas": [persona["name"] for persona in personas],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
