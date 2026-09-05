# =========================================================
# XPAND STC BANK BRAND PACK CHECKER V1.0
#
# Path:
#   telegram-bot/scripts/check_stc_brand_pack.py
#
# Purpose:
#   - Validate STC Bank brand pack JSON
#   - Validate all reference-image paths
#   - Detect missing / duplicated assets
#   - Validate expected reference categories
#   - Detect unsafe paths
#   - Basic image-file validation
#
# ZERO API COST
# NO IMAGE GENERATION
# =========================================================


from __future__ import annotations

import json
import sys

from collections import Counter

from pathlib import Path

from typing import (
    Any,
    Dict,
    List,
    Tuple,
)


# =========================================================
# IDENTITY
# =========================================================

VERSION = "1.0"

MODULE_NAME = "XPAND STC Bank Brand Pack Checker"


# =========================================================
# PROJECT PATHS
# =========================================================

SCRIPT_PATH = Path(
    __file__
).resolve()

SCRIPTS_DIR = (
    SCRIPT_PATH.parent
)

PROJECT_ROOT = (
    SCRIPTS_DIR.parent
)

BRAND_ASSETS_ROOT = (
    PROJECT_ROOT
    /
    "brand_assets"
)

STC_BANK_ROOT = (
    BRAND_ASSETS_ROOT
    /
    "stc_bank"
)

PACK_PATH = (
    STC_BANK_ROOT
    /
    "stc_bank_brand_pack.json"
)


# =========================================================
# EXPECTED STRUCTURE
# =========================================================

EXPECTED_DIRECTORIES = [
    "dna",
    "realistic",
    "purple",
    "augmented",
    "merchant",
]


MINIMUM_ASSET_COUNTS = {
    "dna": 5,
    "realistic": 5,
    "purple": 3,
    "augmented": 3,
    "merchant": 4,
}


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 5000,
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


def safe_dict(
    value: Any,
) -> Dict[str, Any]:

    if isinstance(
        value,
        dict,
    ):

        return value

    return {}


def safe_list(
    value: Any,
) -> List[Any]:

    if isinstance(
        value,
        list,
    ):

        return value

    return []


def relative_to_project(
    path: Path,
) -> str:

    try:

        return str(
            path.relative_to(
                PROJECT_ROOT
            )
        )

    except Exception:

        return str(
            path
        )


def print_header() -> None:

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND STC BANK BRAND PACK CHECKER V1.0"
    )
    print(
        "=========================================="
    )
    print("")

    print(
        "Project root:"
    )
    print(
        PROJECT_ROOT
    )

    print("")

    print(
        "Brand pack:"
    )
    print(
        PACK_PATH
    )

    print("")


# =========================================================
# JSON LOADER
# =========================================================

def load_pack() -> Tuple[
    Dict[str, Any],
    List[str],
]:

    errors: List[str] = []

    if not PACK_PATH.is_file():

        errors.append(
            (
                "Brand pack JSON is missing: "
                +
                str(
                    PACK_PATH
                )
            )
        )

        return (
            {},
            errors,
        )

    try:

        raw = PACK_PATH.read_text(
            encoding="utf-8"
        )

    except Exception as error:

        errors.append(
            (
                "Could not read brand pack JSON: "
                +
                clean_text(
                    error
                )
            )
        )

        return (
            {},
            errors,
        )

    try:

        payload = json.loads(
            raw
        )

    except Exception as error:

        errors.append(
            (
                "Invalid JSON: "
                +
                clean_text(
                    error
                )
            )
        )

        return (
            {},
            errors,
        )

    if not isinstance(
        payload,
        dict,
    ):

        errors.append(
            "Brand pack root must be a JSON object."
        )

        return (
            {},
            errors,
        )

    return (
        payload,
        errors,
    )


# =========================================================
# JSON STRUCTURE VALIDATION
# =========================================================

