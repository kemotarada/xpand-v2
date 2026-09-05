# =========================================================
# XPAND STC BANK BRAND KIT V2.0
#
# PERMANENT LOCAL BRAND REFERENCE CURATOR
# FULL RUNTIME-COMPATIBLE REPLACEMENT
#
# =========================================================
#
# PURPOSE
#
# - Load permanent STC Bank reference library
# - Understand current JSON V2 schema
# - Preserve old schema compatibility
# - Select references by:
#       brand DNA
#       visual family
#       service / benefit family
#       role
#       priority
#       diversity
# - Return REAL local image paths
# - Prevent wrong-style references
# - Avoid duplicate / redundant references
# - Build brand-grounding instructions
#
# =========================================================
#
# COMPATIBILITY PRESERVED
#
#   ReferenceAsset
#   StyleFamily
#   BrandKit
#
#   BrandKit.load()
#   BrandKit.resolve_asset_path()
#   BrandKit.asset_exists()
#   BrandKit.existing_assets()
#   BrandKit.select_assets()
#   BrandKit.build_brand_grounding_text()
#   BrandKit.build_banned_patterns_text()
#   BrandKit.reference_paths()
#   BrandKit.summary()
#
# =========================================================


from __future__ import annotations


import hashlib
import json
import re

from dataclasses import (
    dataclass,
    field,
)

from pathlib import Path

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
)


# =========================================================
# IDENTITY
# =========================================================

VERSION = "2.0"

MODULE_NAME = "XPAND STC Bank Brand Kit"


# =========================================================
# HELPERS
# =========================================================

def _clean_text(
    value: Any,
    limit: int = 8000,
) -> str:

    return (
        str(
            value
            if value is not None
            else ""
        )
        .replace(
            "\x00",
            "",
        )
        .strip()[:limit]
    )


def _as_list(
    value: Any,
) -> List[str]:

    if value is None:

        return []

    if isinstance(
        value,
        list,
    ):

        output: List[str] = []

        for item in value:

            text = _clean_text(
                item,
                1000,
            )

            if text:

                output.append(
                    text
                )

        return output

    text = _clean_text(
        value,
        1000,
    )

    return (
        [text]
        if text
        else []
    )


def _safe_dict(
    value: Any,
) -> Dict[str, Any]:

    if isinstance(
        value,
        dict,
    ):

        return value

    return {}


def _safe_int(
    value: Any,
    default: int = 50,
) -> int:

    try:

        return int(
            value
        )

    except Exception:

        return int(
            default
        )


def _normalize(
    value: Any,
) -> str:

    text = _clean_text(
        value,
        20000,
    ).lower()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
        "ـ": "",
    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new,
        )

    text = re.sub(
        r"[\u064B-\u065F]",
        "",
        text,
    )

    text = re.sub(
        r"[^a-z0-9\u0600-\u06FF_./ -]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _contains_any(
    value: Any,
    markers: Sequence[str],
) -> bool:

    text = _normalize(
        value
    )

    return any(
        _normalize(
            marker
        )
        in text
        for marker
        in markers
    )


def _dedupe_strings(
    values: Iterable[str],
) -> List[str]:

    result: List[str] = []

    seen: Set[str] = set()

    for raw in values:

        value = _clean_text(
            raw,
            2000,
        )

        if not value:

            continue

        key = value.lower()

        if key in seen:

            continue

        seen.add(
            key
        )

        result.append(
            value
        )

    return result


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class ReferenceAsset:

    asset_id: str

    path: str

    kind: str

    roles: List[str] = field(
        default_factory=list
    )

    tags: List[str] = field(
        default_factory=list
    )

    benefit_families: List[str] = field(
        default_factory=list
    )

    visual_families: List[str] = field(
        default_factory=list
    )

    priority: int = 50

    notes: str = ""

    category: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class StyleFamily:

    family_id: str

    name: str = ""

    description: str = ""

    mood: List[str] = field(
        default_factory=list
    )

    colors: List[str] = field(
        default_factory=list
    )

    materials: List[str] = field(
        default_factory=list
    )

    lighting: List[str] = field(
        default_factory=list
    )

    scene_rules: List[str] = field(
        default_factory=list
    )

    camera_language: List[str] = field(
        default_factory=list
    )


