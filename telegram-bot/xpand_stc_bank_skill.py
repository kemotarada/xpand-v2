"""Loads the user-approved STC Bank Hyper Visual Direction System for every image path."""

from __future__ import annotations

from pathlib import Path


STC_BANK_MARKERS = (
    "stc bank",
    "stcbank",
    "بنك stc",
    "اس تي سي بنك",
    "stc بنك",
    "stcbank_ksa",
)


def is_stc_bank_request(value: object) -> bool:
    text = str(value or "").lower()
    return any(marker in text for marker in STC_BANK_MARKERS)


_PROMPT_PATH = (
    Path(__file__).resolve().parent
    / "agents"
    / "xpand"
    / "stc_bank_system_prompt.md"
)


def load_stc_bank_system_prompt() -> str:
    try:
        value = _PROMPT_PATH.read_text(encoding="utf-8").strip()
        if value:
            return value
    except Exception:
        pass

    return (
        "Use the STC Bank Hyper Visual Direction System. "
        "Generate a clean photorealistic key visual with 25–40% natural "
        "negative space. Never render text, letters, numbers, logos, UI, "
        "watermarks, decorative graphics, particles or connection lines. "
        "Strict color tiers: Tier A = 100% natural (no environment purple), "
        "Tier B = natural base + ≤15% edge purple, Tier C = purple backdrop only. "
        "Never apply global purple cast on skin or natural materials. "
        "Use saved references as visual DNA without copying their ideas. "
        "Spend maximum effort. Quality over speed."
    )


STC_BANK_VISUAL_SKILL = load_stc_bank_system_prompt()
STC_BANK_IMAGE_GUARD = STC_BANK_VISUAL_SKILL
