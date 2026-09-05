# xpand_stc_brand_kit.py
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


def _as_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [str(value).strip()] if str(value).strip() else []


@dataclass
class ReferenceAsset:
    asset_id: str
    path: str
    kind: str
    roles: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    benefit_families: List[str] = field(default_factory=list)
    visual_families: List[str] = field(default_factory=list)
    priority: int = 50
    notes: str = ""


@dataclass
class StyleFamily:
    family_id: str
    mood: List[str] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)
    lighting: List[str] = field(default_factory=list)
    scene_rules: List[str] = field(default_factory=list)


@dataclass
class BrandKit:
    brand_id: str
    brand_name: str
    identity_keywords: List[str]
    required_brand_signals: List[str]
    banned_patterns: List[str]
    approved_mechanisms: List[str]
    style_families: Dict[str, StyleFamily]
    assets: List[ReferenceAsset]
    pack_path: Path

    @classmethod
    def load(cls, pack_json_path: str | Path) -> "BrandKit":
        path = Path(pack_json_path)
        data = json.loads(path.read_text(encoding="utf-8"))

        style_families: Dict[str, StyleFamily] = {}
        for family_id, family_data in data.get("style_families", {}).items():
            style_families[family_id] = StyleFamily(
                family_id=family_id,
                mood=_as_list(family_data.get("mood")),
                colors=_as_list(family_data.get("colors")),
                materials=_as_list(family_data.get("materials")),
                lighting=_as_list(family_data.get("lighting")),
                scene_rules=_as_list(family_data.get("scene_rules")),
            )

        assets: List[ReferenceAsset] = []
        for item in data.get("assets", []):
            assets.append(
                ReferenceAsset(
                    asset_id=item["asset_id"],
                    path=item["path"],
                    kind=item.get("kind", "reference"),
                    roles=_as_list(item.get("roles")),
                    tags=_as_list(item.get("tags")),
                    benefit_families=_as_list(item.get("benefit_families")),
                    visual_families=_as_list(item.get("visual_families")),
                    priority=int(item.get("priority", 50)),
                    notes=item.get("notes", ""),
                )
            )

        return cls(
            brand_id=data["brand_id"],
            brand_name=data["brand_name"],
            identity_keywords=_as_list(data.get("identity_keywords")),
            required_brand_signals=_as_list(data.get("required_brand_signals")),
            banned_patterns=_as_list(data.get("banned_patterns")),
            approved_mechanisms=_as_list(data.get("approved_mechanisms")),
            style_families=style_families,
            assets=assets,
            pack_path=path,
        )

    def resolve_asset_path(self, relative_path: str) -> Path:
        return self.pack_path.parent.parent / relative_path

    def asset_exists(self, asset: ReferenceAsset) -> bool:
        return self.resolve_asset_path(asset.path).exists()

    def existing_assets(self) -> List[ReferenceAsset]:
        return [a for a in self.assets if self.asset_exists(a)]

    def _score_asset(
        self,
        asset: ReferenceAsset,
        benefit_family: Optional[str],
        visual_family: Optional[str],
        preferred_roles: Optional[List[str]] = None,
    ) -> int:
        score = asset.priority

        if benefit_family and benefit_family in asset.benefit_families:
            score += 30

        if visual_family and visual_family in asset.visual_families:
            score += 25

        if preferred_roles:
            overlap = set(preferred_roles) & set(asset.roles)
            score += len(overlap) * 20

        return score

    def select_assets(
        self,
        benefit_family: Optional[str],
        visual_family: Optional[str],
        max_brand_dna: int = 3,
        max_physical: int = 2,
        max_layout: int = 2,
        max_total: int = 7,
    ) -> List[ReferenceAsset]:
        available = self.existing_assets()

        brand_dna = []
        physical = []
        layout = []
        rest = []

        for asset in available:
            if "brand_dna" in asset.roles:
                brand_dna.append(asset)
            elif "physical_product" in asset.roles or "ui_product" in asset.roles:
                physical.append(asset)
            elif "layout" in asset.roles or "campaign_style" in asset.roles:
                layout.append(asset)
            else:
                rest.append(asset)

        brand_dna.sort(
            key=lambda a: self._score_asset(
                a, benefit_family, visual_family, preferred_roles=["brand_dna"]
            ),
            reverse=True,
        )
        physical.sort(
            key=lambda a: self._score_asset(
                a,
                benefit_family,
                visual_family,
                preferred_roles=["physical_product", "ui_product"],
            ),
            reverse=True,
        )
        layout.sort(
            key=lambda a: self._score_asset(
                a, benefit_family, visual_family, preferred_roles=["layout", "campaign_style"]
            ),
            reverse=True,
        )
        rest.sort(
            key=lambda a: self._score_asset(a, benefit_family, visual_family),
            reverse=True,
        )

        selected: List[ReferenceAsset] = []
        selected.extend(brand_dna[:max_brand_dna])
        selected.extend(physical[:max_physical])
        selected.extend(layout[:max_layout])

        used_ids = {a.asset_id for a in selected}
        for asset in rest:
            if asset.asset_id in used_ids:
                continue
            selected.append(asset)
            used_ids.add(asset.asset_id)
            if len(selected) >= max_total:
                break

        return selected[:max_total]

    def build_brand_grounding_text(self, visual_family: str) -> str:
        family = self.style_families.get(visual_family)

        lines = []
        lines.append(f"Brand identity: {self.brand_name}.")
        if self.identity_keywords:
            lines.append("Identity keywords: " + ", ".join(self.identity_keywords) + ".")
        if self.required_brand_signals:
            lines.append("Required brand signals: " + ", ".join(self.required_brand_signals) + ".")
        if family:
            if family.mood:
                lines.append("Mood: " + ", ".join(family.mood) + ".")
            if family.colors:
                lines.append("Color language: " + ", ".join(family.colors) + ".")
            if family.materials:
                lines.append("Material language: " + ", ".join(family.materials) + ".")
            if family.lighting:
                lines.append("Lighting language: " + ", ".join(family.lighting) + ".")
            if family.scene_rules:
                lines.append("Scene rules: " + ", ".join(family.scene_rules) + ".")
        if self.approved_mechanisms:
            lines.append("Approved advertising mechanisms: " + ", ".join(self.approved_mechanisms) + ".")

        return " ".join(lines)

    def build_banned_patterns_text(self) -> str:
        if not self.banned_patterns:
            return ""
        return "Avoid these banned patterns: " + ", ".join(self.banned_patterns) + "."

    def reference_paths(self, assets: List[ReferenceAsset]) -> List[str]:
        return [str(self.resolve_asset_path(asset.path)) for asset in assets]

    def summary(self) -> Dict:
        return {
            "brand_id": self.brand_id,
            "brand_name": self.brand_name,
            "assets_total": len(self.assets),
            "assets_existing": len(self.existing_assets()),
            "style_families": list(self.style_families.keys()),
        }


if __name__ == "__main__":
    pack = BrandKit.load("brand_assets/stc_bank/stc_bank_brand_pack.json")
    print("==========================================")
    print(" XPAND STC BRAND KIT SELF TEST")
    print("==========================================")
    info = pack.summary()
    print(f"brand_id = {info['brand_id']}")
    print(f"brand_name = {info['brand_name']}")
    print(f"assets_total = {info['assets_total']}")
    print(f"assets_existing = {info['assets_existing']}")
    print(f"style_families = {', '.join(info['style_families'])}")
    print("PASS ✅")