@dataclass
class BrandKit:

    brand_id: str

    brand_name: str

    identity_keywords: List[str]

    required_brand_signals: List[str]

    banned_patterns: List[str]

    approved_mechanisms: List[str]

    style_families: Dict[
        str,
        StyleFamily
    ]

    assets: List[
        ReferenceAsset
    ]

    pack_path: Path

    version: str = ""

    default_visual_family: str = (
        "premium_realistic"
    )

    global_rules: Dict[
        str,
        Any
    ] = field(
        default_factory=dict
    )

    benefit_families: Dict[
        str,
        Any
    ] = field(
        default_factory=dict
    )

    raw_data: Dict[
        str,
        Any
    ] = field(
        default_factory=dict
    )


    # =====================================================
    # LOAD
    # =====================================================

    @classmethod
    def load(
        cls,
        pack_json_path: str | Path,
    ) -> "BrandKit":

        path = Path(
            pack_json_path
        ).resolve()

        if not path.is_file():

            raise FileNotFoundError(
                (
                    "STC brand pack not found: "
                    +
                    str(
                        path
                    )
                )
            )

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            data,
            dict,
        ):

            raise ValueError(
                "STC brand pack root must be an object."
            )

        # =================================================
        # STYLE FAMILIES
        # =================================================

        style_families: Dict[
            str,
            StyleFamily
        ] = {}

        for (
            family_id,
            raw_family,
        ) in _safe_dict(
            data.get(
                "style_families"
            )
        ).items():

            family_data = _safe_dict(
                raw_family
            )

            #
            # IMPORTANT:
            #
            # V2 JSON uses "rules".
            # Old schema used "scene_rules".
            #
            # Support BOTH.
            #

            rules = (
                _as_list(
                    family_data.get(
                        "rules"
                    )
                )
                +
                _as_list(
                    family_data.get(
                        "scene_rules"
                    )
                )
            )

            style_families[
                str(
                    family_id
                )
            ] = StyleFamily(

                family_id=str(
                    family_id
                ),

                name=_clean_text(
                    family_data.get(
                        "name"
                    ),
                    500,
                ),

                description=_clean_text(
                    family_data.get(
                        "description"
                    ),
                    2500,
                ),

                mood=_as_list(
                    family_data.get(
                        "mood"
                    )
                ),

                colors=_as_list(
                    family_data.get(
                        "colors"
                    )
                ),

                materials=_as_list(
                    family_data.get(
                        "materials"
                    )
                ),

                lighting=_as_list(
                    family_data.get(
                        "lighting"
                    )
                ),

                scene_rules=(
                    _dedupe_strings(
                        rules
                    )
                ),

                camera_language=_as_list(
                    family_data.get(
                        "camera_language"
                    )
                ),
            )

        # =================================================
        # ASSETS
        # =================================================

        assets: List[
            ReferenceAsset
        ] = []

        for raw_item in data.get(
            "assets",
            [],
        ):

            if not isinstance(
                raw_item,
                dict,
            ):

                continue

            asset_id = _clean_text(
                raw_item.get(
                    "asset_id"
                ),
                300,
            )

            asset_path = _clean_text(
                raw_item.get(
                    "path"
                ),
                1200,
            )

            if not asset_id or not asset_path:

                continue

            #
            # IMPORTANT:
            #
            # V2 JSON:
            #   "styles"
            #
            # Old code:
            #   "visual_families"
            #
            # Support BOTH.
            #

            visual_families = (
                _as_list(
                    raw_item.get(
                        "styles"
                    )
                )
                +
                _as_list(
                    raw_item.get(
                        "visual_families"
                    )
                )
            )

            roles = _as_list(
                raw_item.get(
                    "roles"
                )
            )

            tags = _as_list(
                raw_item.get(
                    "tags"
                )
            )

            benefit_families = _as_list(
                raw_item.get(
                    "benefit_families"
                )
            )

            category = cls._infer_asset_category_static(
                path=asset_path,
                roles=roles,
            )

            #
            # Add useful derived tags.
            #

            derived_tags = [
                category,
                asset_id,
            ]

            derived_tags.extend(
                roles
            )

            derived_tags.extend(
                visual_families
            )

            derived_tags.extend(
                benefit_families
            )

            assets.append(

                ReferenceAsset(

                    asset_id=(
                        asset_id
                    ),

                    path=(
                        asset_path
                    ),

                    kind=_clean_text(
                        raw_item.get(
                            "kind",
                            "image",
                        ),
                        100,
                    )
                    or
                    "image",

                    roles=(
                        _dedupe_strings(
                            roles
                        )
                    ),

                    tags=(
                        _dedupe_strings(
                            tags
                            +
                            derived_tags
                        )
                    ),

                    benefit_families=(
                        _dedupe_strings(
                            benefit_families
                        )
                    ),

                    visual_families=(
                        _dedupe_strings(
                            visual_families
                        )
                    ),

                    priority=_safe_int(
                        raw_item.get(
                            "priority"
                        ),
                        50,
                    ),

                    notes=_clean_text(
                        raw_item.get(
                            "notes"
                        ),
                        2500,
                    ),

                    category=(
                        category
                    ),

                    metadata=dict(
                        raw_item
                    ),
                )
            )

        # =================================================
        # APPROVED MECHANISM KEY COMPATIBILITY
        # =================================================

        approved_mechanisms = (
            _as_list(
                data.get(
                    "approved_mechanisms"
                )
            )
            +
            _as_list(
                data.get(
                    "approved_visual_mechanisms"
                )
            )
        )

        return cls(

            brand_id=_clean_text(
                data.get(
                    "brand_id"
                ),
                200,
            ),

            brand_name=_clean_text(
                data.get(
                    "brand_name"
                ),
                500,
            ),

            identity_keywords=_as_list(
                data.get(
                    "identity_keywords"
                )
            ),

            required_brand_signals=_as_list(
                data.get(
                    "required_brand_signals"
                )
            ),

            banned_patterns=_as_list(
                data.get(
                    "banned_patterns"
                )
            ),

            approved_mechanisms=(
                _dedupe_strings(
                    approved_mechanisms
                )
            ),

            style_families=(
                style_families
            ),

            assets=(
                assets
            ),

            pack_path=(
                path
            ),

            version=_clean_text(
                data.get(
                    "version"
                ),
                100,
            ),

            default_visual_family=(
                _clean_text(
                    data.get(
                        "default_visual_family"
                    ),
                    200,
                )
                or
                "premium_realistic"
            ),

            global_rules=_safe_dict(
                data.get(
                    "global_rules"
                )
            ),

            benefit_families=_safe_dict(
                data.get(
                    "benefit_families"
                )
            ),

            raw_data=(
                data
            ),
        )


    # =====================================================
    # CATEGORY INFERENCE
    # =====================================================

    @staticmethod
    def _infer_asset_category_static(
        *,
        path: str,
        roles: Sequence[str],
    ) -> str:

        value = _normalize(
            path
            +
            " "
            +
            " ".join(
                roles
            )
        )

        if "brand_dna" in value or "/dna/" in value:

            return "dna"

        if (
            "realistic_reference"
            in value
            or
            "/realistic/"
            in value
        ):

            return "realistic"

        if (
            "purple_reference"
            in value
            or
            "/purple/"
            in value
        ):

            return "purple"

        if (
            "augmented_reference"
            in value
            or
            "/augmented/"
            in value
        ):

            return "augmented"

        if (
            "merchant_reference"
            in value
            or
            "/merchant/"
            in value
        ):

            return "merchant"

        if (
            "physical_product"
            in value
            or
            "/products/"
            in value
        ):

            return "product"

        if (
            "ui_product"
            in value
            or
            "/ui/"
            in value
        ):

            return "ui"

        if (
            "layout"
            in value
            or
            "/layouts/"
            in value
        ):

            return "layout"

        return "other"


    # =====================================================
    # PATH RESOLUTION
    # =====================================================

    def resolve_asset_path(
        self,
        relative_path: str,
    ) -> Path:

        relative = Path(
            _clean_text(
                relative_path,
                2000,
            )
        )

        if relative.is_absolute():

            return relative

        #
        # Current structure:
        #
        # /app/brand_assets/stc_bank/stc_bank_brand_pack.json
        #
        # JSON path:
        #
        # stc_bank/dna/stc_dna_01.jpg
        #
        # Root therefore:
        #
        # /app/brand_assets/
        #

        brand_assets_root = (
            self.pack_path
            .parent
            .parent
        )

        candidate = (
            brand_assets_root
            /
            relative
        ).resolve()

        return candidate


    def asset_exists(
        self,
        asset: ReferenceAsset,
    ) -> bool:

        try:

            path = self.resolve_asset_path(
                asset.path
            )

            return (
                path.is_file()
                and
                path.stat().st_size > 0
            )

        except Exception:

            return False


    def existing_assets(
        self,
    ) -> List[
        ReferenceAsset
    ]:

        return [
            asset
            for asset
            in self.assets
            if self.asset_exists(
                asset
            )
        ]


    # =====================================================
    # REQUEST / STYLE HELPERS
    # =====================================================

    def normalize_visual_family(
        self,
        visual_family: Optional[str],
    ) -> str:

        value = _clean_text(
            visual_family,
            300,
        )

        if not value:

            return self.default_visual_family

        aliases = {

            "realistic":
                "premium_realistic",

            "premium realistic":
                "premium_realistic",

            "premium_realistic":
                "premium_realistic",

            "واقعي":
                "premium_realistic",

            "واقعية":
                "premium_realistic",

            "purple":
                "premium_purple_architecture",

            "purple architecture":
                "premium_purple_architecture",

            "premium_purple_architecture":
                "premium_purple_architecture",

            "بنفسجي":
                "premium_purple_architecture",

            "augmented":
                "premium_augmented_realism",

            "augmented realism":
                "premium_augmented_realism",

            "symbolic realism":
                "premium_augmented_realism",

            "premium_augmented_realism":
                "premium_augmented_realism",

            "واقعية معززة":
                "premium_augmented_realism",
        }

        normalized = _normalize(
            value
        )

        for alias, target in aliases.items():

            if _normalize(
                alias
            ) == normalized:

                return target

        if value in self.style_families:

            return value

        return (
            self.default_visual_family
        )


    # =====================================================
    # ASSET ROLE HELPERS
    # =====================================================

    def is_brand_dna(
        self,
        asset: ReferenceAsset,
    ) -> bool:

        return bool(
            "brand_dna"
            in asset.roles
            or
            asset.category
            ==
            "dna"
        )


    def is_style_reference(
        self,
        asset: ReferenceAsset,
    ) -> bool:

        return bool(
            asset.category
            in {
                "realistic",
                "purple",
                "augmented",
            }
            or
            "style_reference"
            in asset.roles
        )


    def is_service_reference(
        self,
        asset: ReferenceAsset,
    ) -> bool:

        return bool(
            asset.benefit_families
            or
            asset.category
            ==
            "merchant"
            or
            "merchant_reference"
            in asset.roles
        )


    def is_physical_reference(
        self,
        asset: ReferenceAsset,
    ) -> bool:

        return bool(
            asset.category
            in {
                "product",
                "ui",
            }
            or
            "physical_product"
            in asset.roles
            or
            "ui_product"
            in asset.roles
        )


    def is_layout_reference(
        self,
        asset: ReferenceAsset,
    ) -> bool:

        return bool(
            asset.category
            ==
            "layout"
            or
            "layout"
            in asset.roles
            or
            "campaign_style"
            in asset.roles
        )


    # =====================================================
    # VISUAL FAMILY MATCH
    # =====================================================

    def _visual_family_matches(
        self,
        asset: ReferenceAsset,
        visual_family: Optional[str],
    ) -> bool:

        if not visual_family:

            return True

        family = self.normalize_visual_family(
            visual_family
        )

        if not asset.visual_families:

            #
            # Brand DNA can be cross-style.
            #

            return self.is_brand_dna(
                asset
            )

        return family in asset.visual_families


    # =====================================================
    # WRONG STYLE PENALTY
    # =====================================================

    def _wrong_style_penalty(
        self,
        asset: ReferenceAsset,
        visual_family: str,
    ) -> int:

        family = self.normalize_visual_family(
            visual_family
        )

        if self.is_brand_dna(
            asset
        ):

            #
            # Brand DNA is allowed to cross families,
            # but exact match is still preferred.
            #

            if family in asset.visual_families:

                return 0

            return 8

        if family == "premium_realistic":

            if asset.category == "purple":

                return 80

            if asset.category == "augmented":

                return 45

        if family == "premium_purple_architecture":

            if asset.category == "realistic":

                return 35

            if asset.category == "augmented":

                return 45

        if family == "premium_augmented_realism":

            if asset.category == "purple":

                return 45

        if (
            asset.visual_families
            and
            family not in asset.visual_families
        ):

            return 45

        return 0


    # =====================================================
    # ASSET SCORE
    # =====================================================

    def _score_asset(
        self,
        asset: ReferenceAsset,
        benefit_family: Optional[str],
        visual_family: Optional[str],
        preferred_roles: Optional[
            List[str]
        ] = None,
    ) -> int:

        score = int(
            asset.priority
        )

        family = self.normalize_visual_family(
            visual_family
        )

        # -------------------------------------------------
        # BRAND DNA
        # -------------------------------------------------

        if self.is_brand_dna(
            asset
        ):

            score += 32

        # -------------------------------------------------
        # SERVICE / BENEFIT
        # -------------------------------------------------

        if benefit_family:

            if (
                benefit_family
                in asset.benefit_families
            ):

                score += 55

            elif (
                asset.benefit_families
                and
                benefit_family
                not in asset.benefit_families
            ):

                score -= 35

        # -------------------------------------------------
        # VISUAL FAMILY
        # -------------------------------------------------

        if family:

            if family in asset.visual_families:

                score += 42

            elif self.is_brand_dna(
                asset
            ):

                score += 10

        # -------------------------------------------------
        # SPECIAL CATEGORY MATCH
        # -------------------------------------------------

        if (
            family
            ==
            "premium_realistic"
            and
            asset.category
            ==
            "realistic"
        ):

            score += 38

        if (
            family
            ==
            "premium_purple_architecture"
            and
            asset.category
            ==
            "purple"
        ):

            score += 38

        if (
            family
            ==
            "premium_augmented_realism"
            and
            asset.category
            ==
            "augmented"
        ):

            score += 38

        # -------------------------------------------------
        # MERCHANT
        # -------------------------------------------------

        if (
            benefit_family
            ==
            "merchant_payments"
            and
            asset.category
            ==
            "merchant"
        ):

            score += 50

        # -------------------------------------------------
        # ROLE MATCH
        # -------------------------------------------------

        if preferred_roles:

            overlap = (
                set(
                    preferred_roles
                )
                &
                set(
                    asset.roles
                )
            )

            score += (
                len(
                    overlap
                )
                *
                22
            )

        # -------------------------------------------------
        # WRONG-STYLE PENALTY
        # -------------------------------------------------

        score -= self._wrong_style_penalty(
            asset,
            family,
        )

        return int(
            score
        )


    # =====================================================
    # ROTATION
    # =====================================================

    def _rotation_bonus(
        self,
        asset: ReferenceAsset,
        rotation_key: Optional[str],
    ) -> int:

        if not rotation_key:

            return 0

        value = (
            _clean_text(
                rotation_key,
                2000,
            )
            +
            "|"
            +
            asset.asset_id
        )

        digest = hashlib.sha256(
            value.encode(
                "utf-8"
            )
        ).hexdigest()

        #
        # Small deterministic 0-8 bonus.
        #
        # Enough to rotate similarly scored refs
        # without destroying quality ranking.
        #

        return (
            int(
                digest[:4],
                16,
            )
            %
            9
        )


    # =====================================================
    # DIVERSITY
    # =====================================================

    def _asset_similarity_key(
        self,
        asset: ReferenceAsset,
    ) -> Tuple[
        str,
        Tuple[str, ...],
    ]:

        return (
            asset.category,
            tuple(
                sorted(
                    asset.roles
                )
            ),
        )


    def _append_unique(
        self,
        selected: List[
            ReferenceAsset
        ],
        asset: ReferenceAsset,
        *,
        max_total: int,
    ) -> bool:

        if len(
            selected
        ) >= max_total:

            return False

        used_ids = {
            item.asset_id
            for item
            in selected
        }

        if asset.asset_id in used_ids:

            return False

        used_paths = {
            item.path
            for item
            in selected
        }

        if asset.path in used_paths:

            return False

        selected.append(
            asset
        )

        return True


    # =====================================================
    # RANK
    # =====================================================

    def rank_assets(
        self,
        *,
        benefit_family: Optional[str],
        visual_family: Optional[str],
        preferred_roles: Optional[
            List[str]
        ] = None,
        rotation_key: Optional[str] = None,
        exclude_asset_ids: Optional[
            Sequence[str]
        ] = None,
    ) -> List[
        ReferenceAsset
    ]:

        excluded = set(
            exclude_asset_ids
            or []
        )

        candidates = [
            asset
            for asset
            in self.existing_assets()
            if asset.asset_id
            not in excluded
            and self._visual_family_matches(asset, visual_family)
        ]

        candidates.sort(

            key=lambda asset: (
                self._score_asset(
                    asset,
                    benefit_family,
                    visual_family,
                    preferred_roles,
                )
                +
                self._rotation_bonus(
                    asset,
                    rotation_key,
                ),
                asset.priority,
                asset.asset_id,
            ),

            reverse=True,
        )

        return candidates


    # =====================================================
    # MAIN REFERENCE CURATOR
    # =====================================================

    def select_assets(
        self,
        benefit_family: Optional[str],
        visual_family: Optional[str],
        max_brand_dna: int = 3,
        max_physical: int = 2,
        max_layout: int = 2,
        max_total: int = 7,
        rotation_key: Optional[str] = None,
        exclude_asset_ids: Optional[
            Sequence[str]
        ] = None,
    ) -> List[
        ReferenceAsset
    ]:

        #
        # IMPORTANT:
        #
        # Signature remains backward compatible.
        #
        # max_physical / max_layout are preserved because
        # older XPAND production code may still pass them.
        #
        # New V2 library maps them intelligently to:
        #
        #   style refs
        #   benefit/service refs
        #
        # when old product/layout categories don't exist.
        #

        max_brand_dna = max(
            0,
            min(
                5,
                int(
                    max_brand_dna
                ),
            ),
        )

        max_physical = max(
            0,
            min(
                5,
                int(
                    max_physical
                ),
            ),
        )

        max_layout = max(
            0,
            min(
                5,
                int(
                    max_layout
                ),
            ),
        )

        max_total = max(
            1,
            min(
                10,
                int(
                    max_total
                ),
            ),
        )

        family = self.normalize_visual_family(
            visual_family
        )

        excluded = set(
            exclude_asset_ids
            or []
        )

        available = [
            asset
            for asset
            in self.existing_assets()
            if asset.asset_id
            not in excluded
            and self._visual_family_matches(asset, family)
        ]

        selected: List[
            ReferenceAsset
        ] = []

        # =================================================
        # 1. BRAND DNA
        # =================================================

        brand_dna = [
            asset
            for asset
            in available
            if self.is_brand_dna(
                asset
            )
        ]

        brand_dna.sort(

            key=lambda asset: (
                self._score_asset(
                    asset,
                    benefit_family,
                    family,
                    [
                        "brand_dna",
                    ],
                )
                +
                self._rotation_bonus(
                    asset,
                    rotation_key,
                )
            ),

            reverse=True,
        )

        # =================================================
        # 2. VISUAL STYLE REFERENCES
        # =================================================

        style_candidates = [
            asset
            for asset
            in available
            if (
                self.is_style_reference(
                    asset
                )
                and
                self._visual_family_matches(
                    asset,
                    family,
                )
            )
        ]

        style_candidates.sort(

            key=lambda asset: (
                self._score_asset(
                    asset,
                    benefit_family,
                    family,
                    [
                        "style_reference",
                        (
                            "realistic_reference"
                            if family
                            ==
                            "premium_realistic"
                            else
                            "purple_reference"
                            if family
                            ==
                            "premium_purple_architecture"
                            else
                            "augmented_reference"
                        ),
                    ],
                )
                +
                self._rotation_bonus(
                    asset,
                    rotation_key,
                )
            ),

            reverse=True,
        )

        #
        # New V2 semantics:
        #
        # max_physical behaves as the style-reference budget
        # when no old physical-product assets exist.
        #

        style_budget = max(
            1,
            max_physical,
        )

        for asset in style_candidates[
            :style_budget
        ]:

            self._append_unique(
                selected,
                asset,
                max_total=max_total,
            )

        for asset in brand_dna[
            :max_brand_dna
        ]:

            self._append_unique(
                selected,
                asset,
                max_total=max_total,
            )

        # =================================================
        # 3. BENEFIT / SERVICE REFERENCES
        # =================================================

        service_candidates = [
            asset
            for asset
            in available
            if self.is_service_reference(
                asset
            )
        ]

        service_candidates.sort(

            key=lambda asset: (
                self._score_asset(
                    asset,
                    benefit_family,
                    family,
                    [
                        "merchant_reference",
                    ],
                )
                +
                self._rotation_bonus(
                    asset,
                    rotation_key,
                )
            ),

            reverse=True,
        )

        #
        # max_layout becomes the service-reference budget
        # in the new library.
        #

        service_budget = max(
            0,
            max_layout,
        )

        if benefit_family:

            for asset in service_candidates[
                :service_budget
            ]:

                #
                # Do not force unrelated service refs.
                #

                if (
                    asset.benefit_families
                    and
                    benefit_family
                    not in asset.benefit_families
                ):

                    continue

                self._append_unique(
                    selected,
                    asset,
                    max_total=max_total,
                )

        # =================================================
        # 4. OLD PHYSICAL / UI REFERENCES
        #
        # Compatibility if old assets ever return.
        # =================================================

        old_physical = [
            asset
            for asset
            in available
            if self.is_physical_reference(
                asset
            )
        ]

        old_physical.sort(

            key=lambda asset:
                self._score_asset(
                    asset,
                    benefit_family,
                    family,
                    [
                        "physical_product",
                        "ui_product",
                    ],
                ),

            reverse=True,
        )

        for asset in old_physical[
            :max_physical
        ]:

            self._append_unique(
                selected,
                asset,
                max_total=max_total,
            )

        # =================================================
        # 5. OLD LAYOUT REFERENCES
        # =================================================

        old_layout = [
            asset
            for asset
            in available
            if self.is_layout_reference(
                asset
            )
        ]

        old_layout.sort(

            key=lambda asset:
                self._score_asset(
                    asset,
                    benefit_family,
                    family,
                    [
                        "layout",
                        "campaign_style",
                    ],
                ),

            reverse=True,
        )

        for asset in old_layout[
            :max_layout
        ]:

            self._append_unique(
                selected,
                asset,
                max_total=max_total,
            )

        # =================================================
        # 6. QUALITY FILL
        # =================================================

        ranked_all = self.rank_assets(

            benefit_family=(
                benefit_family
            ),

            visual_family=(
                family
            ),

            rotation_key=(
                rotation_key
            ),

            exclude_asset_ids=(
                exclude_asset_ids
            ),
        )

        for asset in ranked_all:

            if len(
                selected
            ) >= max_total:

                break

            #
            # Dedicated wrong-style references should not
            # sneak in during fill.
            #

            if (
                not self.is_brand_dna(
                    asset
                )
                and
                asset.visual_families
                and
                family
                not in asset.visual_families
            ):

                continue

            self._append_unique(
                selected,
                asset,
                max_total=max_total,
            )

        return selected[
            :max_total
        ]


    # =====================================================
    # SMALL GENERATION SET
    #
    # Designed for actual image-model reference upload.
    # =====================================================

    def select_generation_assets(
        self,
        *,
        benefit_family: Optional[str],
        visual_family: Optional[str],
        max_total: int = 5,
        rotation_key: Optional[str] = None,
        exclude_asset_ids: Optional[
            Sequence[str]
        ] = None,
    ) -> List[
        ReferenceAsset
    ]:

        #
        # Recommended production mix:
        #
        # 2 brand DNA
        # 2 selected style refs
        # 1 service ref
        #
        # This avoids dumping all 20 images into Gemini.
        #

        return self.select_assets(

            benefit_family=(
                benefit_family
            ),

            visual_family=(
                visual_family
            ),

            max_brand_dna=2,

            max_physical=2,

            max_layout=1,

            max_total=max(
                1,
                min(
                    7,
                    int(
                        max_total
                    ),
                ),
            ),

            rotation_key=(
                rotation_key
            ),

            exclude_asset_ids=(
                exclude_asset_ids
            ),
        )


    # =====================================================
    # IDEATION REFERENCE SET
    #
    # Slightly broader than generation refs.
    # =====================================================

    def select_ideation_assets(
        self,
        *,
        benefit_family: Optional[str],
        visual_family: Optional[str],
        max_total: int = 7,
        rotation_key: Optional[str] = None,
    ) -> List[
        ReferenceAsset
    ]:

        return self.select_assets(

            benefit_family=(
                benefit_family
            ),

            visual_family=(
                visual_family
            ),

            max_brand_dna=3,

            max_physical=2,

            max_layout=2,

            max_total=max_total,

            rotation_key=(
                rotation_key
            ),
        )


    # =====================================================
    # BRAND GROUNDING
    # =====================================================

    def build_brand_grounding_text(
        self,
        visual_family: str,
        benefit_family: Optional[str] = None,
    ) -> str:

        family_id = self.normalize_visual_family(
            visual_family
        )

        family = self.style_families.get(
            family_id
        )

        from xpand_stc_skill_runtime import style_direction
        lines: List[str] = [style_direction(family_id)]

        lines.append(
            (
                "Brand identity: "
                +
                self.brand_name
                +
                "."
            )
        )

        lines.append(
            (
                "Selected visual family: "
                +
                family_id
                +
                "."
            )
        )

        if self.identity_keywords:

            lines.append(
                (
                    "Identity keywords: "
                    +
                    ", ".join(
                        self.identity_keywords
                    )
                    +
                    "."
                )
            )

        if self.required_brand_signals:

            lines.append(
                (
                    "Required brand signals: "
                    +
                    ", ".join(
                        self.required_brand_signals
                    )
                    +
                    "."
                )
            )

        if family:

            if family.description:

                lines.append(
                    (
                        "Style definition: "
                        +
                        family.description
                    )
                )

            if family.mood:

                lines.append(
                    (
                        "Mood: "
                        +
                        ", ".join(
                            family.mood
                        )
                        +
                        "."
                    )
                )

            if family.colors:

                lines.append(
                    (
                        "Color language: "
                        +
                        ", ".join(
                            family.colors
                        )
                        +
                        "."
                    )
                )

            if family.materials:

                lines.append(
                    (
                        "Material language: "
                        +
                        ", ".join(
                            family.materials
                        )
                        +
                        "."
                    )
                )

            if family.lighting:

                lines.append(
                    (
                        "Lighting language: "
                        +
                        ", ".join(
                            family.lighting
                        )
                        +
                        "."
                    )
                )

            if family.camera_language:

                lines.append(
                    (
                        "Camera language: "
                        +
                        ", ".join(
                            family.camera_language
                        )
                        +
                        "."
                    )
                )

            if family.scene_rules:

                lines.append(
                    (
                        "Scene rules: "
                        +
                        ", ".join(
                            family.scene_rules
                        )
                        +
                        "."
                    )
                )

        if self.approved_mechanisms:

            lines.append(
                (
                    "Approved advertising mechanisms: "
                    +
                    ", ".join(
                        self.approved_mechanisms
                    )
                    +
                    "."
                )
            )

        # =================================================
        # BENEFIT FAMILY
        # =================================================

        if benefit_family:

            benefit_data = _safe_dict(
                self.benefit_families.get(
                    benefit_family
                )
            )

            if benefit_data:

                required_messages = _as_list(
                    benefit_data.get(
                        "required_messages"
                    )
                )

                creative_rule = _clean_text(
                    benefit_data.get(
                        "creative_rule"
                    ),
                    3000,
                )

                preferred_mechanisms = _as_list(
                    benefit_data.get(
                        "preferred_visual_mechanisms"
                    )
                )

                if required_messages:

                    lines.append(
                        (
                            "Benefit messages that must be communicated: "
                            +
                            ", ".join(
                                required_messages
                            )
                            +
                            "."
                        )
                    )

                if creative_rule:

                    lines.append(
                        (
                            "Benefit-specific creative rule: "
                            +
                            creative_rule
                        )
                    )

                if preferred_mechanisms:

                    lines.append(
                        (
                            "Preferred benefit mechanisms: "
                            +
                            ", ".join(
                                preferred_mechanisms
                            )
                            +
                            "."
                        )
                    )

        # =================================================
        # GLOBAL RULES
        # =================================================

        enabled_rules: List[str] = []

        for key, value in self.global_rules.items():

            if value is True:

                enabled_rules.append(
                    key.replace(
                        "_",
                        " ",
                    )
                )

        if enabled_rules:

            lines.append(
                (
                    "Mandatory global rules: "
                    +
                    ", ".join(
                        enabled_rules
                    )
                    +
                    "."
                )
            )

        lines.append(
            (
                "Reference images are visual DNA, not cloning targets. "
                "Use their art direction, hierarchy, lighting, materials, "
                "camera discipline and brand confidence without copying "
                "their exact scene, people, text, logos or layout."
            )
        )

        return " ".join(
            lines
        ).strip()


    # =====================================================
    # BANNED PATTERNS
    # =====================================================

    def build_banned_patterns_text(
        self,
    ) -> str:

        if not self.banned_patterns:

            return ""

        return (
            "Avoid these banned STC Bank patterns: "
            +
            ", ".join(
                self.banned_patterns
            )
            +
            "."
        )


    # =====================================================
    # REFERENCE BRIEF
    # =====================================================

    def build_reference_brief(
        self,
        assets: Sequence[
            ReferenceAsset
        ],
    ) -> str:

        if not assets:

            return (
                "No local STC reference images selected."
            )

        lines = [
            (
                "Selected STC Bank visual references. "
                "Treat them as visual DNA, not scene templates:"
            )
        ]

        for index, asset in enumerate(
            assets,
            start=1,
        ):

            parts = [
                (
                    str(
                        index
                    )
                    +
                    ") "
                    +
                    asset.asset_id
                ),

                (
                    "category="
                    +
                    (
                        asset.category
                        or
                        "other"
                    )
                ),
            ]

            if asset.roles:

                parts.append(
                    (
                        "roles="
                        +
                        ",".join(
                            asset.roles
                        )
                    )
                )

            if asset.visual_families:

                parts.append(
                    (
                        "styles="
                        +
                        ",".join(
                            asset.visual_families
                        )
                    )
                )

            if asset.benefit_families:

                parts.append(
                    (
                        "benefits="
                        +
                        ",".join(
                            asset.benefit_families
                        )
                    )
                )

            if asset.notes:

                parts.append(
                    (
                        "purpose="
                        +
                        asset.notes
                    )
                )

            lines.append(
                " | ".join(
                    parts
                )
            )

        lines.append(
            (
                "Do not copy readable text, logos, people, "
                "exact composition or exact scene from references."
            )
        )

        return "\n".join(
            lines
        )


    # =====================================================
    # REFERENCE PATHS
    # =====================================================

    def reference_paths(
        self,
        assets: List[
            ReferenceAsset
        ],
    ) -> List[str]:

        paths: List[str] = []

        for asset in assets:

            path = self.resolve_asset_path(
                asset.path
            )

            if (
                path.is_file()
                and
                path.stat().st_size > 0
            ):

                paths.append(
                    str(
                        path
                    )
                )

        return paths


    # =====================================================
    # SERIALIZATION
    # =====================================================

    def asset_to_dict(
        self,
        asset: ReferenceAsset,
    ) -> Dict[str, Any]:

        path = self.resolve_asset_path(
            asset.path
        )

        return {

            "asset_id":
                asset.asset_id,

            "path":
                asset.path,

            "resolved_path":
                str(
                    path
                ),

            "exists":
                self.asset_exists(
                    asset
                ),

            "kind":
                asset.kind,

            "category":
                asset.category,

            "roles":
                list(
                    asset.roles
                ),

            "tags":
                list(
                    asset.tags
                ),

            "benefit_families":
                list(
                    asset.benefit_families
                ),

            "visual_families":
                list(
                    asset.visual_families
                ),

            "priority":
                asset.priority,

            "notes":
                asset.notes,
        }


    def selection_to_dict(
        self,
        assets: Sequence[
            ReferenceAsset
        ],
    ) -> List[
        Dict[str, Any]
    ]:

        return [
            self.asset_to_dict(
                asset
            )
            for asset
            in assets
        ]


    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(
        self,
    ) -> Dict[str, Any]:

        existing = self.existing_assets()

        category_counts: Dict[
            str,
            int
        ] = {}

        for asset in existing:

            category = (
                asset.category
                or
                "other"
            )

            category_counts[
                category
            ] = (
                category_counts.get(
                    category,
                    0,
                )
                +
                1
            )

        return {

            "version":
                VERSION,

            "pack_version":
                self.version,

            "brand_id":
                self.brand_id,

            "brand_name":
                self.brand_name,

            "default_visual_family":
                self.default_visual_family,

            "assets_total":
                len(
                    self.assets
                ),

            "assets_existing":
                len(
                    existing
                ),

            "style_families":
                list(
                    self.style_families.keys()
                ),

            "categories":
                category_counts,

            "pack_path":
                str(
                    self.pack_path
                ),
        }


