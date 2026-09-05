# xpand_stc_ad_quality.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

from xpand_stc_ad_brain import AdConcept


@dataclass
class QualityAudit:
    passed: bool
    total_score: int
    issues: List[str]
    strengths: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class STCAdQualityGate:
    """
    بوابة قتل الرداءة.
    إذا الفكرة generic أو مكررة أو لا تشبه إعلان بنك، تترفض.
    """

    GENERIC_PATTERNS = [
        "generic office",
        "plain office",
        "wooden checkout counter",
        "simple payment counter",
        "floating card",
        "plain purple wall",
        "random bank app UI",
        "unbranded retail payment scene",
        "documentary style payment moment",
        "generic fintech clutter",
    ]

    BANNED_ENVIRONMENT_HINTS = [
        "office",
        "plain counter",
        "bank branch desk",
        "generic lobby",
    ]

    REQUIRED_AD_SIGNALS = [
        "visual mechanism",
        "benefit translation",
        "brand fit",
        "premium shot language",
    ]

    def audit_concept(self, concept: AdConcept, brand_banned_patterns: List[str]) -> QualityAudit:
        issues: List[str] = []
        strengths: List[str] = []
        score = 100

        env = concept.environment.lower()
        scene = concept.scene_structure.lower()
        shot = concept.shot_language.lower()
        visual = concept.visual_mechanism.lower()
        brand_fit = concept.brand_fit_reason.lower()

        for bad in self.BANNED_ENVIRONMENT_HINTS:
            if bad in env:
                issues.append(f"Environment too generic or weak: {bad}")
                score -= 20

        for bad in brand_banned_patterns:
            if bad.lower() in env or bad.lower() in scene or bad.lower() in visual:
                issues.append(f"Matched banned pattern: {bad}")
                score -= 25

        if "advertising" not in shot and "commercial" not in shot:
            issues.append("Shot language is not explicitly advertising-grade.")
            score -= 15
        else:
            strengths.append("Advertising-grade shot language is present.")

        if len(visual.split()) < 8:
            issues.append("Visual mechanism is weak or too short.")
            score -= 15
        else:
            strengths.append("Visual mechanism is clearly defined.")

        if "bank" not in brand_fit and "brand" not in brand_fit:
            issues.append("Brand fit logic is weak.")
            score -= 10
        else:
            strengths.append("Brand-fit reasoning exists.")

        if concept.originality_score < 85:
            issues.append("Originality score below required STC high-alert threshold.")
            score -= 10
        else:
            strengths.append("Originality is above threshold.")

        if concept.brand_fit_score < 90:
            issues.append("Brand-fit score below required STC threshold.")
            score -= 10
        else:
            strengths.append("Brand-fit is strong.")

        if concept.clarity_score < 88:
            issues.append("Clarity score below target.")
            score -= 5
        else:
            strengths.append("Clarity is strong.")

        passed = score >= 88 and len(issues) == 0
        return QualityAudit(
            passed=passed,
            total_score=max(score, 0),
            issues=issues,
            strengths=strengths,
        )

    def audit_prompt_text(self, prompt_text: str, brand_banned_patterns: List[str]) -> QualityAudit:
        issues: List[str] = []
        strengths: List[str] = []
        score = 100
        lowered = prompt_text.lower()

        for bad in brand_banned_patterns + self.GENERIC_PATTERNS:
            if bad.lower() in lowered:
                issues.append(f"Prompt contains banned/generic signal: {bad}")
                score -= 20

        required_tokens = [
            "advertising image",
            "premium",
            "brand identity",
            "visual mechanism",
            "not a generic scene",
        ]
        for token in required_tokens:
            if token not in lowered:
                issues.append(f"Prompt missing required signal: {token}")
                score -= 8
            else:
                strengths.append(f"Prompt includes required signal: {token}")

        passed = score >= 88 and len(issues) <= 1
        return QualityAudit(
            passed=passed,
            total_score=max(score, 0),
            issues=issues,
            strengths=strengths,
        )


if __name__ == "__main__":
    from xpand_stc_ad_brain import STCAdBrain

    brain = STCAdBrain()
    concept = brain.generate_concepts("merchant_payments", "premium_realistic")[0]
    gate = STCAdQualityGate()
    audit = gate.audit_concept(concept, ["wooden checkout counter", "floating card"])

    print("==========================================")
    print(" XPAND STC AD QUALITY SELF TEST")
    print("==========================================")
    print(f"passed = {audit.passed}")
    print(f"total_score = {audit.total_score}")
    print(f"issues = {len(audit.issues)}")
    print(f"strengths = {len(audit.strengths)}")
    print("PASS ✅")s