def validate_pack_structure(
    pack: Dict[str, Any],
) -> Tuple[
    List[str],
    List[str],
]:

    errors: List[str] = []

    warnings: List[str] = []

    required_string_fields = [
        "brand_id",
        "brand_name",
        "version",
        "default_visual_family",
    ]

    for field_name in required_string_fields:

        value = clean_text(
            pack.get(
                field_name
            )
        )

        if not value:

            errors.append(
                (
                    "Missing or empty JSON field: "
                    +
                    field_name
                )
            )

    if (
        clean_text(
            pack.get(
                "brand_id"
            )
        )
        !=
        "stc_bank"
    ):

        errors.append(
            (
                "brand_id must be exactly "
                "'stc_bank'."
            )
        )

    required_list_fields = [
        "identity_keywords",
        "required_brand_signals",
        "banned_patterns",
        "approved_visual_mechanisms",
        "assets",
    ]

    for field_name in required_list_fields:

        value = pack.get(
            field_name
        )

        if not isinstance(
            value,
            list,
        ):

            errors.append(
                (
                    "JSON field must be a list: "
                    +
                    field_name
                )
            )

    if not isinstance(
        pack.get(
            "global_rules"
        ),
        dict,
    ):

        errors.append(
            "global_rules must be a JSON object."
        )

    if not isinstance(
        pack.get(
            "style_families"
        ),
        dict,
    ):

        errors.append(
            "style_families must be a JSON object."
        )

    if not isinstance(
        pack.get(
            "benefit_families"
        ),
        dict,
    ):

        errors.append(
            "benefit_families must be a JSON object."
        )

    style_families = safe_dict(
        pack.get(
            "style_families"
        )
    )

    expected_styles = [
        "premium_realistic",
        "premium_purple_architecture",
        "premium_augmented_realism",
    ]

    for style_name in expected_styles:

        if style_name not in style_families:

            errors.append(
                (
                    "Missing STC visual family: "
                    +
                    style_name
                )
            )

    benefit_families = safe_dict(
        pack.get(
            "benefit_families"
        )
    )

    if (
        "merchant_payments"
        not in benefit_families
    ):

        errors.append(
            (
                "Missing benefit family: "
                "merchant_payments"
            )
        )

    assets = safe_list(
        pack.get(
            "assets"
        )
    )

    if len(
        assets
    ) < 20:

        warnings.append(
            (
                "Brand pack currently contains only "
                +
                str(
                    len(
                        assets
                    )
                )
                +
                " assets. Expected at least 20 "
                "for the current STC reference library."
            )
        )

    return (
        errors,
        warnings,
    )


# =========================================================
# DIRECTORY VALIDATION
# =========================================================

def validate_directories() -> List[str]:

    errors: List[str] = []

    if not BRAND_ASSETS_ROOT.is_dir():

        errors.append(
            (
                "Missing brand_assets directory: "
                +
                str(
                    BRAND_ASSETS_ROOT
                )
            )
        )

        return errors

    if not STC_BANK_ROOT.is_dir():

        errors.append(
            (
                "Missing STC Bank directory: "
                +
                str(
                    STC_BANK_ROOT
                )
            )
        )

        return errors

    for directory_name in EXPECTED_DIRECTORIES:

        directory_path = (
            STC_BANK_ROOT
            /
            directory_name
        )

        if not directory_path.is_dir():

            errors.append(
                (
                    "Missing directory: "
                    +
                    relative_to_project(
                        directory_path
                    )
                )
            )

    return errors


# =========================================================
# SAFE PATH
# =========================================================

def resolve_asset_path(
    relative_asset_path: str,
) -> Tuple[
    Path,
    bool,
]:

    #
    # JSON currently stores paths such as:
    #
    #   stc_bank/dna/stc_dna_01.jpg
    #
    # They are relative to:
    #
    #   brand_assets/
    #

    candidate = (
        BRAND_ASSETS_ROOT
        /
        relative_asset_path
    ).resolve()

    root = (
        BRAND_ASSETS_ROOT.resolve()
    )

    try:

        candidate.relative_to(
            root
        )

        safe = True

    except Exception:

        safe = False

    return (
        candidate,
        safe,
    )


# =========================================================
# BASIC IMAGE SIGNATURE
# =========================================================

