# =========================================================
# XPAND BRAND RESEARCH V1.0
#
# Purpose:
# - Detect branded visual requests
# - Activate deep research mode for STC Bank
# - Search official + inspiration sources when available
# - Build a strong researched image prompt before generation
#
# No extra dependencies required besides requests.
# =========================================================

from __future__ import annotations

import os
import re
import requests

from typing import Any, Dict, List, Optional


TAVILY_API_KEY = str(
    os.environ.get(
        "TAVILY_API_KEY",
        ""
    )
).strip()


TAVILY_SEARCH_URL = "https://api.tavily.com/search"


STC_INSTAGRAM_URL = "https://www.instagram.com/stcbank_ksa/"


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value: Any,
    max_length: int = 12000
) -> str:

    return (
        str(value if value is not None else "")
        .replace("\x00", "")
        .strip()[:max_length]
    )


def normalize_arabic(
    value: Any
) -> str:

    text = clean_text(
        value,
        20000
    ).lower()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(
        r"[\u064B-\u065F]",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def contains_any(
    text: str,
    markers: List[str]
) -> bool:

    source = normalize_arabic(text)

    return any(
        normalize_arabic(marker) in source
        for marker in markers
    )


# =========================================================
# IMAGE INTENT
# =========================================================

VISUAL_MARKERS = [
    "صوره",
    "صورة",
    "صور",
    "اعلان",
    "إعلان",
    "بوستر",
    "بانر",
    "مشهد",
    "post",
    "poster",
    "banner",
    "ad",
    "advertisement",
    "visual",
    "key visual",
    "campaign",
    "design",
    "صمم",
    "اعمللي",
    "اعمل لي",
    "سويلي",
    "سوي لي",
    "create",
    "generate",
    "image",
    "scene",
]


def looks_like_visual_request(
    text: str
) -> bool:

    return contains_any(
        text,
        VISUAL_MARKERS
    )


# =========================================================
# BRAND DETECTION
# =========================================================

def detect_brand(
    prompt: str
) -> str:

    if contains_any(
        prompt,
        [
            "stc bank",
            "بنك stc",
            "stcbank",
            "stcbank_ksa",
            "stc",
        ]
    ):
        return "stc_bank"

    return ""


def should_apply_deep_research(
    prompt: str
) -> bool:

    brand = detect_brand(prompt)

    if not brand:
        return False

    if not looks_like_visual_request(prompt):
        return False

    return True


# =========================================================
# BRAND PROFILES
# =========================================================

BRAND_PROFILES: Dict[str, Dict[str, Any]] = {
    "stc_bank": {
        "brand_label": "STC Bank KSA",
        "official_sources": [
            STC_INSTAGRAM_URL,
        ],
        "default_mode": "best",
        "default_ratio": "4:5",
        "default_resolution": "4K",
        "visual_dna": [
            "Deep STC purple as the leading brand color.",
            "Mint / turquoise green as secondary accent color.",
            "White typography and clean modern layout blocks.",
            "Premium modern banking / fintech visual language.",
            "Cinematic but clean commercial lighting.",
            "Modern Saudi / Gulf lifestyle settings.",
            "Airport, travel, car interior, lounge, city-night, and premium indoor scenes.",
            "Confident human subjects, polished styling, premium presentation.",
            "Bold Arabic headline hierarchy with short supporting copy.",
            "Strong service-led visuals: cards, money transfer, iban, travel payment, digital banking.",
            "Clean negative space and strong CTA treatment.",
            "Modern realistic image quality with commercial-grade finish.",
        ],
        "photography_rules": [
            "Prefer hero-shot or cinematic ad composition.",
            "Use premium lens feeling and realistic perspective.",
            "Use believable skin, fabric, metal, plastic and glass rendering.",
            "Use refined reflections, depth, and controlled shadows.",
            "No cheap generic corporate look.",
            "No random clutter.",
            "No distorted hands or malformed products.",
        ],
        "creative_positioning": [
            "premium",
            "smart",
            "clean",
            "trustworthy",
            "modern",
            "confident",
            "Saudi / Gulf relevant",
            "banking + fintech + lifestyle",
        ],
        "inspiration_domains": [
            "instagram.com",
            "pinterest.com",
            "behance.net",
            "dribbble.com",
            "midjourney.com",
            "adsoftheworld.com",
        ],
        "research_queries": [
            "STC Bank KSA Instagram campaign visual design",
            "STC Bank KSA advertising poster",
            "STC Bank KSA travel card campaign",
            "Saudi fintech banking premium advertisement",
            "banking app luxury campaign Saudi Arabia",
            "premium digital banking poster Arabic",
            "Pinterest STC Bank style banking ad",
            "Behance banking campaign Arabic premium",
            "Dribbble fintech card campaign purple green",
            "Midjourney premium banking scene luxury lighting",
        ],
    }
}


# =========================================================
# WEB SEARCH
# =========================================================

def run_tavily_search(
    query: str,
    include_domains: Optional[List[str]] = None,
    max_results: int = 5
) -> List[Dict[str, Any]]:

    if not TAVILY_API_KEY:
        return []

    payload: Dict[str, Any] = {
        "api_key": TAVILY_API_KEY,
        "query": clean_text(query, 1000),
        "search_depth": "advanced",
        "max_results": max(1, min(max_results, 10)),
        "include_answer": False,
        "include_raw_content": False,
    }

    if include_domains:
        payload["include_domains"] = include_domains

    try:
        response = requests.post(
            TAVILY_SEARCH_URL,
            json=payload,
            timeout=45
        )
    except Exception:
        return []

    if not response.ok:
        return []

    try:
        data = response.json()
    except Exception:
        return []

    results = data.get("results", [])
    if not isinstance(results, list):
        return []

    cleaned: List[Dict[str, Any]] = []

    for item in results:
        if not isinstance(item, dict):
            continue

        cleaned.append(
            {
                "title": clean_text(item.get("title", ""), 300),
                "url": clean_text(item.get("url", ""), 500),
                "content": clean_text(item.get("content", ""), 1000),
            }
        )

    return cleaned


# =========================================================
# RESEARCH COLLECTION
# =========================================================

def collect_brand_research(
    brand_id: str,
    user_prompt: str
) -> Dict[str, Any]:

    profile = BRAND_PROFILES.get(brand_id, {})
    if not profile:
        return {
            "results": [],
            "sources_used": [],
        }

    queries = profile.get("research_queries", [])
    inspiration_domains = profile.get("inspiration_domains", [])

    collected_results: List[Dict[str, Any]] = []
    sources_used: List[str] = []

    if not TAVILY_API_KEY:
        return {
            "results": [],
            "sources_used": [],
        }

    # 1) official leaning query
    official_query = (
        f"{profile.get('brand_label', brand_id)} official Instagram visual style "
        f"{user_prompt}"
    )

    official_results = run_tavily_search(
        official_query,
        include_domains=["instagram.com"],
        max_results=4
    )

    if official_results:
        collected_results.extend(official_results)
        sources_used.extend(
            [item.get("url", "") for item in official_results if item.get("url")]
        )

    # 2) broader inspiration
    for query in queries[:6]:
        results = run_tavily_search(
            query,
            include_domains=inspiration_domains,
            max_results=3
        )

        if results:
            collected_results.extend(results)
            sources_used.extend(
                [item.get("url", "") for item in results if item.get("url")]
            )

    # dedupe urls
    unique_sources: List[str] = []
    seen = set()

    for url in sources_used:
        if not url or url in seen:
            continue
        seen.add(url)
        unique_sources.append(url)

    return {
        "results": collected_results[:20],
        "sources_used": unique_sources[:20],
    }


# =========================================================
# SUMMARIZATION
# =========================================================

def build_default_brand_brief(
    brand_id: str
) -> str:

    profile = BRAND_PROFILES.get(brand_id, {})
    if not profile:
        return ""

    visual_dna = profile.get("visual_dna", [])
    photography_rules = profile.get("photography_rules", [])
    positioning = profile.get("creative_positioning", [])

    lines: List[str] = []

    lines.append(
        f"Brand: {profile.get('brand_label', brand_id)}"
    )

    lines.append(
        f"Default style target: {', '.join(positioning)}"
    )

    lines.append("Visual DNA:")
    for item in visual_dna:
        lines.append(f"- {item}")

    lines.append("Photography / ad-direction rules:")
    for item in photography_rules:
        lines.append(f"- {item}")

    return "\n".join(lines)


def summarize_search_results(
    results: List[Dict[str, Any]],
    max_items: int = 8
) -> str:

    if not results:
        return "No live web-search summary available. Use the default STC Bank brand profile and official-source-first creative behavior."

    lines: List[str] = []
    count = 0

    for item in results:
        if count >= max_items:
            break

        title = clean_text(item.get("title", ""), 220)
        content = clean_text(item.get("content", ""), 420)

        if not title and not content:
            continue

        lines.append(f"- {title}: {content}")
        count += 1

    if not lines:
        return "No usable search snippets found. Use the default STC Bank brand profile."

    return "\n".join(lines)


# =========================================================
# PROMPT BUILDING
# =========================================================

def build_researched_prompt(
    user_prompt: str
) -> Dict[str, Any]:

    prompt = clean_text(user_prompt, 10000)

    brand_id = detect_brand(prompt)

    if not brand_id:
        return {
            "applied": False,
            "brand_id": "",
            "brand_label": "",
            "mode_override": "",
            "final_prompt": prompt,
            "research_summary": "",
            "sources_used": [],
        }

    profile = BRAND_PROFILES.get(brand_id, {})
    if not profile:
        return {
            "applied": False,
            "brand_id": "",
            "brand_label": "",
            "mode_override": "",
            "final_prompt": prompt,
            "research_summary": "",
            "sources_used": [],
        }

    live_research = collect_brand_research(
        brand_id,
        prompt
    )

    default_brief = build_default_brand_brief(
        brand_id
    )

    live_summary = summarize_search_results(
        live_research.get("results", [])
    )

    final_prompt = f"""
USER REQUEST:
{prompt}

XPAND BRAND RESEARCH MODE:
Deep brand-research mode is active for STC Bank KSA.

OFFICIAL SOURCE PRIORITY:
- Instagram official page: {STC_INSTAGRAM_URL}
- Prefer official brand language first.
- If the official page or any source is not fully accessible, do not fake access. Use indexed/public references and the brand profile below.

BRAND PROFILE:
{default_brief}

PUBLIC RESEARCH SNAPSHOTS:
{live_summary}

CREATIVE EXECUTION RULES:
- This is NOT a generic image request.
- Treat this as a premium STC Bank advertising production.
- Preserve the exact marketing intent of the user request.
- Translate the idea into a stronger visual concept if needed.
- Use professional art direction, premium commercial realism, strong visual hierarchy, realistic materials, believable lighting, and refined composition.
- Match STC Bank visual language as closely as possible in spirit, tone, color logic, and campaign quality.
- Use Saudi / Gulf-appropriate styling where people appear.
- Prefer a clean ad-campaign look, not a random AI-art look.
- The output must look like a top-tier agency campaign.
- Strong camera angle, premium background, premium lighting, and clear subject focus are mandatory.
- Avoid clutter, malformed anatomy, fake watermarks, random text, and visual noise.
- Do not directly copy a single existing ad.
- Learn from the brand language and elevate it.

OUTPUT TARGET:
- Premium advertising visual
- Commercial realism
- High-end campaign quality
- 4K intent
- Best possible execution
- If text is requested, render it clearly and accurately
- If the user did not specify ratio, prefer 4:5 for ad/poster requests

FINAL TASK:
Generate the strongest possible final advertising image for this request while staying aligned with STC Bank KSA brand language.
""".strip()

    return {
        "applied": True,
        "brand_id": brand_id,
        "brand_label": profile.get("brand_label", brand_id),
        "mode_override": profile.get("default_mode", "best"),
        "final_prompt": final_prompt,
        "research_summary": live_summary,
        "sources_used": live_research.get("sources_used", []),
    }


# =========================================================
# SELF TEST
# =========================================================

if __name__ == "__main__":

    test_prompt = "اعمللي بوستر فاخر لبنك stc عن السفر والدفع الدولي"

    result = build_researched_prompt(test_prompt)

    print("")
    print("==========================================")
    print(" XPAND BRAND RESEARCH V1.0")
    print("==========================================")
    print("")
    print("Applied:", result["applied"])
    print("Brand:", result["brand_label"])
    print("Mode override:", result["mode_override"])
    print("Sources used:", len(result["sources_used"]))
    print("")
    print(result["final_prompt"][:3000])
    print("")
