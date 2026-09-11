"""Canonical on-disk STC direction loaded by the running workers. No API calls."""
import json
import re
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

def master_system_prompt():
    return read_skill_file("references/stc-bank-master-system-prompt-v1.md")

def creative_first_system_prompt():
    return read_skill_file("references/stc-bank-creative-first-v2.md")

def non_literal_concept_gate():
    return read_skill_file("references/non-literal-concept-gate-mandatory.md")

def prompt_engineering_direction():
    return read_skill_file("references/prompt-engineering.md")

def camera_finish_direction():
    return read_skill_file("references/camera-light-material-atlas.md")

def style_direction(style):
    name = STYLE_FILES.get(style)
    return read_skill_file("references/" + name) if name else ""

def reference_observations(style):
    canonical = {"purple_architectural": "premium_purple_architecture",
                 "augmented_realism": "premium_augmented_realism"}.get(style, style)
    rows = json.loads(read_skill_file("references/reference-atlas.json"))
    matches = [row for row in rows if row["family"] == canonical]
    # Avoid teaching a new service through four near-identical card ads.
    selected = [matches[i] for i in sorted({0, len(matches)//2, len(matches)-1})] if matches else []
    return "Visual-language observations only; do not inherit the reference's product or service. " \
        "No reference image is attached to the returned standalone prompt.\n" + "\n".join(
        row["observed_camera"] + ": " + row["observations"] for row in selected)

def clean_public_prompt(value):
    """Remove repository reference identifiers from a portable user prompt."""
    text = str(value or "").strip()
    ref = r"(?:local_stc:)?stc_(?:curated|purple|realistic|augmented|merchant|dna)_\d+(?:\.jpe?g)?"
    text = re.sub(r"(?:inspired by|based on|referencing|matching|as in)\s+" + ref, "", text, flags=re.I)
    text = re.sub(ref, "", text, flags=re.I)
    text = re.sub(r"[ \t]+([,.;])", r"\1", text)
    text = re.sub(r"[,;]\s*[,;]", ",", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()

def stc_execution_order():
    return """MANDATORY STC EXECUTION ORDER
1. Extract concept DNA and run the Concept Mutation Lab before final prompt writing.
2. Generate materially different mutations; do not polish the first acceptable idea.
3. Translate the selected mutation into one photographable advertising scene.
4. Run the Strict Visual Output Guard before generation and again after generation.
5. The image contains the scene only: no readable text, logos, UI or design-instruction labels.
""".strip()

def concept_mutation_lab_prompt():
    return read_skill_file("references/stc-bank-concept-mutation-lab.md")

def strict_visual_output_guard_prompt():
    return read_skill_file("references/stc-bank-strict-visual-output-ad-quality-guard.md")

def prompt_direction(style):
    return "\n\n".join(filter(None, [stc_execution_order(), concept_mutation_lab_prompt(), core_direction(), style_direction(style), reference_observations(style),
        read_skill_file("references/concept-workflow.md"),
        read_skill_file("references/reference-campaign-grammar.md"),
        read_skill_file("references/prompt-specification.md"),
        read_skill_file("references/visual-language.md"),
        read_skill_file("references/creative-concept-execution-intelligence.md"),
        master_system_prompt(),
        creative_first_system_prompt(),
        prompt_engineering_direction(),
        camera_finish_direction(),
        read_skill_file("references/effects-and-finish.md"),
        strict_visual_output_guard_prompt()]))
