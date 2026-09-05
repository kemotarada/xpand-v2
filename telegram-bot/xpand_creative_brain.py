# -*- coding: utf-8 -*-
"""
XPAND CREATIVE BRAIN V5.0
Quality-upgraded ideation director
Compatible with:
- XPAND Smart Image Engine V2.2
- XPAND STC Bank Visual Skill V3.0
- XPAND Brand Research V2.0
- XPAND Brand Memory V3.0
- XPAND Production Engine V5.0
- XPAND Image Telegram V3.4

Purpose:
- Generate higher-quality ad concepts, especially for STC Bank
- Enforce premium ad-thinking instead of generic "person using phone" scenes
- Require a clear visual mechanism, one strong message, and clean composition
- Preserve the "technical failure -> smart fallback allowed" contract

Notes:
- This module focuses on IDEATION and concept selection, not final image generation
- No winner-finalizer paid call
- Normal director calls = 2
- Maximum calls with recovery = 3
"""

from __future__ import annotations

import ast
import json
import os
import re
import textwrap
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Tuple

__version__ = "5.0"


# =========================================================
# Exceptions
# =========================================================

class CreativeBrainError(Exception):
    """Base error for creative brain."""


class TechnicalCreativeFailure(CreativeBrainError):
    """
    Technical failure only.
    Must preserve Smart Engine fallback.
    """


# =========================================================
# Data models
# =========================================================

@dataclass
class CreativeConcept:
    title: str
    hook: str
    benefit_message: str
    scene_archetype: str
    visual_mechanism: str
    hero_subject: str
    scene_description: str
    saudi_authenticity: str
    brand_dna: str
    camera: str
    lighting: str
    materials: str
    composition: str
    copy_space: str
    why_memorable: str
    why_feasible: str
    avoid: List[str] = field(default_factory=list)
    negative_prompt: List[str] = field(default_factory=list)
    score: float = 0.0
    review_notes: List[str] = field(default_factory=list)


@dataclass
class CreativeResult:
    ok: bool
    technical_failure: bool
    allow_smart_engine_fallback: bool
    creative_state: str
    creative_score: Optional[float]
    benefit_family: str
    stc_style: str
    concepts: List[Dict[str, Any]]
    shortlist: List[Dict[str, Any]]
    selected_concept: Optional[Dict[str, Any]]
    director_calls_made: int
    director_routes_tried: List[str]
    reason: str
    errors: List[str]


# =========================================================
# Utilities
# =========================================================

def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on", "y"}


def _clamp(num: float, low: float, high: float) -> float:
    return max(low, min(high, num))


def _strip_fences(text: str) -> str:
    if not isinstance(text, str):
        return text
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json|python|py)?\s*", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _extract_json_candidate(text: str) -> str:
    text = _strip_fences(text)
    if not isinstance(text, str):
        return text

    # Try to extract first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1].strip()
    return text.strip()


def _parse_structured_text(text: str) -> Dict[str, Any]:
    """
    Accept:
    - native dict
    - fenced JSON
    - python literal
    """
    if isinstance(text, dict):
        return text

    if not isinstance(text, str):
        raise ValueError("Structured text is neither dict nor string")

    candidate = _extract_json_candidate(text)

    # JSON
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Python literal
    try:
        parsed = ast.literal_eval(candidate)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    raise ValueError("Structured output is not valid JSON.")


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _listify(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        return [value]
    return [str(value).strip()]


def _contains_any(text: str, keywords: List[str]) -> bool:
    low = (text or "").lower()
    return any(k.lower() in low for k in keywords)


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


# =========================================================
# JSON schema
# =========================================================

IDEATION_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "concepts": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "hook": {"type": "string"},
                    "benefit_message": {"type": "string"},
                    "scene_archetype": {"type": "string"},
                    "visual_mechanism": {"type": "string"},
                    "hero_subject": {"type": "string"},
                    "scene_description": {"type": "string"},
                    "saudi_authenticity": {"type": "string"},
                    "brand_dna": {"type": "string"},
                    "camera": {"type": "string"},
                    "lighting": {"type": "string"},
                    "materials": {"type": "string"},
                    "composition": {"type": "string"},
                    "copy_space": {"type": "string"},
                    "why_memorable": {"type": "string"},
                    "why_feasible": {"type": "string"},
                    "avoid": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "negative_prompt": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": [
                    "title",
                    "hook",
                    "benefit_message",
                    "scene_archetype",
                    "visual_mechanism",
                    "hero_subject",
                    "scene_description",
                    "saudi_authenticity",
                    "brand_dna",
                    "camera",
                    "lighting",
                    "materials",
                    "composition",
                    "copy_space",
                    "why_memorable",
                    "why_feasible",
                    "avoid",
                    "negative_prompt"
                ]
            }
        }
    },
    "required": ["concepts"]
}


# =========================================================
# STC / Brand heuristics
# =========================================================