def looks_like_real_image(
    path: Path,
) -> bool:

    try:

        with path.open(
            "rb"
        ) as handle:

            head = handle.read(
                32
            )

    except Exception:

        return False

    suffix = path.suffix.lower()

    #
    # JPEG
    #

    if suffix in {
        ".jpg",
        ".jpeg",
    }:

        return (
            len(
                head
            )
            >=
            3
            and
            head[:3]
            ==
            b"\xff\xd8\xff"
        )

    #
    # PNG
    #

    if suffix == ".png":

        return (
            head.startswith(
                b"\x89PNG\r\n\x1a\n"
            )
        )

    #
    # WEBP
    #

    if suffix == ".webp":

        return (
            len(
                head
            )
            >=
            12
            and
            head[:4]
            ==
            b"RIFF"
            and
            head[8:12]
            ==
            b"WEBP"
        )

    return False


# =========================================================
# ASSET VALIDATION
# =========================================================

def validate_assets(
    pack: Dict[str, Any],
) -> Tuple[
    List[str],
    List[str],
    Dict[str, int],
    int,
]:

    errors: List[str] = []

    warnings: List[str] = []

    assets = safe_list(
        pack.get(
            "assets"
        )
    )

    asset_ids: List[str] = []

    asset_paths: List[str] = []

    category_counts: Dict[
        str,
        int
    ] = {
        name: 0
        for name
        in EXPECTED_DIRECTORIES
    }

    valid_file_count = 0

    for index, raw_asset in enumerate(
        assets,
        start=1,
    ):

        if not isinstance(
            raw_asset,
            dict,
        ):

            errors.append(
                (
                    "Asset #"
                    +
                    str(
                        index
                    )
                    +
                    " is not a JSON object."
                )
            )

            continue

        asset_id = clean_text(
            raw_asset.get(
                "asset_id"
            ),
            300,
        )

        relative_path = clean_text(
            raw_asset.get(
                "path"
            ),
            1000,
        )

        kind = clean_text(
            raw_asset.get(
                "kind"
            ),
            100,
        )

        roles = safe_list(
            raw_asset.get(
                "roles"
            )
        )

        if not asset_id:

            errors.append(
                (
                    "Asset #"
                    +
                    str(
                        index
                    )
                    +
                    " has no asset_id."
                )
            )

        else:

            asset_ids.append(
                asset_id
            )

        if not relative_path:

            errors.append(
                (
                    "Asset "
                    +
                    (
                        asset_id
                        or
                        "#"
                        +
                        str(
                            index
                        )
                    )
                    +
                    " has no path."
                )
            )

            continue

        asset_paths.append(
            relative_path
        )

        if kind and kind != "image":

            warnings.append(
                (
                    asset_id
                    +
                    ": kind is '"
                    +
                    kind
                    +
                    "', expected 'image'."
                )
            )

        if not roles:

            warnings.append(
                (
                    asset_id
                    +
                    ": roles list is empty."
                )
            )

        normalized_path = (
            relative_path
            .replace(
                "\\",
                "/",
            )
            .strip("/")
        )

        parts = normalized_path.split(
            "/"
        )

        #
        # Expected:
        #
        # stc_bank/dna/file.jpg
        #

        if len(
            parts
        ) < 3:

            errors.append(
                (
                    asset_id
                    +
                    ": invalid asset path structure: "
                    +
                    relative_path
                )
            )

        elif parts[
            0
        ] != "stc_bank":

            errors.append(
                (
                    asset_id
                    +
                    ": path must start with "
                    "'stc_bank/': "
                    +
                    relative_path
                )
            )

        else:

            category = parts[
                1
            ]

            if category in category_counts:

                category_counts[
                    category
                ] += 1

            else:

                warnings.append(
                    (
                        asset_id
                        +
                        ": unknown STC asset category: "
                        +
                        category
                    )
                )

        resolved_path, safe_path = (
            resolve_asset_path(
                relative_path
            )
        )

        if not safe_path:

            errors.append(
                (
                    asset_id
                    +
                    ": unsafe path detected: "
                    +
                    relative_path
                )
            )

            continue

        extension = (
            resolved_path
            .suffix
            .lower()
        )

        if extension not in SUPPORTED_IMAGE_EXTENSIONS:

            errors.append(
                (
                    asset_id
                    +
                    ": unsupported image extension: "
                    +
                    extension
                )
            )

        if not resolved_path.is_file():

            errors.append(
                (
                    asset_id
                    +
                    ": image file is missing: "
                    +
                    relative_to_project(
                        resolved_path
                    )
                )
            )

            continue

        try:

            size_bytes = (
                resolved_path.stat().st_size
            )

        except Exception:

            size_bytes = 0

        if size_bytes <= 0:

            errors.append(
                (
                    asset_id
                    +
                    ": image file is empty: "
                    +
                    relative_to_project(
                        resolved_path
                    )
                )
            )

            continue

        if size_bytes < 10_000:

            warnings.append(
                (
                    asset_id
                    +
                    ": image file is unusually small ("
                    +
                    str(
                        size_bytes
                    )
                    +
                    " bytes)."
                )
            )

        if not looks_like_real_image(
            resolved_path
        ):

            errors.append(
                (
                    asset_id
                    +
                    ": file extension says image, "
                    "but image signature is invalid: "
                    +
                    relative_to_project(
                        resolved_path
                    )
                )
            )

            continue

        valid_file_count += 1

    # =====================================================
    # DUPLICATE IDS
    # =====================================================

    duplicate_ids = [
        item
        for item, count
        in Counter(
            asset_ids
        ).items()
        if count > 1
    ]

    for duplicate in duplicate_ids:

        errors.append(
            (
                "Duplicate asset_id: "
                +
                duplicate
            )
        )

    # =====================================================
    # DUPLICATE PATHS
    # =====================================================

    duplicate_paths = [
        item
        for item, count
        in Counter(
            asset_paths
        ).items()
        if count > 1
    ]

    for duplicate in duplicate_paths:

        errors.append(
            (
                "Duplicate asset path: "
                +
                duplicate
            )
        )

    # =====================================================
    # CATEGORY COUNTS
    # =====================================================

    for category, minimum in (
        MINIMUM_ASSET_COUNTS.items()
    ):

        current = category_counts.get(
            category,
            0,
        )

        if current < minimum:

            errors.append(
                (
                    "Category '"
                    +
                    category
                    +
                    "' contains "
                    +
                    str(
                        current
                    )
                    +
                    " manifest assets; expected at least "
                    +
                    str(
                        minimum
                    )
                    +
                    "."
                )
            )

    return (
        errors,
        warnings,
        category_counts,
        valid_file_count,
    )


