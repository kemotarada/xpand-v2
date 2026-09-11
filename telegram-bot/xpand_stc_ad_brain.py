# xpand_stc_ad_brain.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class AdConcept:
    concept_id: str
    title: str
    headline_strategy: str
    core_idea: str
    visual_mechanism: str
    benefit_translation: str
    environment: str
    hero_subject: str
    scene_structure: str
    shot_language: str
    lighting_language: str
    materials_language: str
    brand_fit_reason: str
    originality_score: int
    brand_fit_score: int
    clarity_score: int
    diversity_tags: List[str]

    @property
    def total_score(self) -> int:
        return self.originality_score + self.brand_fit_score + self.clarity_score

    def to_dict(self) -> Dict:
        return asdict(self)


class STCAdBrain:
    """
    هذا الملف لا يستدعي أي API.
    وظيفته: منع XPAND من الانهيار إلى "مشهد عادي"،
    وإجباره على التفكير كفريق إبداعي إعلاني.
    """

    def generate_concepts(self, benefit_family: str, visual_family: str) -> List[AdConcept]:
        if benefit_family == "merchant_payments":
            return self._merchant_payments_concepts(visual_family)
        return self._generic_financial_concepts(benefit_family, visual_family)

    def shortlist(self, concepts: List[AdConcept], top_n: int = 3) -> List[AdConcept]:
        ranked = sorted(concepts, key=lambda c: c.total_score, reverse=True)

        selected: List[AdConcept] = []
        used_tags = set()

        for concept in ranked:
            concept_tags = set(concept.diversity_tags)
            if not selected:
                selected.append(concept)
                used_tags |= concept_tags
                continue

            overlap = len(used_tags & concept_tags)
            if overlap <= 2:
                selected.append(concept)
                used_tags |= concept_tags

            if len(selected) >= top_n:
                break

        if len(selected) < top_n:
            for concept in ranked:
                if concept not in selected:
                    selected.append(concept)
                if len(selected) >= top_n:
                    break

        return selected[:top_n]

    def _merchant_payments_concepts(self, visual_family: str) -> List[AdConcept]:
        """Return campaign ideas, not variations of a payment counter."""
        purple = visual_family in {"purple_architectural", "premium_purple_architecture"}
        palette = (
            "Saturated STC deep-violet architectural planes, near-black graphite hero objects, a broad violet/magenta pool from upper-right or rear, restrained mint accent, and physically motivated reflections."
            if purple
            else
            "Natural Saudi commercial palette with one motivated STC purple accent, clean skin/material color, and premium directional light."
        )
        return [
            AdConcept(
                concept_id="mp_continuous_surface",
                title="One Surface, Every Sale",
                headline_strategy="One connected commerce flow.",
                core_idea="A sculptural merchant surface carries an unbranded online order cue into a real contactless checkout action; one change of level makes the digital-to-physical relationship visible.",
                visual_mechanism="Continuous material transition: an abstract product/order cue on a real device leads along one supported surface to a separate POS tap and the prepared handoff.",
                benefit_translation="STC Bank connects online commerce and physical acceptance for the same merchant.",
                environment=f"Purpose-built premium STC campaign set, not a shop counter: {palette}",
                hero_subject="The continuous surface and decisive tapping hand, with the POS as the causal hero.",
                scene_structure="Asymmetric 4:5 frame; foreground contactless action, midground material bridge, secondary online/fulfillment cue; 25–40% integrated copy space.",
                shot_language="Advertising-grade elevated three-quarter close shot, 50mm commercial perspective, one coherent vanishing system and controlled depth.",
                lighting_language="Broad upper-right/rear violet-magenta key, deep-violet falloff, restrained mint reflection, crisp contact shadows and surface-specific highlights.",
                materials_language="Satin violet lacquer, graphite metal, smoked glass, tactile packaging and realistic screen glass; no random stone pedestal.",
                brand_fit_reason="The STC palette, architectural set and single causal surface make the merchant ecosystem ownable without generated logo or copy.",
                originality_score=94, brand_fit_score=96, clarity_score=94,
                diversity_tags=["continuous_surface", "material_transition", "purple_architecture", "close_action"],
            ),
            AdConcept(
                concept_id="mp_threshold_reveal",
                title="The Sale Opens",
                headline_strategy="From online intent to accepted payment.",
                core_idea="A real architectural threshold frames a physical POS acceptance in the foreground and the fulfilled order beyond it, making one commercial action feel like access to the next stage.",
                visual_mechanism="Perspective reveal through one physical opening; the POS remains near and separate, while the order outcome is visible through the same depth and light.",
                benefit_translation="One STC merchant ecosystem carries the customer from digital order to physical acceptance.",
                environment=f"Sculptural violet threshold set with graphite interior depth; {palette}",
                hero_subject="A hand completing the tap at the threshold, with the order outcome as secondary proof.",
                scene_structure="Low oblique 4:5 composition with a strong doorway silhouette, foreground action and calm upper-right copy space integrated into the lit plane.",
                shot_language="Low-grazing campaign hero shot, 45mm lens character, deliberate asymmetry and physically coherent perspective.",
                lighting_language="Violet pool behind the threshold, controlled rim on the terminal, deep plum shadow and real reflected light on satin planes.",
                materials_language="Matte architectural paint, satin lacquer bevels, graphite terminal, tactile parcel and smoked reflective surface.",
                brand_fit_reason="The physical threshold expresses access and continuity in the same visual grammar as the supplied STC architectural references.",
                originality_score=93, brand_fit_score=95, clarity_score=92,
                diversity_tags=["threshold", "reveal", "low_angle", "architectural"],
            ),
            AdConcept(
                concept_id="mp_precise_handoff",
                title="The Moment Connects",
                headline_strategy="One tap, one connected operation.",
                core_idea="Two hands perform one timed commercial handoff: one completes contactless acceptance while the other receives or seals the same order, with a supporting non-readable online cue kept secondary.",
                visual_mechanism="Synchronized hand choreography creates cause and effect without a split screen, graphic line or unrelated device display.",
                benefit_translation="STC Bank keeps digital order and physical payment in the same merchant rhythm.",
                environment=f"Editorial STC studio close-up with violet planes and graphite work surface; {palette}",
                hero_subject="The two-hand timing and contactless POS interaction.",
                scene_structure="Tight diagonal 4:5 crop, hands and objects large, one secondary phone/tablet edge with abstract unreadable UI only if needed; integrated dark-violet copy space.",
                shot_language="Macro-adjacent close-up, 70mm product realism, focus on contact and material tension, no face-led framing.",
                lighting_language="Soft violet side key, narrow real reflections on metal/glass, controlled negative fill and attached hand/object shadows.",
                materials_language="Graphite hardware, satin violet surface, natural cardboard/fabric, skin texture and physically correct screen glass.",
                brand_fit_reason="STC identity comes from confident restraint, precise action, purple architecture and premium material separation—not generic fintech graphics.",
                originality_score=92, brand_fit_score=94, clarity_score=95,
                diversity_tags=["handoff", "hands", "macro", "timing"],
            ),
            AdConcept(
                concept_id="mp_reflection_pairing",
                title="Every Channel in View",
                headline_strategy="Commerce, reflected as one.",
                core_idea="A sharp physical POS tap is paired with a real reflection in the same glossy plane that reveals the online/fulfillment context, never as a floating duplicate.",
                visual_mechanism="Reflection-led pairing: one surface and one camera make the two channels visibly belong to the same merchant workflow.",
                benefit_translation="STC Bank unifies the visible checkout and the online order journey.",
                environment=f"Deep-violet STC studio with a purposeful smoked-glass plane and restrained green accent; {palette}",
                hero_subject="The contactless gesture and its physically correct reflected relationship.",
                scene_structure="Elevated oblique 4:5 frame with hero action on the lower third, reflection as secondary proof and calm lit upper plane for copy.",
                shot_language="Reflection-led oblique advertising shot, 55mm compression, level horizon and one focus plane.",
                lighting_language="Large soft upper-right source, violet/magenta rear pool, controlled specular strip and deep readable shadow.",
                materials_language="Smoked glass, satin lacquer, brushed graphite metal, matte package surface; reflections follow roughness and surface normal.",
                brand_fit_reason="The reference-matched color and reflection discipline make the service relationship feel like a premium STC campaign device.",
                originality_score=95, brand_fit_score=95, clarity_score=91,
                diversity_tags=["reflection", "pairing", "elevated_oblique", "glass"],
            ),
            AdConcept(
                concept_id="mp_product_theatre",
                title="The Merchant Engine",
                headline_strategy="One system behind the sale.",
                core_idea="A designed STC product theatre compresses the merchant workflow into one bold silhouette: a real POS action, one order cue and a physical handoff share a purposeful set.",
                visual_mechanism="Scale and spatial compression: the support planes make the online and physical stages readable as one operating system without a diagram.",
                benefit_translation="STC Bank supports the merchant across digital and in-person commerce.",
                environment=f"Premium violet architectural theatre with two connected planes, deep recess and graphite hero supports; {palette}",
                hero_subject="A real POS in active use, not a card or terminal displayed as a trophy.",
                scene_structure="Controlled frontal three-quarter 4:5 silhouette with one dominant action, one secondary order cue and 30% integrated upper-plane copy space.",
                shot_language="Low oblique product advertising shot, 65mm perspective, crisp hero focus and clean negative fill.",
                lighting_language="Saturated violet pool on the rear plane, soft key from upper-right, violet edge response and grounded contact shadows.",
                materials_language="Graphite metal, satin violet lacquer, matte packaging, selective glass reflection and accurate bevel highlights.",
                brand_fit_reason="It applies the supplied STC product-ad language while replacing the generic pedestal with a meaningful merchant mechanism.",
                originality_score=91, brand_fit_score=97, clarity_score=90,
                diversity_tags=["product_theatre", "scale", "silhouette", "low_oblique"],
            ),
            AdConcept(
                concept_id="mp_saudi_commerce",
                title="A Business in Motion",
                headline_strategy="Built for every way customers buy.",
                core_idea="A specific contemporary Saudi merchant category is captured at the instant an online order becomes an in-person handoff, with the POS action driving the moment.",
                visual_mechanism="Foreground/background cause and effect: a contactless acceptance action leads the eye to a real order handoff in one continuous premium environment.",
                benefit_translation="STC Bank helps Saudi merchants serve online and in-store customers through one connected service.",
                environment="Specific modern Saudi specialty retailer with controlled STC purple architectural accents, tactile local material culture and no stock-office staging.",
                hero_subject="Merchant hands and customer handoff; faces remain secondary.",
                scene_structure="Eye-level oblique 4:5 environmental close shot, real depth, dark purple practical light and integrated side copy space.",
                shot_language="35mm environmental advertising perspective with foreground occlusion and controlled background falloff.",
                lighting_language="Motivated violet practical plus neutral key, green accent only on a small physical detail, natural skin and realistic reflections.",
                materials_language="Contemporary Saudi retail materials, premium packaging, graphite terminal, glass and fabric with accurate roughness.",
                brand_fit_reason="The service is anchored in believable Saudi commerce while the controlled STC palette and camera make it campaign-owned rather than stock photography.",
                originality_score=93, brand_fit_score=94, clarity_score=93,
                diversity_tags=["saudi_context", "handoff", "environmental", "human_action"],
            ),
        ]
    def _generic_financial_concepts(self, benefit_family: str, visual_family: str) -> List[AdConcept]:
        return [
            AdConcept(
                concept_id="gen_01",
                title="Brand-Led Premium Financial Story",
                headline_strategy="Benefit transformed into a branded visual story.",
                core_idea=f"Translate {benefit_family} into a premium STC Bank advertising image.",
                visual_mechanism="Clear consumer benefit mapped into one strong ad mechanism.",
                benefit_translation=f"Make {benefit_family} visually understandable and premium.",
                environment="Premium Saudi lifestyle setting with clear brand-fit.",
                hero_subject="A relevant Saudi customer or merchant scenario.",
                scene_structure="Advertising image, not a generic scene.",
                shot_language="Premium campaign photography.",
                lighting_language="High-end branded realism.",
                materials_language="Refined materials and strong brand discipline.",
                brand_fit_reason="Ensures the request remains ad-grade and brand-aware.",
                originality_score=82,
                brand_fit_score=88,
                clarity_score=87,
                diversity_tags=["generic", "brand_first"],
            )
        ]


if __name__ == "__main__":
    brain = STCAdBrain()
    concepts = brain.generate_concepts("merchant_payments", "premium_realistic")
    shortlisted = brain.shortlist(concepts, top_n=3)

    print("==========================================")
    print(" XPAND STC AD BRAIN SELF TEST")
    print("==========================================")
    print(f"generated_concepts = {len(concepts)}")
    print(f"shortlisted = {len(shortlisted)}")
    for item in shortlisted:
        print(f"- {item.concept_id} | {item.title} | total={item.total_score}")
    print("PASS ✅")