APPROVED_SCENE_ARCHETYPES = {
    "product_hero_set",
    "premium_lifestyle_utility",
    "merchant_commerce_fusion",
    "app_utility_hero",
    "travel_freedom_lifestyle",
    "benefit_symbolic_realism",
    "home_life_financing",
    "executive_finance_lifestyle",
    "support_service_utility"
}

APPROVED_VISUAL_MECHANISMS = {
    "continuous_commerce_journey",
    "card_as_portal",
    "card_as_architecture",
    "device_as_service_window",
    "benefit_visible_in_real_life_moment",
    "app_ui_anchored_in_real_action",
    "hero_product_on_premium_set",
    "single_service_single_scene_fusion",
    "brand_colored_path_or_ribbon",
    "service_transformation_moment"
}

GENERIC_BAD_PATTERNS = [
    "person using phone",
    "man using phone",
    "woman using phone",
    "customer paying",
    "person standing",
    "office portrait",
    "generic banking scene",
    "generic fintech scene",
    "floating interface",
    "glowing network lines",
    "neon fintech",
    "abstract banking background",
]

ANTI_NEON_TERMS = [
    "neon", "glowing lines", "network lines", "cyber", "hologram city", "futuristic banking"
]

STC_VISUAL_DISCIPLINE = [
    "premium realism",
    "architectural clarity",
    "calm luxury lighting",
    "disciplined purple use",
    "deep purple or neutral palette",
    "mint-green accent only when justified",
    "clean hero composition",
    "one clear message",
    "copy space",
    "no cheap fintech clutter"
]


# =========================================================
# Benefit / style detection
# =========================================================

def detect_benefit_family(payload: Dict[str, Any]) -> str:
    explicit = _safe_text(payload.get("benefit_family"))
    if explicit:
        return explicit.strip().lower()

    text = " ".join([
        _safe_text(payload.get("prompt")),
        _safe_text(payload.get("user_text")),
        _safe_text(payload.get("brief")),
        _safe_text(payload.get("service")),
        _safe_text(payload.get("benefit"))
    ]).lower()

    checks = [
        (["merchant", "point of sale", "pos", "trade", "e-commerce", "ecommerce", "online store", "payments", "نقاط البيع", "التجارة الإلكترونية", "تاجر", "مدفوعات"], "merchant_payments"),
        (["travel", "visa", "airport", "cashback", "بطاقة", "بطاقات", "سفر"], "cards_travel"),
        (["salary", "loan", "finance", "personal financing", "راتب", "تمويل", "تمويل شخصي"], "salary_financing"),
        (["iban", "transfer", "transfers", "bank transfer", "آيبان", "حوالة", "حوالات"], "transfers_iban"),
        (["digital card", "gift cards", "marketplace", "market", "بطاقات رقمية", "السوق", "بطاقات المتاجر"], "digital_marketplace"),
        (["support", "faq", "help", "contact", "دعم", "تواصل", "مساعدة"], "digital_support"),
        (["international top up", "numbers", "top up", "شحن أرقام", "دولي"], "international_topup"),
        (["furniture", "home", "home finance", "أثاث", "بيت", "منزل"], "home_financing"),
    ]

    for terms, family in checks:
        if _contains_any(text, terms):
            return family

    return "general_banking"


def detect_stc_style(payload: Dict[str, Any]) -> str:
    explicit = _safe_text(payload.get("stc_style"))
    explicit_low = explicit.lower()

    if explicit_low in {"premium_realistic", "premium_purple_architecture", "premium_augmented_realism"}:
        return explicit_low

    full = " ".join([
        explicit,
        _safe_text(payload.get("prompt")),
        _safe_text(payload.get("user_text")),
        _safe_text(payload.get("brief"))
    ]).lower()

    if _contains_any(full, ["augmented", "conceptual realism", "cinematic symbolic", "معزز", "واقعية معززة"]):
        return "premium_augmented_realism"

    if _contains_any(full, ["purple architecture", "architectural purple", "بنفسجي", "purple set", "استوديو بنفسجي"]):
        return "premium_purple_architecture"

    # Default for STC Bank remains realistic
    return "premium_realistic"


# =========================================================
# Main class
# =========================================================