# =========================================================
# UNREGISTERED IMAGES
# =========================================================

def find_unregistered_images(
    pack: Dict[str, Any],
) -> List[str]:

    warnings: List[str] = []

    manifest_paths = set()

    for asset in safe_list(
        pack.get(
            "assets"
        )
    ):

        if not isinstance(
            asset,
            dict,
        ):

            continue

        path_value = clean_text(
            asset.get(
                "path"
            ),
            1000,
        )

        if path_value:

            manifest_paths.add(
                path_value
                .replace(
                    "\\",
                    "/",
                )
                .strip("/")
            )

    for directory_name in EXPECTED_DIRECTORIES:

        directory = (
            STC_BANK_ROOT
            /
            directory_name
        )

        if not directory.is_dir():

            continue

        for file_path in directory.iterdir():

            if not file_path.is_file():

                continue

            if (
                file_path.suffix.lower()
                not in
                SUPPORTED_IMAGE_EXTENSIONS
            ):

                continue

            manifest_form = (
                "stc_bank/"
                +
                directory_name
                +
                "/"
                +
                file_path.name
            )

            if (
                manifest_form
                not in
                manifest_paths
            ):

                warnings.append(
                    (
                        "Image exists in GitHub but is not "
                        "registered in JSON: "
                        +
                        relative_to_project(
                            file_path
                        )
                    )
                )

    return warnings


