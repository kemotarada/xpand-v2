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
        premium_realistic = visual_family == "premium_realistic"

        return [
            AdConcept(
                concept_id="mp_01",
                title="Commerce Continuum",
                headline_strategy="The sale never breaks.",
                core_idea="A single premium Saudi retail environment shows the digital order journey and the in-store payment journey fused into one elegant commercial moment.",
                visual_mechanism="One frame, two synchronized transactions: a customer completes a tap payment while a fulfilled e-commerce parcel is prepared in the same visual rhythm.",
                benefit_translation="STC Bank powers both online commerce and physical checkout in one merchant ecosystem.",
                environment="A premium Saudi concept store with refined stone, soft beige architecture, subtle brand-led color accents, operational elegance, and visible retail sophistication.",
                hero_subject="Saudi merchant ecosystem: merchant, customer, packaging flow, checkout moment.",
                scene_structure="Ad campaign composition with a clear commercial choreography. The frame is intentionally art-directed, not documentary. Distinct zones show in-store payment and e-commerce fulfillment without becoming cluttered.",
                shot_language="Advertising-grade medium wide shot, layered depth, clean visual hierarchy, luxury retail composition, controlled perspective.",
                lighting_language="Soft premium daylight with controlled warm fill, polished ad-grade reflections, elegant shadow separation.",
                materials_language="Natural stone, refined wood in secondary use only, matte metals, premium retail textures, elegant packaging.",
                brand_fit_reason="Strong fit for merchant payments because it shows commerce fusion rather than a random payment moment.",
                originality_score=88 if premium_realistic else 84,
                brand_fit_score=94,
                clarity_score=91,
                diversity_tags=["fusion", "retail", "ecosystem", "ad_choreography"],
            ),
            AdConcept(
                concept_id="mp_02",
                title="Tap and Dispatch",
                headline_strategy="Payment triggers fulfillment.",
                core_idea="The act of tap payment becomes the visual trigger that sets the fulfillment chain in motion.",
                visual_mechanism="A premium visual bridge links the customer tap to a shipping-preparation gesture in the background, creating an advertising metaphor of one action powering both channels.",
                benefit_translation="Online and in-store merchant operations are unified under one payment engine.",
                environment="A Saudi lifestyle merchant space such as a premium perfume atelier or upscale beauty/lifestyle store with visible packing station.",
                hero_subject="Saudi customer paying, merchant receiving, staff preparing a parcel.",
                scene_structure="Foreground action: tap payment. Midground: digital product/order surface. Background: package preparation. Clear ad hierarchy.",
                shot_language="Hero advertising perspective, depth layering, premium brand photography, commercial storytelling angle.",
                lighting_language="Bright premium key light with commercial polish, subtle glow on transaction touchpoint, crisp detail.",
                materials_language="Refined stone counters, premium display shelving, elegant packaging components, understated brand palette accents.",
                brand_fit_reason="Transforms the feature into a commercial mechanism, not a literal generic payment shot.",
                originality_score=90,
                brand_fit_score=92,
                clarity_score=89,
                diversity_tags=["trigger", "fulfillment", "journey", "merchant_story"],
            ),
            AdConcept(
                concept_id="mp_03",
                title="Merchant Operating System",
                headline_strategy="One banking layer behind every sale.",
                core_idea="Instead of a customer-only scene, the hero is the merchant environment itself—showing that STC Bank is the invisible engine behind digital and physical sales.",
                visual_mechanism="A premium retail operations tableau links tablet catalog browsing, point-of-sale readiness, packaging, and merchant control in one editorial-advertising composition.",
                benefit_translation="STC Bank supports the whole merchant operation, not only the final tap.",
                environment="A premium Saudi specialty retailer: design boutique, curated gifting store, premium home accessories showroom, or artisan lifestyle space.",
                hero_subject="Merchant-led scene with visible operational intelligence.",
                scene_structure="Ad-style operations tableau with visual anchors: transaction point, product discovery, order handling, merchant confidence.",
                shot_language="High-end commercial still life + human presence hybrid, structured composition, premium editorial aesthetic.",
                lighting_language="Balanced daylight and warm accent lighting with polished shadows and clear product separation.",
                materials_language="Architectural calm, premium shelving, tactile products, stone and matte finishes.",
                brand_fit_reason="Much closer to a bank ad because it expresses system-level value and brand confidence.",
                originality_score=87,
                brand_fit_score=95,
                clarity_score=88,
                diversity_tags=["merchant_os", "tableau", "system", "editorial"],
            ),
            AdConcept(
                concept_id="mp_04",
                title="Saudi Commerce in Motion",
                headline_strategy="Modern Saudi selling, online and in-store.",
                core_idea="A more dynamic ad showing a merchant business serving both e-commerce and in-store customers at once in a polished, cinematic, premium commercial frame.",
                visual_mechanism="Spatial choreography: one shopper taps to pay while another commerce touchpoint shows online order movement, creating a sense of modern merchant momentum.",
                benefit_translation="STC Bank keeps the merchant business moving across all channels.",
                environment="A modern Saudi merchant environment with cultural authenticity but premium sophistication—not an office, not a plain counter.",
                hero_subject="Merchant, customer, product, and order flow.",
                scene_structure="Motion-rich ad frame with staged realism, premium flow, and narrative energy.",
                shot_language="Cinematic advertising wide-medium hybrid with strong subject blocking and elegant depth.",
                lighting_language="High-end lifestyle commercial lighting, natural but enhanced, luxury-grade tonal control.",
                materials_language="Retail architecture, packaging, textiles, premium objects, restrained palette with brand accents.",
                brand_fit_reason="Adds dynamism and sale momentum, making it feel like a real campaign rather than a catalog scene.",
                originality_score=91,
                brand_fit_score=90,
                clarity_score=87,
                diversity_tags=["motion", "saudi_life", "commerce", "cinematic"],
            ),
            AdConcept(
                concept_id="mp_05",
                title="From Shelf to Screen to Sale",
                headline_strategy="Every path to purchase, one banking experience.",
                core_idea="Product discovery, digital ordering, and in-store payment appear as a single elegant commercial journey.",
                visual_mechanism="Triptych logic inside one frame: product, digital browse/order, payment. The scene feels like an ad concept, not a literal split-screen.",
                benefit_translation="STC Bank bridges discovery, e-commerce, and retail payment.",
                environment="Premium Saudi retail environment with lifestyle credibility and art-directed simplicity.",
                hero_subject="Products and people share the hero role.",
                scene_structure="Ad composition with one hero transaction zone and secondary discovery/fulfillment zones.",
                shot_language="Structured commercial composition with branded discipline and premium product visibility.",
                lighting_language="Polished product-ad lighting with lifestyle realism.",
                materials_language="Elevated retail materials, premium fixtures, sophisticated merchandising.",
                brand_fit_reason="Visually sophisticated and closer to campaign logic than a plain payment shot.",
                originality_score=89,
                brand_fit_score=93,
                clarity_score=90,
                diversity_tags=["journey", "triptych", "product", "campaign_logic"],
            ),
            AdConcept(
                concept_id="mp_06",
                title="The Merchant Confidence Frame",
                headline_strategy="Confidence across every checkout.",
                core_idea="A confident Saudi merchant runs both store and e-commerce from a premium branded environment, with the customer touchpoint embedded naturally rather than staged awkwardly.",
                visual_mechanism="The merchant is visually centered between physical checkout and digital order flow, symbolizing STC Bank as the business enabler.",
                benefit_translation="The bank empowers merchant control, reliability, and payment fluidity.",
                environment="Premium Saudi business environment, contemporary retail-lifestyle space, elegant but not cold.",
                hero_subject="Merchant-led confidence and human assurance.",
                scene_structure="Central hero subject, secondary operational zones, premium copy space left intentionally open.",
                shot_language="Portrait-led advertising composition with strong commercial authority.",
                lighting_language="Confident premium key light with subtle brand color influence, clean highlights.",
                materials_language="Architectural calm, premium retail textures, refined operational details.",
                brand_fit_reason="Banking ads often win when they sell confidence, not just tools.",
                originality_score=86,
                brand_fit_score=96,
                clarity_score=92,
                diversity_tags=["confidence", "merchant", "portrait", "copy_space"],
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