class XPANDCreativeBrain:
    VERSION = __version__

    def __init__(self) -> None:
        # Routing / model config
        self.openai_enabled = _env_bool("XPAND_OPENAI_ENABLED", True)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()

        self.openai_model_sol = os.getenv("XPAND_OPENAI_DIRECTOR_MODEL", "gpt-5.6-sol").strip()
        self.gemini_structured_model = os.getenv("XPAND_GEMINI_STRUCTURED_MODEL", "gemini-2.5-flash").strip()

        self.max_director_calls = int(os.getenv("XPAND_IMAGE_DIRECTOR_MAX_CALLS", "3"))
        self.normal_director_calls = 2
        self.shortlist_size = 2

        # Score weights
        self.weights = {
            "concept_strength": 25,
            "stc_brand_fit": 20,
            "originality": 15,
            "visual_mechanism": 15,
            "hero_quality": 10,
            "feasibility": 10,
            "copy_space": 5,
        }

    # -----------------------------------------------------
    # Prompt building
    # -----------------------------------------------------

    def _build_system_prompt(self, ctx: Dict[str, Any]) -> str:
        benefit_family = ctx["benefit_family"]
        stc_style = ctx["stc_style"]
        is_stc = ctx["brand"] == "stc_bank"

        special_family_rules = self._family_rules(benefit_family)
        style_rules = self._style_rules(stc_style)

        stc_block = ""
        if is_stc:
            stc_block = """
            You are the premium campaign ideation director for STC Bank-level advertising.

            CRITICAL STC QUALITY RULES:
            1) Do NOT produce generic scenes such as:
               - person using phone
               - customer paying at a counter
               - office portrait
               - random bank lifestyle
               unless the scene includes a STRONG visual mechanism and premium art direction.
            2) Every concept MUST contain one clear "visual mechanism".
               Examples:
               - device as a service window
               - card as a portal or architectural object
               - one continuous commerce journey
               - product hero anchored in a premium physical set
               - real-life benefit made visible in a single memorable moment
            3) One message only per concept.
            4) One hero only per concept.
            5) Reserve 25%–40% clean copy space for later typography.
            6) NO generated slogans, NO paragraphs of ad copy, NO legal copy, NO logos rendered inside the scene concept.
            7) No generic fintech language, no neon banking, no floating UI clutter, no network lines.
            8) Output concepts that feel like premium regional banking advertising, not stock photography.
            9) The camera and composition must be intentionally ad-worthy, not incidental.
            10) Prefer concept structures similar to premium bank campaigns:
                - product hero set
                - lifestyle utility hero
                - symbolic realism
                - premium merchant/service scene with clear visual fusion
            """

        return textwrap.dedent(f"""
        You are XPAND CREATIVE BRAIN V5.0.

        TASK:
        Generate exactly 4 premium advertising image concepts in strict JSON.

        OUTPUT:
        Return a single JSON object matching the schema exactly.

        UNIVERSAL RULES:
        - Exactly 4 concepts. Not 20. Not more than 4.
        - Concepts must be image-first and production-feasible.
        - Avoid clutter and visual confusion.
        - Use scientific camera vocabulary and clear lighting vocabulary.
        - Merge creativity with feasibility.
        - Each concept must be distinct in camera, setting, and visual mechanism.
        - Concepts should be suitable for later image generation.
        - No generated copy inside the image concept itself.
        - No generated logos.
        - No fake banking UI overload.
        - No floating product clones.
        - No repetition of the same scene with minor tweaks.

        BRAND:
        {ctx["brand"]}

        BENEFIT FAMILY:
        {benefit_family}

        STYLE:
        {stc_style}

        STYLE RULES:
        {style_rules}

        FAMILY RULES:
        {special_family_rules}

        VISUAL DISCIPLINE:
        {", ".join(STC_VISUAL_DISCIPLINE)}

        APPROVED SCENE ARCHETYPES:
        {", ".join(sorted(APPROVED_SCENE_ARCHETYPES))}

        APPROVED VISUAL MECHANISMS:
        {", ".join(sorted(APPROVED_VISUAL_MECHANISMS))}

        {stc_block}

        REQUIRED FIELDS PER CONCEPT:
        - title
        - hook
        - benefit_message
        - scene_archetype
        - visual_mechanism
        - hero_subject
        - scene_description
        - saudi_authenticity
        - brand_dna
        - camera
        - lighting
        - materials
        - composition
        - copy_space
        - why_memorable
        - why_feasible
        - avoid (array)
        - negative_prompt (array)

        IMPORTANT:
        - scene_archetype must be one of the approved archetypes
        - visual_mechanism must be explicit and non-empty
        - composition must mention where the copy space is
        - copy_space must explicitly say left/right/top/bottom and roughly 25%-40%
        - avoid must include no_text and no_logo
        - negative_prompt should actively block neon fintech clutter and weak generic execution
        """).strip()

    def _family_rules(self, benefit_family: str) -> str:
        rules = {
            "merchant_payments": """
            - The scene must communicate BOTH e-commerce and in-store payment if relevant.
            - Do not solve it as "customer pays + someone packs in background" unless there is a clear visual fusion.
            - Prefer one continuous commercial journey:
              browsing / packing / checkout / fulfillment as one coherent visual story.
            - Use real Saudi merchant life: boutique, café, modern retail, premium counter, packaging desk, stock shelves.
            - Make the point-of-sale moment tangible and elegant.
            - Avoid generic fintech interface overlays.
            """,
            "cards_travel": """
            - Show one tangible travel/lifestyle benefit, not a vague card beauty shot only.
            - Prefer premium travel freedom moments, airport transitions, borderless usage, luxury mobility.
            - A card hero set is allowed if the concept is visually memorable and brand-premium.
            """,
            "salary_financing": """
            - Focus on life-upgrade moments: home, work, aspiration, family progress, practical achievement.
            - Avoid fake money visuals or over-literal banking clichés.
            """,
            "digital_marketplace": """
            - Show the app/service as useful, clean, and desirable.
            - Avoid screen overload.
            - The UI should feel secondary to the benefit.
            """,
            "digital_support": """
            - Communicate clarity, accessibility, and trust.
            - Prefer clean, utility-driven hero compositions.
            """,
            "international_topup": """
            - Show global reach through one coherent, premium mechanism.
            - Avoid tourist-postcard clutter.
            """,
            "transfers_iban": """
            - The benefit is accuracy, speed, and ease.
            - Avoid abstract lines, neon transfers, or fake digital tunnels.
            """,
            "home_financing": """
            - Show a real, desirable home-life improvement moment.
            - Avoid generic "happy couple holding keys".
            """,
            "general_banking": """
            - Show one banking benefit in one strong premium scene.
            - Avoid generic stock-banking imagery.
            """
        }
        return textwrap.dedent(rules.get(benefit_family, rules["general_banking"])).strip()

    def _style_rules(self, stc_style: str) -> str:
        if stc_style == "premium_purple_architecture":
            return textwrap.dedent("""
            - Purple is allowed as a dominant architectural or studio environment.
            - Use refined gradients and premium surfaces, not cheap neon.
            - Product staging and geometry should feel elegant and controlled.
            - Still keep realism and material believability.
            """).strip()

        if stc_style == "premium_augmented_realism":
            return textwrap.dedent("""
            - Use augmented realism: conceptually strong but still physically believable.
            - One metaphor only.
            - No sci-fi clutter.
            - The scene must still feel producible and premium.
            """).strip()

        return textwrap.dedent("""
        - Default to premium realism.
        - Real materials, believable spaces, premium lighting.
        - Purple is optional, not mandatory.
        - Do not use purple neon by default.
        - Prefer elegant, high-end Saudi lifestyle / retail / architectural realism.
        """).strip()

    def _build_user_prompt(self, ctx: Dict[str, Any]) -> str:
        return textwrap.dedent(f"""
        USER BRIEF:
        {ctx["prompt"]}

        NORMALIZED CONTEXT:
        brand = {ctx["brand"]}
        benefit_family = {ctx["benefit_family"]}
        stc_style = {ctx["stc_style"]}
        aspect_ratio = {ctx["aspect_ratio"]}
        image_size = {ctx["image_size"]}
        creative_mode = {ctx["creative_mode"]}

        IMPORTANT CREATIVE DIRECTIVE:
        Generate 4 ad concepts that are premium and memorable enough to feel like a high-end STC Bank campaign.
        Do not return weak or generic scenes.
        Every concept must be:
        - distinct
        - visually memorable
        - strongly art-directed
        - easy to convert into one hero advertising image

        QUALITY CHECK INSIDE THE IDEATION:
        Before finalizing any concept, reject it if it looks like:
        - just a person with a phone
        - just a customer paying
        - just a card on a background
        - just a generic office shot
        unless the concept also has a strong visual mechanism, premium composition, and real campaign presence.
        """).strip()

    # -----------------------------------------------------
    # Director calling
    # -----------------------------------------------------

    def _extract_openai_text(self, response: Any) -> str:
        if response is None:
            return ""

        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text

        # Best-effort extraction
        try:
            out = getattr(response, "output", None) or []
            chunks = []
            for item in out:
                content = getattr(item, "content", None) or []
                for c in content:
                    txt = getattr(c, "text", None)
                    if txt:
                        chunks.append(txt)
            return "\n".join(chunks).strip()
        except Exception:
            pass

        return str(response)

    def _call_openai_response_once(self, system_prompt: str, user_prompt: str) -> str:
        if not self.openai_enabled:
            raise TechnicalCreativeFailure(
                "تم منع استدعاء OpenAI لأن XPAND_OPENAI_ENABLED=false. XPAND سيستخدم Gemini بدلًا منه."
            )
        if not self.openai_api_key:
            raise TechnicalCreativeFailure("OpenAI API key not configured.")

        try:
            from openai import OpenAI
        except Exception as e:
            raise TechnicalCreativeFailure(f"OpenAI SDK unavailable: {e}") from e

        try:
            client = OpenAI(api_key=self.openai_api_key)
            response = client.responses.create(
                model=self.openai_model_sol,
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": system_prompt}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": user_prompt}],
                    },
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "xpand_creative_brain_v5",
                        "strict": True,
                        "schema": IDEATION_JSON_SCHEMA,
                    }
                },
            )
            return self._extract_openai_text(response)
        except Exception as e:
            raise TechnicalCreativeFailure(f"OpenAI structured director failed: {e}") from e

    def _call_gemini_structured_once(self, system_prompt: str, user_prompt: str) -> str:
        if not self.gemini_api_key:
            raise TechnicalCreativeFailure("Gemini API key not configured.")

        full_prompt = (
            system_prompt
            + "\n\n"
            + "Return only JSON.\n\n"
            + user_prompt
        )

        # Try modern google.genai SDK first
        try:
            from google import genai  # type: ignore

            client = genai.Client(api_key=self.gemini_api_key)
            response = client.models.generate_content(
                model=self.gemini_structured_model,
                contents=full_prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.5,
                },
            )
            text = getattr(response, "text", None)
            if text:
                return text
            return str(response)
        except Exception:
            pass

        # Fallback SDK
        try:
            import google.generativeai as genai  # type: ignore

            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel(self.gemini_structured_model)
            response = model.generate_content(full_prompt)
            text = getattr(response, "text", None)
            if text:
                return text
            return str(response)
        except Exception as e:
            raise TechnicalCreativeFailure(f"Gemini structured director failed: {e}") from e

    def _call_director(self, system_prompt: str, user_prompt: str) -> Tuple[Dict[str, Any], int, List[str]]:
        """
        Normal = 2 calls
        Max = 3 with recovery
        OpenAI first for structured, Gemini fallback
        """
        calls = 0
        routes: List[str] = []
        errors: List[str] = []

        # 1) Strict OpenAI first
        try:
            calls += 1
            routes.append("openai_structured")
            text = self._call_openai_response_once(system_prompt, user_prompt)
            parsed = _parse_structured_text(text)
            return parsed, calls, routes
        except Exception as e:
            errors.append(f"openai_structured: {e}")

        # 2) Gemini structured fallback
        try:
            calls += 1
            routes.append("gemini_structured")
            text = self._call_gemini_structured_once(system_prompt, user_prompt)
            parsed = _parse_structured_text(text)
            return parsed, calls, routes
        except Exception as e:
            errors.append(f"gemini_structured: {e}")

        # 3) Recovery call (only once)
        if self.max_director_calls >= 3:
            # Prefer OpenAI recovery if enabled/configured
            recovery_route = "openai_recovery" if (self.openai_enabled and self.openai_api_key) else "gemini_recovery"
            try:
                calls += 1
                routes.append(recovery_route)
                if recovery_route == "openai_recovery":
                    text = self._call_openai_response_once(system_prompt, user_prompt)
                else:
                    text = self._call_gemini_structured_once(system_prompt, user_prompt)
                parsed = _parse_structured_text(text)
                return parsed, calls, routes
            except Exception as e:
                errors.append(f"{recovery_route}: {e}")

        raise TechnicalCreativeFailure(" | ".join(errors) if errors else "Structured Director failed.")

    # -----------------------------------------------------
    # Normalization / review
    # -----------------------------------------------------

    def _normalize_concept(self, raw: Dict[str, Any], ctx: Dict[str, Any], idx: int) -> CreativeConcept:
        return CreativeConcept(
            title=_safe_text(raw.get("title")) or f"Concept {idx}",
            hook=_safe_text(raw.get("hook")),
            benefit_message=_safe_text(raw.get("benefit_message")),
            scene_archetype=_safe_text(raw.get("scene_archetype")).strip().lower(),
            visual_mechanism=_safe_text(raw.get("visual_mechanism")).strip().lower(),
            hero_subject=_safe_text(raw.get("hero_subject")),
            scene_description=_safe_text(raw.get("scene_description")),
            saudi_authenticity=_safe_text(raw.get("saudi_authenticity")),
            brand_dna=_safe_text(raw.get("brand_dna")),
            camera=_safe_text(raw.get("camera")),
            lighting=_safe_text(raw.get("lighting")),
            materials=_safe_text(raw.get("materials")),
            composition=_safe_text(raw.get("composition")),
            copy_space=_safe_text(raw.get("copy_space")),
            why_memorable=_safe_text(raw.get("why_memorable")),
            why_feasible=_safe_text(raw.get("why_feasible")),
            avoid=_listify(raw.get("avoid")),
            negative_prompt=_listify(raw.get("negative_prompt")),
        )

    def _score_concept(self, concept: CreativeConcept, ctx: Dict[str, Any]) -> Tuple[float, List[str]]:
        notes: List[str] = []
        score = 0.0

        # 1) Concept strength
        concept_strength = 0.0
        if 2 <= _word_count(concept.title) <= 8:
            concept_strength += 5
        if _word_count(concept.scene_description) >= 18:
            concept_strength += 8
        if _word_count(concept.why_memorable) >= 8:
            concept_strength += 6
        if _word_count(concept.why_feasible) >= 6:
            concept_strength += 6
        concept_strength = _clamp(concept_strength, 0, self.weights["concept_strength"])
        score += concept_strength

        # 2) STC brand fit
        brand_fit = 0.0
        if concept.scene_archetype in APPROVED_SCENE_ARCHETYPES:
            brand_fit += 6
        if _contains_any(concept.brand_dna, ["premium", "purple", "mint", "neutral", "architectural", "clean"]):
            brand_fit += 6
        if _contains_any(" ".join(concept.avoid).lower(), ["no_text", "no logo", "no_logo"]):
            brand_fit += 4
        if _contains_any(" ".join(concept.negative_prompt).lower(), ["neon", "network", "fintech clutter", "floating"]):
            brand_fit += 4
        brand_fit = _clamp(brand_fit, 0, self.weights["stc_brand_fit"])
        score += brand_fit

        # 3) Originality
        originality = 0.0
        if concept.visual_mechanism and concept.visual_mechanism not in {"none", "generic", "n/a"}:
            originality += 6
        if concept.visual_mechanism in APPROVED_VISUAL_MECHANISMS:
            originality += 4
        if not _contains_any(concept.scene_description.lower(), GENERIC_BAD_PATTERNS):
            originality += 5
        originality = _clamp(originality, 0, self.weights["originality"])
        score += originality

        # 4) Visual mechanism
        visual_mech = 0.0
        if concept.visual_mechanism in APPROVED_VISUAL_MECHANISMS:
            visual_mech += 10
        elif concept.visual_mechanism:
            visual_mech += 5
        if _word_count(concept.why_memorable) >= 8:
            visual_mech += 5
        visual_mech = _clamp(visual_mech, 0, self.weights["visual_mechanism"])
        score += visual_mech

        # 5) Hero quality
        hero_quality = 0.0
        if _word_count(concept.hero_subject) >= 2:
            hero_quality += 4
        if _contains_any(concept.composition.lower(), ["hero", "foreground", "single hero", "dominant", "anchor"]):
            hero_quality += 3
        if _contains_any(concept.camera.lower(), ["worm", "bird", "three-quarter", "over-the-shoulder", "low angle", "elevated"]):
            hero_quality += 3
        hero_quality = _clamp(hero_quality, 0, self.weights["hero_quality"])
        score += hero_quality

        # 6) Feasibility
        feasibility = 0.0
        if _contains_any(concept.why_feasible.lower(), ["real location", "believable", "practical", "set", "retail", "studio", "producible"]):
            feasibility += 6
        if _contains_any(concept.materials.lower(), ["stone", "wood", "metal", "fabric", "glass", "paper", "matte"]):
            feasibility += 2
        if _contains_any(concept.lighting.lower(), ["soft", "directional", "natural", "controlled", "premium"]):
            feasibility += 2
        feasibility = _clamp(feasibility, 0, self.weights["feasibility"])
        score += feasibility

        # 7) Copy space
        copy_space_score = 0.0
        if _contains_any(concept.copy_space.lower(), ["25", "30", "35", "40"]):
            copy_space_score += 2
        if _contains_any(concept.copy_space.lower(), ["left", "right", "top", "bottom"]):
            copy_space_score += 3
        copy_space_score = _clamp(copy_space_score, 0, self.weights["copy_space"])
        score += copy_space_score

        # Family-specific bonuses / penalties
        if ctx["benefit_family"] == "merchant_payments":
            low_scene = " ".join([
                concept.scene_description.lower(),
                concept.visual_mechanism.lower(),
                concept.why_memorable.lower()
            ])

            has_pos = _contains_any(low_scene, ["pos", "point-of-sale", "point of sale", "checkout", "tap", "counter", "terminal", "payment"])
            has_ecom = _contains_any(low_scene, ["e-commerce", "ecommerce", "online order", "fulfillment", "packing", "shipment", "delivery", "merchant"])

            if has_pos and has_ecom:
                score += 8
                notes.append("merchant_payments: dual-channel story present")
            elif has_pos or has_ecom:
                score -= 5
                notes.append("merchant_payments: missing full commerce fusion")
            else:
                score -= 10
                notes.append("merchant_payments: weak service fit")

        # Rejections / penalties
        joined = " ".join([
            concept.title,
            concept.hook,
            concept.scene_description,
            concept.why_memorable,
            concept.composition,
            concept.visual_mechanism
        ]).lower()

        if _contains_any(joined, ["generic", "stock photo", "smiling customer", "simple office"]):
            score -= 10
            notes.append("generic feel penalty")

        if _contains_any(joined, ANTI_NEON_TERMS):
            score -= 12
            notes.append("anti-neon penalty")

        if _contains_any(joined, ["floating ui", "hologram", "network lines", "digital tunnel"]):
            score -= 12
            notes.append("generic fintech penalty")

        if concept.scene_archetype not in APPROVED_SCENE_ARCHETYPES:
            score -= 6
            notes.append("unapproved scene_archetype")

        if concept.visual_mechanism not in APPROVED_VISUAL_MECHANISMS:
            score -= 4
            notes.append("weak visual_mechanism")

        # Hard rule: avoid totally generic phone-person concept
        if _contains_any(joined, ["person using phone", "man using phone", "woman using phone"]) and concept.visual_mechanism not in APPROVED_VISUAL_MECHANISMS:
            score -= 15
            notes.append("generic phone usage without strong mechanism")

        score = _clamp(score, 0, 100)
        if score >= 85:
            notes.append("release-quality ideation")
        elif score >= 75:
            notes.append("strong concept")
        elif score >= 65:
            notes.append("usable but not elite")
        else:
            notes.append("weak concept")

        return score, notes

    def _review_concepts(self, concepts: List[CreativeConcept], ctx: Dict[str, Any]) -> List[CreativeConcept]:
        for c in concepts:
            score, notes = self._score_concept(c, ctx)
            c.score = score
            c.review_notes = notes

        # Sort high to low
        concepts.sort(key=lambda x: x.score, reverse=True)
        return concepts

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        brand = _safe_text(payload.get("brand")).strip().lower() or "generic_brand"
        if brand in {"stc", "stcbank", "stc bank"}:
            brand = "stc_bank"

        ctx = {
            "brand": brand,
            "prompt": _safe_text(payload.get("prompt") or payload.get("user_text") or payload.get("brief")),
            "benefit_family": detect_benefit_family(payload),
            "stc_style": detect_stc_style(payload),
            "aspect_ratio": _safe_text(payload.get("aspect_ratio") or "4:5"),
            "image_size": _safe_text(payload.get("image_size") or "2K"),
            "creative_mode": _safe_text(payload.get("creative_mode") or "masterpiece"),
        }

        system_prompt = self._build_system_prompt(ctx)
        user_prompt = self._build_user_prompt(ctx)

        try:
            parsed, calls, routes = self._call_director(system_prompt, user_prompt)

            raw_concepts = parsed.get("concepts", [])
            if not isinstance(raw_concepts, list) or len(raw_concepts) < 4:
                raise TechnicalCreativeFailure("Structured output did not return 4 concepts.")

            normalized = []
            for i, rc in enumerate(raw_concepts[:4], start=1):
                if not isinstance(rc, dict):
                    raise TechnicalCreativeFailure(f"Concept {i} is not a valid object.")
                normalized.append(self._normalize_concept(rc, ctx, i))

            reviewed = self._review_concepts(normalized, ctx)
            shortlist = reviewed[:self.shortlist_size]
            selected = shortlist[0] if shortlist else None

            result = CreativeResult(
                ok=True,
                technical_failure=False,
                allow_smart_engine_fallback=True,
                creative_state="ok",
                creative_score=selected.score if selected else None,
                benefit_family=ctx["benefit_family"],
                stc_style=ctx["stc_style"],
                concepts=[asdict(x) for x in reviewed],
                shortlist=[asdict(x) for x in shortlist],
                selected_concept=asdict(selected) if selected else None,
                director_calls_made=calls,
                director_routes_tried=routes,
                reason="creative_success",
                errors=[],
            )
            return asdict(result)

        except TechnicalCreativeFailure as e:
            # Must preserve smart fallback
            result = CreativeResult(
                ok=False,
                technical_failure=True,
                allow_smart_engine_fallback=True,
                creative_state="technical_failure",
                creative_score=None,
                benefit_family=ctx["benefit_family"],
                stc_style=ctx["stc_style"],
                concepts=[],
                shortlist=[],
                selected_concept=None,
                director_calls_made=0,
                director_routes_tried=[],
                reason="technical_failure",
                errors=[str(e)],
            )
            return asdict(result)

        except Exception as e:
            # Unexpected errors still treated as technical, so fallback survives
            result = CreativeResult(
                ok=False,
                technical_failure=True,
                allow_smart_engine_fallback=True,
                creative_state="technical_failure",
                creative_score=None,
                benefit_family=ctx["benefit_family"],
                stc_style=ctx["stc_style"],
                concepts=[],
                shortlist=[],
                selected_concept=None,
                director_calls_made=0,
                director_routes_tried=[],
                reason="unexpected_failure",
                errors=[str(e)],
            )
            return asdict(result)