# =========================================================
# PRINT RESULTS
# =========================================================

def print_results(
    *,
    pack: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
    category_counts: Dict[str, int],
    valid_file_count: int,
) -> None:

    print(
        "Brand:"
    )
    print(
        "  "
        +
        clean_text(
            pack.get(
                "brand_name"
            )
        )
    )

    print(
        "Version:"
    )
    print(
        "  "
        +
        clean_text(
            pack.get(
                "version"
            )
        )
    )

    print("")
    print(
        "Reference categories:"
    )

    for category in EXPECTED_DIRECTORIES:

        print(
            (
                "  "
                +
                category
                +
                ": "
                +
                str(
                    category_counts.get(
                        category,
                        0,
                    )
                )
            )
        )

    print("")

    print(
        "Valid image files:"
    )
    print(
        "  "
        +
        str(
            valid_file_count
        )
    )

    print("")

    if warnings:

        print(
            "------------------------------------------"
        )
        print(
            " WARNINGS"
        )
        print(
            "------------------------------------------"
        )
        print("")

        for warning in warnings:

            print(
                "⚠️ "
                +
                warning
            )

        print("")

    if errors:

        print(
            "------------------------------------------"
        )
        print(
            " ERRORS"
        )
        print(
            "------------------------------------------"
        )
        print("")

        for error in errors:

            print(
                "❌ "
                +
                error
            )

        print("")

        print(
            "=========================================="
        )
        print(
            " STC BRAND PACK CHECK: FAIL ❌"
        )
        print(
            "=========================================="
        )
        print("")

    else:

        print(
            "=========================================="
        )
        print(
            " STC BRAND PACK CHECK: PASS ✅"
        )
        print(
            "=========================================="
        )
        print("")

        print(
            "✅ JSON structure valid"
        )
        print(
            "✅ STC visual families available"
        )
        print(
            "✅ Merchant-payments family available"
        )
        print(
            "✅ Reference directories valid"
        )
        print(
            "✅ Reference paths valid"
        )
        print(
            "✅ No duplicate asset IDs"
        )
        print(
            "✅ No duplicate asset paths"
        )
        print(
            "✅ Image files exist"
        )
        print(
            "✅ Image signatures valid"
        )
        print(
            "✅ Permanent STC brand library is ready"
        )
        print(
            "🚫 No API calls were made"
        )
        print(
            "🚫 No images were generated"
        )
        print("")


# =========================================================
# MAIN
# =========================================================

def main() -> int:

    print_header()

    all_errors: List[str] = []

    all_warnings: List[str] = []

    directory_errors = (
        validate_directories()
    )

    all_errors.extend(
        directory_errors
    )

    pack, load_errors = (
        load_pack()
    )

    all_errors.extend(
        load_errors
    )

    if not pack:

        print_results(
            pack={},
            errors=all_errors,
            warnings=all_warnings,
            category_counts={},
            valid_file_count=0,
        )

        return 1

    structure_errors, structure_warnings = (
        validate_pack_structure(
            pack
        )
    )

    all_errors.extend(
        structure_errors
    )

    all_warnings.extend(
        structure_warnings
    )

    (
        asset_errors,
        asset_warnings,
        category_counts,
        valid_file_count,
    ) = validate_assets(
        pack
    )

    all_errors.extend(
        asset_errors
    )

    all_warnings.extend(
        asset_warnings
    )

    unregistered_warnings = (
        find_unregistered_images(
            pack
        )
    )

    all_warnings.extend(
        unregistered_warnings
    )

    #
    # Remove exact duplicate messages.
    #

    all_errors = list(
        dict.fromkeys(
            all_errors
        )
    )

    all_warnings = list(
        dict.fromkeys(
            all_warnings
        )
    )

    print_results(
        pack=pack,
        errors=all_errors,
        warnings=all_warnings,
        category_counts=category_counts,
        valid_file_count=valid_file_count,
    )

    return (
        1
        if all_errors
        else 0
    )


if __name__ == "__main__":

    sys.exit(
        main()
    )
