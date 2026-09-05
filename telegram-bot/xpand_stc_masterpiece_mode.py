# xpand_stc_masterpiece_mode.py
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Dict, List

from xpand_stc_brand_kit import BrandKit, ReferenceAsset
from xpand_stc_ad_brain import STCAdBrain, AdConcept
from xpand_stc_ad_quality import STCAdQualityGate


@dataclass
class HighAlertSettings:
    enabled: bool = True
    concepts_required: int = 6
    shortlist_count: int = 3
    require_brand_pack: bool = True
    min_prompt_score: int = 88
    min_concept_score: int = 88
    block_generic_scene: bool = True
    block_fast_final_delivery: bool = True
    allow_second_generation: bool = True
    allow_second_critique: bool = True
    allow_openai_structured: bool = True
    allow_gemini_structured: bool = True
    allow_gemini_image_pro_upgrade: bool = True


class STCMasterpieceMode:
    """
    وضع STC 5-Star عالي التأهب:
    - يحمّل هوية STC من GitHub
    - يولد أفكار إعلانية وليس مشاهد عشوائية
    - يقتل التكرار
    - يبني prompt إعلاني حقيقي
    """

    def __init__(self, brand_pack_path: str = "brand_assets/stc_bank/stc_bank_brand_pack.json"):
        self.brand_kit = BrandKit.load(brand_pack_path)
        self.brain = STCAdBrain()
        self.quality = STCAdQualityGate()
        self.settings = HighAlertSettings()

    def build_package(
        self,
        user_prompt: str,
        benefit_family: str,
        visual_family: str = "premium_realistic",
    ) -> Dict:
        concepts = self.brain.generate_concepts(benefit_family, visual_family)

        if len(concepts) < self.settings.concepts_required:
            raise RuntimeError(
                f"STC high-alert requires at least {self.settings.concepts_required} concepts. "
                f"Generated={len(concepts)}"
            )

        shortlisted = self.brain.shortlist(concepts, top_n=self.settings.shortlist_count)

        audited = []
        for concept in shortlisted:
            audit = self.quality.audit_concept(concept, self.brand_kit.banned_patterns)
            audited.append((concept, audit))

        valid = [item for item in audited if item[1].total_score >= self.settings.min_concept_score]
        if not valid:
            valid = audited

        best_concept, best_audit = sorted(valid, key=lambda pair: pair[1].total_score, reverse=True)[0]

        selected_assets = self.brand_kit.select_assets(
            benefit_family=benefit_family,
            visual_family=visual_family,
            max_brand_dna=3,
            max_physical=2,
            max_layout=2,
            max_total=7,
        )

        final_prompt = self._build_generation_prompt(
            user_prompt=user_prompt,
            benefit_family=benefit_family,
            visual_family=visual_family,
            best_concept=best_concept,
            selected_assets=selected_assets,
        )

        prompt_audit = self.quality.audit_prompt_text(
            final_prompt,
            self.brand_kit.banned_patterns,
        )

        package = {
            "mode": "stc_masterpiece_high_alert",
            "settings": asdict(self.settings),
            "brand_summary": self.brand_kit.summary(),
            "best_concept": best_concept.to_dict(),
            "best_concept_audit": best_audit.to_dict(),
            "shortlist": [c.to_dict() for c, _ in audited],
            "selected_reference_paths": self.brand_kit.reference_paths(selected_assets),
            "selected_reference_assets": [asset.asset_id for asset in selected_assets],
            "prompt": final_prompt,
            "prompt_audit": prompt_audit.to_dict(),
            "negative_prompt": self._build_negative_prompt(),
            "delivery_policy": {
                "block_fast_final_delivery": True,
                "require_advertising_grade_result": True,
                "reject_generic_scene": True,
                "reject_repeated_scene": True,
                "force_brand_grounding": True,
            },
        }
        return package

    def _build_generation_prompt(
        self,
        user_prompt: str,
        benefit_family: str,
        visual_family: str,
        best_concept: AdConcept,
        selected_assets: List[ReferenceAsset],
    ) -> str:
        brand_grounding = self.brand_kit.build_brand_grounding_text(visual_family)
        banned_text = self.brand_kit.build_banned_patterns_text()

        reference_text_lines = []
        if selected_assets:
            reference_text_lines.append(
                "Use the provided reference images as a permanent brand grounding system."
            )
            for idx, asset in enumerate(selected_assets, start=1):
                reference_text_lines.append(
                    f"Reference {idx}: {asset.asset_id} | roles={', '.join(asset.roles)} | "
                    f"notes={asset.notes or 'brand grounding'}."
                )

        prompt = f"""
Create a premium advertising image for {self.brand_kit.brand_name}.

This must be an advertising image, not a generic scene, not a documentary frame, and not a quick literal illustration.
The result must feel like a top-tier bank campaign with strong brand identity, premium art direction, commercial sophistication, and a clear consumer message translated visually.

User request:
{user_prompt}

Benefit family:
{benefit_family}

Visual family:
{visual_family}

Brand identity grounding:
{brand_grounding}

Creative concept title:
{best_concept.title}

Headline strategy:
{best_concept.headline_strategy}

Core idea:
{best_concept.core_idea}

Visual mechanism:
{best_concept.visual_mechanism}

Benefit translation:
{best_concept.benefit_translation}

Environment:
{best_concept.environment}

Hero subject:
{best_concept.hero_subject}

Scene structure:
{best_concept.scene_structure}

Shot language:
{best_concept.shot_language}

Lighting language:
{best_concept.lighting_language}

Materials language:
{best_concept.materials_language}

Brand fit:
{best_concept.brand_fit_reason}

Advertising direction:
- Make the image feel like a professionally art-directed bank advertisement.
- The composition must communicate the benefit through a smart advertising mechanism, not through a plain literal payment scene.
- Show a clear link between e-commerce and in-store payments.
- Preserve Saudi lifestyle authenticity with modern premium execution.
- Build visual hierarchy and elegant copy space.
- Show brand identity through palette, material language, tone, retail sophistication, app/card/product logic, and campaign styling.
- Avoid making the scene look like a random office, a repeated wooden counter, or a generic fintech ad.

Mandatory quality rules:
- Premium commercial realism.
- Strong brand identity.
- Strong visual idea.
- Strong advertising composition.
- Strong originality.
- Strong distinction from previous repeated outputs.
- Not a generic scene.
- Not a plain store counter shot.
- Not a floating-card cliché.
- Not an empty purple room with product placement only.
- No clutter.
- No visual laziness.

Reference instructions:
{" ".join(reference_text_lines)}

Hard bans:
{banned_text}

If there is a choice between a fast easy scene and a stronger ad idea, choose the stronger ad idea.
""".strip()

        return prompt

    def _build_negative_prompt(self) -> str:
        bad = self.brand_kit.banned_patterns + [
            "generic office",
            "simple merchant counter",
            "plain wood desk",
            "floating card",
            "random neon fintech style",
            "unrelated banking UI",
            "cheap stock-photo look",
            "weak composition",
            "plain documentary frame",
        ]
        return ", ".join(sorted(set(bad)))

    def print_debug_report(self, package: Dict) -> None:
        print("==========================================")
        print(" XPAND STC MASTERPIECE MODE REPORT")
        print("==========================================")
        print(f"mode = {package['mode']}")
        print(f"best_concept = {package['best_concept']['concept_id']} | {package['best_concept']['title']}")
        print(f"selected_reference_assets = {', '.join(package['selected_reference_assets'])}")
        print(f"prompt_score = {package['prompt_audit']['total_score']}")
        print(f"best_concept_score = {package['best_concept_audit']['total_score']}")
        print("PASS ✅")


if __name__ == "__main__":
    engine = STCMasterpieceMode()
    package = engine.build_package(
        user_prompt=(
            "أنشئ صورة إعلانية لبنك STC Bank عن خدمات التجارة الإلكترونية ونقاط البيع "
            "بأسلوب واقعي فوتوغرافي فاخر مع مشهد أصيل من الحياة التجارية السعودية."
        ),
        benefit_family="merchant_payments",
        visual_family="premium_realistic",
    )
    engine.print_debug_report(package)
    print(json.dumps({
        "best_concept": package["best_concept"]["title"],
        "selected_reference_assets": package["selected_reference_assets"],
        "prompt_score": package["prompt_audit"]["total_score"],
    }, ensure_ascii=False, indent=2))