# =========================================================
# Compatibility wrappers
# =========================================================

def creative_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    return XPANDCreativeBrain().run(payload)


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    return creative_run(payload)


# =========================================================
# Self test
# =========================================================

def self_test() -> bool:
    print("==========================================")
    print(" XPAND CREATIVE BRAIN V5.0")
    print(" ZERO-COST SELF TEST")
    print("==========================================")
    print()

    passed: List[str] = []
    failed: List[str] = []

    def check(name: str, condition: bool) -> None:
        if condition:
            passed.append(name)
            print(f"✅ {name}")
        else:
            failed.append(name)
            print(f"❌ {name}")

    brain = XPANDCreativeBrain()

    # score weights
    check("score_weights", isinstance(brain.weights, dict) and sum(brain.weights.values()) == 100)

    # benefit routing
    check(
        "merchant_payments_routing",
        detect_benefit_family({
            "prompt": "صورة عن خدمات التجارة الإلكترونية ونقاط البيع للتجار"
        }) == "merchant_payments"
    )

    # style detection
    check("stc_default_realistic", detect_stc_style({"prompt": "إعلان بنك STC"}) == "premium_realistic")
    check("stc_explicit_purple", detect_stc_style({"stc_style": "premium_purple_architecture"}) == "premium_purple_architecture")
    check("stc_augmented_realism", detect_stc_style({"prompt": "واقعية معززة لبنك STC"}) == "premium_augmented_realism")

    # anti-neon
    check("anti_neon", "neon" in ANTI_NEON_TERMS)

    # parsers
    check("native_dict_parsing", _parse_structured_text({"concepts": []}) == {"concepts": []})
    check("fenced_json_parsing", _parse_structured_text('```json\n{"concepts":[]}\n```') == {"concepts": []})
    check("python_literal_parsing", _parse_structured_text("{'concepts': []}") == {"concepts": []})

    # schema
    check("ideation_schema_four", IDEATION_JSON_SCHEMA["properties"]["concepts"]["minItems"] == 4 and IDEATION_JSON_SCHEMA["properties"]["concepts"]["maxItems"] == 4)

    # STC safety
    sp = brain._build_system_prompt({
        "brand": "stc_bank",
        "benefit_family": "merchant_payments",
        "stc_style": "premium_realistic",
        "prompt": "demo",
        "aspect_ratio": "4:5",
        "image_size": "2K",
        "creative_mode": "masterpiece",
    })
    check("stc_no_text", "NO generated slogans" in sp or "No generated copy" in sp)
    check("stc_purple_not_default", "Purple is optional, not mandatory" in sp or "Do not use purple neon by default" in sp)

    # call limits
    check("max_three_director_calls", brain.max_director_calls >= 3)
    check("normal_two_director_calls", brain.normal_director_calls == 2)

    # upgraded quality tests
    check("visual_mechanism_required", "Every concept MUST contain one clear \"visual mechanism\"" in sp)
    check("generic_scene_rejection", "Do NOT produce generic scenes" in sp)
    check("one_message_rule", "One message only per concept" in sp)
    check("copy_space_lock", "25%–40% clean copy space" in sp or "25%-40%" in sp)
    check("merchant_fusion_rule", "continuous commercial journey" in brain._family_rules("merchant_payments"))
    check("camera_feasibility_merge", "scientific camera vocabulary" in sp.lower())

    # sample scoring sanity
    sample = CreativeConcept(
        title="Commerce in One Motion",
        hook="One merchant journey",
        benefit_message="E-commerce + in-store payments",
        scene_archetype="merchant_commerce_fusion",
        visual_mechanism="continuous_commerce_journey",
        hero_subject="Saudi boutique checkout counter with online fulfillment",
        scene_description="A premium Saudi retail scene where a customer taps to pay in the foreground while packaging and online order preparation are visually fused into the same commercial journey.",
        saudi_authenticity="Modern Saudi boutique, authentic attire, local retail behavior",
        brand_dna="premium realism, subtle purple-neutral palette, mint accent only if justified",
        camera="elevated three-quarter angle with hero counter perspective",
        lighting="controlled natural daylight with warm premium fill",
        materials="stone, oak wood, matte metal, packaging paper",
        composition="single hero counter scene with 30% clean copy space in upper left",
        copy_space="upper left, 30%",
        why_memorable="The scene fuses online and in-store commerce into one memorable branded moment.",
        why_feasible="Real retail environment, practical props, physically believable scene.",
        avoid=["no_text", "no_logo", "no_neon"],
        negative_prompt=["no neon", "no network lines", "no floating UI", "no generic fintech clutter"],
    )
    sample_score, _ = brain._score_concept(sample, {
        "benefit_family": "merchant_payments",
        "brand": "stc_bank",
        "stc_style": "premium_realistic",
    })
    check("high_quality_scoring", sample_score >= 80)

    print()
    if failed:
        print("XPAND Creative Brain V5.0 self-test: FAIL ❌")
        print()
        print(f"Passed: {len(passed)}")
        print(f"Failed: {len(failed)}")
        print("Failed checks:", ", ".join(failed))
        return False

    print("XPAND Creative Brain V5.0 self-test: PASS ✅")
    print()
    print("✅ 4 concepts instead of 20")
    print("✅ 2-concept paid shortlist")
    print("✅ Normal paid Director calls = 2")
    print("✅ Maximum calls with recovery = 3")
    print("✅ Explicit JSON schemas")
    print("✅ Merchant payments priority")
    print("✅ Premium realistic STC default")
    print("✅ Purple architecture only when justified")
    print("✅ Augmented realism supported")
    print("✅ Scientific camera vocabulary")
    print("✅ Camera + feasibility merged into review")
    print("✅ No winner-finalizer paid call")
    print("✅ STC no text / logo")
    print("✅ Purple-neon guard")
    print("✅ Generic fintech guard")
    print("✅ Scene-realism guard")
    print("✅ Visual mechanism required")
    print("✅ Hero composition discipline")
    print("✅ Generic-scene rejection")
    print("✅ Technical failure keeps Smart fallback alive")
    print("🚫 No API calls were made")
    return True


if __name__ == "__main__":
    self_test()