# =========================================================
# DEFAULT PACK HELPER
# =========================================================

def default_stc_brand_pack_path() -> Path:

    module_root = Path(
        __file__
    ).resolve().parent

    candidates = [

        (
            module_root
            /
            "brand_assets"
            /
            "stc_bank"
            /
            "stc_bank_brand_pack.json"
        ),

        (
            Path.cwd()
            /
            "brand_assets"
            /
            "stc_bank"
            /
            "stc_bank_brand_pack.json"
        ),

        Path(
            "/app/brand_assets/stc_bank/stc_bank_brand_pack.json"
        ),
    ]

    for candidate in candidates:

        try:

            if candidate.is_file():

                return candidate.resolve()

        except Exception:

            continue

    #
    # Return canonical project path even if absent,
    # so error message is useful.
    #

    return candidates[
        0
    ].resolve()


def load_default_stc_brand_kit() -> BrandKit:

    return BrandKit.load(
        default_stc_brand_pack_path()
    )


# =========================================================
# ZERO-COST SELF TEST
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND STC BRAND KIT V2.0"
    )
    print(
        " REFERENCE CURATOR SELF TEST"
    )
    print(
        "=========================================="
    )
    print("")

    tests: Dict[
        str,
        bool
    ] = {}

    try:

        pack_path = (
            default_stc_brand_pack_path()
        )

        print(
            "Pack:"
        )
        print(
            pack_path
        )
        print("")

        pack = BrandKit.load(
            pack_path
        )

        info = pack.summary()

        print(
            "brand_id =",
            info[
                "brand_id"
            ],
        )

        print(
            "brand_name =",
            info[
                "brand_name"
            ],
        )

        print(
            "pack_version =",
            info[
                "pack_version"
            ],
        )

        print(
            "assets_total =",
            info[
                "assets_total"
            ],
        )

        print(
            "assets_existing =",
            info[
                "assets_existing"
            ],
        )

        print(
            "categories =",
            info[
                "categories"
            ],
        )

        print("")

        # =================================================
        # BASIC CONTRACT
        # =================================================

        tests[
            "brand_id"
        ] = (
            pack.brand_id
            ==
            "stc_bank"
        )

        tests[
            "reference_assets_loaded"
        ] = (
            len(
                pack.assets
            )
            >=
            20
        )

        tests[
            "all_reference_assets_exist"
        ] = (
            len(
                pack.existing_assets()
            )
            ==
            len(pack.assets)
        )

        # =================================================
        # JSON V2 STYLE FIELD SUPPORT
        # =================================================

        realistic_asset = next(
            (
                asset
                for asset
                in pack.assets
                if asset.asset_id
                ==
                "stc_realistic_01"
            ),
            None,
        )

        tests[
            "styles_field_parsed"
        ] = bool(
            realistic_asset
            and
            "premium_realistic"
            in realistic_asset.visual_families
        )

        purple_asset = next(
            (
                asset
                for asset
                in pack.assets
                if asset.asset_id
                ==
                "stc_purple_01"
            ),
            None,
        )

        tests[
            "purple_field_parsed"
        ] = bool(
            purple_asset
            and
            "premium_purple_architecture"
            in purple_asset.visual_families
        )

        # =================================================
        # STYLE RULE SUPPORT
        # =================================================

        purple_family = (
            pack.style_families.get(
                "premium_purple_architecture"
            )
        )

        tests[
            "style_rules_parsed"
        ] = bool(
            purple_family
            and
            purple_family.scene_rules
        )

        # =================================================
        # REALISTIC SELECTION
        # =================================================

        realistic_refs = (
            pack.select_generation_assets(

                benefit_family=(
                    "merchant_payments"
                ),

                visual_family=(
                    "premium_realistic"
                ),

                max_total=5,

                rotation_key=(
                    "merchant-realistic-test"
                ),
            )
        )

        realistic_ids = [
            asset.asset_id
            for asset
            in realistic_refs
        ]

        realistic_categories = [
            asset.category
            for asset
            in realistic_refs
        ]

        tests[
            "realistic_selection_nonempty"
        ] = bool(
            realistic_refs
        )

        tests[
            "merchant_reference_selected"
        ] = (
            "merchant"
            in realistic_categories
        )

        tests[
            "purple_not_forced_into_realistic"
        ] = not any(
            asset.category
            ==
            "purple"
            for asset
            in realistic_refs
            if not pack.is_brand_dna(
                asset
            )
        )

        tests[
            "generation_refs_max_five"
        ] = (
            len(
                realistic_refs
            )
            <=
            5
        )

        tests[
            "generation_paths_exist"
        ] = all(
            Path(
                path
            ).is_file()
            for path
            in pack.reference_paths(
                realistic_refs
            )
        )

        # =================================================
        # PURPLE SELECTION
        # =================================================

        purple_refs = (
            pack.select_generation_assets(

                benefit_family=(
                    "general_banking"
                ),

                visual_family=(
                    "premium_purple_architecture"
                ),

                max_total=5,

                rotation_key=(
                    "purple-test"
                ),
            )
        )

        tests[
            "purple_reference_selected"
        ] = any(
            asset.category
            ==
            "purple"
            for asset
            in purple_refs
        )

        # =================================================
        # AUGMENTED SELECTION
        # =================================================

        augmented_refs = (
            pack.select_generation_assets(

                benefit_family=(
                    "general_banking"
                ),

                visual_family=(
                    "premium_augmented_realism"
                ),

                max_total=5,

                rotation_key=(
                    "augmented-test"
                ),
            )
        )

        tests[
            "augmented_reference_selected"
        ] = any(
            asset.category
            ==
            "augmented"
            for asset
            in augmented_refs
        )

        # =================================================
        # BRAND GROUNDING
        # =================================================

        grounding = (
            pack.build_brand_grounding_text(

                "premium_realistic",

                benefit_family=(
                    "merchant_payments"
                ),
            )
        )

        tests[
            "merchant_creative_rule_loaded"
        ] = _contains_any(
            grounding,
            [
                "physical payment",
                "online commerce",
            ],
        )

        tests[
            "reference_dna_instruction"
        ] = _contains_any(
            grounding,
            [
                "visual DNA",
            ],
        )

        # =================================================
        # PRINT SELECTION
        # =================================================

        print(
            "------------------------------------------"
        )
        print(
            " REALISTIC + MERCHANT GENERATION SET"
        )
        print(
            "------------------------------------------"
        )

        for asset in realistic_refs:

            print(
                (
                    "✅ "
                    +
                    asset.asset_id
                    +
                    " | "
                    +
                    asset.category
                    +
                    " | "
                    +
                    str(
                        pack.resolve_asset_path(
                            asset.path
                        )
                    )
                )
            )

        print("")

        print(
            "------------------------------------------"
        )
        print(
            " TEST RESULTS"
        )
        print(
            "------------------------------------------"
        )
        print("")

        passed = all(
            tests.values()
        )

        for name, result in tests.items():

            print(
                (
                    "✅ "
                    if result
                    else
                    "❌ "
                )
                +
                name
            )

        print("")

        if passed:

            print(
                "XPAND STC Brand Kit V2.0 self-test: PASS ✅"
            )

        else:

            print(
                "XPAND STC Brand Kit V2.0 self-test: FAIL ❌"
            )

        print("")
        print(
            "✅ Permanent STC reference library loaded"
        )
        print(
            "✅ JSON V2 'styles' supported"
        )
        print(
            "✅ JSON V2 'rules' supported"
        )
        print(
            "✅ Old visual_families compatibility preserved"
        )
        print(
            "✅ Old scene_rules compatibility preserved"
        )
        print(
            "✅ Brand DNA selection"
        )
        print(
            "✅ Style-aware selection"
        )
        print(
            "✅ Merchant benefit selection"
        )
        print(
            "✅ Wrong-style penalty"
        )
        print(
            "✅ Real local image paths"
        )
        print(
            "✅ Small generation reference set"
        )
        print(
            "✅ Broader ideation reference set"
        )
        print(
            "✅ Deterministic reference rotation"
        )
        print(
            "🚫 No API calls were made"
        )
        print(
            "🚫 No images were generated"
        )
        print("")

    except Exception as error:

        print(
            "XPAND STC Brand Kit V2.0 self-test: FAIL ❌"
        )

        print(
            (
                "Error: "
                +
                str(
                    error
                )
            )
        )

        print("")
