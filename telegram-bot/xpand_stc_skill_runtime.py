"""Canonical on-disk STC direction loaded by the running workers. No API calls."""
import json
from pathlib import Path
from functools import lru_cache

SKILL_ROOT = Path(__file__).resolve().parent / "agents/xpand/skills/stc-bank-visual-director"
STYLE_FILES = {
    "premium_realistic": "premium-realistic.md",
    "purple_architectural": "purple-studio.md",
    "premium_purple_architecture": "purple-studio.md",
    "augmented_realism": "augmented-realism.md",
    "premium_augmented_realism": "augmented-realism.md",
}
@lru_cache(maxsize=16)
def read_skill_file(name):
    # Only internal names are used. Missing deployment files must be visible.
    path = SKILL_ROOT / name
    if not path.is_file():
        raise RuntimeError("Missing STC runtime skill resource: " + name)
    return path.read_text(encoding="utf-8").strip()

def core_direction():
    return read_skill_file("SKILL.md")

def style_direction(style):
    name = STYLE_FILES.get(style)
    return read_skill_file("references/" + name) if name else ""

def reference_observations(style):
    canonical = {"purple_architectural": "premium_purple_architecture",
                 "augmented_realism": "premium_augmented_realism"}.get(style, style)
    rows = json.loads(read_skill_file("references/reference-atlas.json"))
    matches = [row for row in rows if row["family"] == canonical]
    return "Curated visual observations (not a claim of live vision):\n" + "\n".join(
        row["asset_id"] + ": " + row["observed_camera"] + ". " + row["observations"]
        for row in matches[:4])

def prompt_direction(style):
    return "\n\n".join(filter(None, [core_direction(), style_direction(style), reference_observations(style),
        read_skill_file("references/prompt-specification.md"),
        read_skill_file("references/visual-language.md"),
        read_skill_file("references/effects-and-finish.md")]))
