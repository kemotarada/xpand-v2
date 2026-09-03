# =========================================================
# XPAND PRODUCTION ENGINE V2.0
#
# Professional image-production orchestration for XPAND.
#
# FOUNDATION
# ---------------------------------------------------------
# Creative Brain
#      ↓
# Prompt Compiler
#      ↓
# Reference / Product Lock Loader
#      ↓
# Base Generation
#      ↓
# Composition Pass
#      ↓
# Product Fidelity Pass
#      ↓
# Lighting Pass
#      ↓
# Material Pass
#      ↓
# Final Polish
#      ↓
# Vision QA
#      ↓
# Automatic Correction Loop
#      ↓
# Best Final Image
#
#
# IMPLEMENTS
# ---------------------------------------------------------
# 1. Model-specific Prompt Compiler
# 2. High-Fidelity Product Reference Lock
# 3. Multi-Pass Generation
# 4. Camera Lock
# 5. Brand Lock
# 6. Composition Lock
# 7. Lighting Pass
# 8. Material Pass
# 9. Final Polish
# 10. Generated-image Vision QA
# 11. Weighted QA score /100
# 12. Automatic correction if score < target
# 13. Best-version preservation
# 14. Native high-resolution output mapping
#
#
# IMPORTANT
# ---------------------------------------------------------
# "Product Lock" here means high-fidelity reference-constrained
# generation/editing.
#
# It does NOT claim guaranteed pixel-identical reproduction.
#
# For truly exact logos/cards/packages:
# a later composite/inpainting stage must preserve the
# original asset instead of regenerating it.
#
#
# Current executable provider:
# - OpenAI GPT-Image-2
#
# Prompt compilers are also prepared for:
# - Gemini Image
# - Midjourney
# - FLUX
# - Ideogram
# - Runway
# - Kling
# - Seedance
#
# Those compilers do not claim provider execution unless
# an actual integration exists.
# =========================================================

from __future__ import annotations

import base64
import io
import json
import os
import re
import time
import uuid

from dataclasses import (
    dataclass,
    field,
)

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
)

import requests


# =========================================================
# XPAND EXISTING MODULES
# =========================================================

from xpand_image_engine import (
    OPENAI_API_KEY,
    OPENAI_IMAGE_MODEL,
    REQUEST_TIMEOUT,
    GeneratedImage,
    ImageRoute,
    PROVIDER_OPENAI,
    build_route,
    call_openai_director,
    generate_with_openai,
)

from xpand_brand_memory import (
    load_visual_references,
)


# =========================================================
# ENGINE
# =========================================================

ENGINE_NAME = (
    "XPAND Production Engine"
)

ENGINE_VERSION = (
    "2.0"
)


# =========================================================
# API
# =========================================================

OPENAI_IMAGE_EDITS_URL = (
    "https://api.openai.com/v1/images/edits"
)


# =========================================================
# MODES
# =========================================================

MODE_FAST = (
    "fast"
)

MODE_PRO = (
    "pro"
)

MODE_MASTERPIECE = (
    "masterpiece"
)


# =========================================================
# PROMPT TARGETS
# =========================================================

TARGET_OPENAI = (
    "openai"
)

TARGET_GEMINI = (
    "gemini"
)

TARGET_MIDJOURNEY = (
    "midjourney"
)

TARGET_FLUX = (
    "flux"
)

TARGET_IDEOGRAM = (
    "ideogram"
)

TARGET_RUNWAY = (
    "runway"
)

TARGET_KLING = (
    "kling"
)

TARGET_SEEDANCE = (
    "seedance"
)


# =========================================================
# QA
# =========================================================

QA_TARGET_SCORE = max(
    50,
    min(
        100,
        int(
            os.environ.get(
                "XPAND_IMAGE_QA_TARGET",
                "90"
            )
            or
            90
        )
    )
)


QA_MAX_CORRECTIONS = max(
    0,
    min(
        4,
        int(
            os.environ.get(
                "XPAND_IMAGE_QA_MAX_CORRECTIONS",
                "2"
            )
            or
            2
        )
    )
)


QA_WEIGHTS = {
    "concept_execution":
        10,

    "reference_adherence":
        10,

    "perspective":
        10,

    "product_fidelity":
        15,

    "lighting":
        10,

    "shadows":
        5,

    "reflections":
        5,

    "human_anatomy":
        5,

    "background_cleanliness":
        5,

    "brand_alignment":
        10,

    "text_logo_integrity":
        5,

    "advertising_readiness":
        10,
}


# =========================================================
# DATA CLASSES
# =========================================================

@dataclass
class ProductionReference:

    role: str

    image_bytes: bytes

    mime_type: str

    dna: Dict[str, Any] = field(
        default_factory=dict
    )

    product_lock: Dict[str, Any] = field(
        default_factory=dict
    )

    user_note: str = ""

    source_id: str = ""


@dataclass
class CompiledPrompt:

    target: str

    prompt: str

    negative_prompt: str

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class QAEvaluation:

    score: float

    scores: Dict[str, float]

    passed: bool

    strengths: List[str]

    problems: List[str]

    correction_instruction: str

    raw: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ProductionPassResult:

    pass_name: str

    image: GeneratedImage

    qa: Optional[QAEvaluation] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ProductionResult:

    ok: bool

    final_image: GeneratedImage

    best_score: float

    qa: Optional[QAEvaluation]

    passes: List[ProductionPassResult]

    compiled_prompt: CompiledPrompt

    references_used: int

    product_references_used: int

    elapsed_seconds: float

    errors: List[str] = field(
        default_factory=list
    )


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 20000
) -> str:

    return (
        str(
            value
            if value is not None
            else ""
        )
        .replace(
            "\x00",
            ""
        )
        .strip()[:limit]
    )


def clamp_score(
    value: Any
) -> float:

    try:

        number = float(
            value
        )

    except Exception:

        number = 0.0

    return max(
        0.0,
        min(
            100.0,
            number
        )
    )


def safe_json(
    value: Any,
    limit: int = 30000
) -> str:

    try:

        return clean_text(
            json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                default=str
            ),
            limit
        )

    except Exception:

        return clean_text(
            value,
            limit
        )


def extract_json_object(
    value: str
) -> Dict[str, Any]:

    text = clean_text(
        value,
        100000
    )

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:

        parsed = json.loads(
            text
        )

        if isinstance(
            parsed,
            dict
        ):

            return parsed

    except Exception:

        pass

    start = text.find(
        "{"
    )

    end = text.rfind(
        "}"
    )

    if (
        start >= 0
        and
        end > start
    ):

        try:

            parsed = json.loads(
                text[
                    start:end + 1
                ]
            )

            if isinstance(
                parsed,
                dict
            ):

                return parsed

        except Exception:

            pass

    return {}


# =========================================================
# IMAGE RESPONSE PARSING
# =========================================================

def decode_image_value(
    value: str
) -> Optional[bytes]:

    value = clean_text(
        value,
        100000000
    )

    if not value:

        return None

    if value.startswith(
        "data:image/"
    ):

        try:

            value = value.split(
                ",",
                1
            )[1]

        except Exception:

            return None

    try:

        result = base64.b64decode(
            value
        )

        return (
            result
            if result
            else
            None
        )

    except Exception:

        return None


def find_images_in_response(
    value: Any
) -> List[
    Tuple[
        bytes,
        str
    ]
]:

    found: List[
        Tuple[
            bytes,
            str
        ]
    ] = []

    def walk(
        item: Any
    ) -> None:

        if isinstance(
            item,
            dict
        ):

            mime_type = clean_text(
                (
                    item.get(
                        "mime_type"
                    )
                    or
                    item.get(
                        "mimeType"
                    )
                    or
                    ""
                ),
                100
            )

            for key in [
                "b64_json",
                "base64",
                "data",
            ]:

                raw_value = item.get(
                    key
                )

                if not isinstance(
                    raw_value,
                    str
                ):

                    continue

                raw = decode_image_value(
                    raw_value
                )

                if raw:

                    found.append(
                        (
                            raw,
                            mime_type
                            or
                            "image/png"
                        )
                    )

                    break

            for child in item.values():

                walk(
                    child
                )

        elif isinstance(
            item,
            list
        ):

            for child in item:

                walk(
                    child
                )

    walk(
        value
    )

    unique = []

    signatures = set()

    for raw, mime_type in found:

        signature = (
            len(
                raw
            ),
            raw[:64],
        )

        if signature in signatures:

            continue

        signatures.add(
            signature
        )

        unique.append(
            (
                raw,
                mime_type
            )
        )

    return unique


# =========================================================
# NATIVE OUTPUT RESOLUTION
#
# GPT-Image-2 supports flexible valid resolutions.
# These values keep both dimensions multiples of 16 and
# remain within the supported total-pixel ceiling.
# =========================================================

def production_size_for_ratio(
    aspect_ratio: str,
    *,
    final_quality: bool = True
) -> str:

    ratio = clean_text(
        aspect_ratio,
        30
    )

    if not final_quality:

        mapping = {
            "1:1":
                "1024x1024",

            "4:5":
                "1024x1280",

            "5:4":
                "1280x1024",

            "9:16":
                "1024x1792",

            "16:9":
                "1792x1024",

            "2:3":
                "1024x1536",

            "3:2":
                "1536x1024",

            "3:4":
                "1024x1360",

            "4:3":
                "1360x1024",
        }

        return mapping.get(
            ratio,
            "1024x1024"
        )

    #
    # High-resolution final outputs.
    #

    mapping = {
        "1:1":
            "2048x2048",

        "4:5":
            "2560x3200",

        "5:4":
            "3200x2560",

        "9:16":
            "2160x3840",

        "16:9":
            "3840x2160",

        "2:3":
            "2304x3456",

        "3:2":
            "3456x2304",

        "3:4":
            "2448x3264",

        "4:3":
            "3264x2448",

        "21:9":
            "3840x1648",
    }

    return mapping.get(
        ratio,
        "2048x2048"
    )


# =========================================================
# PROMPT COMPILER
# =========================================================

def base_negative_prompt() -> str:

    return (
        "avoid malformed anatomy, extra fingers, warped products, "
        "incorrect perspective, broken reflections, duplicated objects, "
        "random decorative elements, generic stock-photo composition, "
        "fake watermarks, random text, misspelled typography, "
        "unrequested logos, visual clutter, cheap CGI appearance"
    )


def compile_openai_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any
) -> CompiledPrompt:

    prompt = f"""
ORIGINAL REQUEST
================

{clean_text(request, 12000)}


APPROVED CREATIVE DIRECTION
===========================

{safe_json(creative_direction, 16000)}


BRAND MEMORY
============

{safe_json(brand_context, 14000)}


VISUAL REFERENCE DNA
====================

{safe_json(references, 14000)}


CAMERA LOCK
===========

{safe_json(camera_direction, 6000)}


PRODUCT LOCK
============

{safe_json(product_lock, 8000)}


OPENAI GPT-IMAGE EXECUTION RULES
================================

Create one world-class commercial advertising image.

Preserve the approved core concept.

Use the camera direction literally and coherently.

Maintain:
- physically plausible camera geometry
- premium commercial photography
- realistic material response
- believable contact shadows
- controlled reflections
- sophisticated depth
- clear visual hierarchy
- intentional negative space
- brand-consistent colors
- realistic human anatomy
- professional advertising finish

If product references are supplied:
- treat those images as the authoritative product identity
- preserve silhouette
- preserve proportions
- preserve corner geometry
- preserve material
- preserve color relationships
- preserve major graphic layout
- do not invent a different card/product/package
- redesign the environment around the product, not the product itself

Do not imitate one existing advertisement exactly.

Do not create a generic AI banking image.

The scene should feel intentionally art-directed and physically photographed.
""".strip()

    return CompiledPrompt(
        target=
            TARGET_OPENAI,

        prompt=
            prompt,

        negative_prompt=
            base_negative_prompt(),

        metadata={
            "compiler":
                "openai_gpt_image",

            "product_lock":
                bool(
                    product_lock
                ),
        }
    )


def compile_gemini_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any
) -> CompiledPrompt:

    prompt = f"""
TASK:
{clean_text(request, 12000)}

CREATIVE DIRECTION:
{safe_json(creative_direction, 16000)}

BRAND:
{safe_json(brand_context, 12000)}

REFERENCE DNA:
{safe_json(references, 12000)}

CAMERA:
{safe_json(camera_direction, 5000)}

LOCKED PRODUCT:
{safe_json(product_lock, 7000)}

Generate a premium photorealistic advertising key visual.

Prioritize semantic coherence and brand consistency.
Preserve locked product geometry and identity.
Use clean professional composition and realistic lighting.
Avoid generic banking clichés.
""".strip()

    return CompiledPrompt(
        target=
            TARGET_GEMINI,

        prompt=
            prompt,

        negative_prompt=
            base_negative_prompt(),

        metadata={
            "compiler":
                "gemini_image",
        }
    )


def compile_midjourney_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any
) -> CompiledPrompt:

    prompt = (
        clean_text(
            request,
            5000
        )
        +
        ", "
        +
        clean_text(
            safe_json(
                creative_direction,
                5000
            ),
            5000
        )
        +
        ", commercial advertising photography, "
        +
        "precise cinematic camera geometry, "
        +
        "premium realistic materials, controlled reflections, "
        +
        "professional lighting, intentional negative space"
    )

    return CompiledPrompt(
        target=
            TARGET_MIDJOURNEY,

        prompt=
            prompt,

        negative_prompt=
            (
                "generic banking icons, floating coins, "
                "deformed anatomy, warped product, random typography"
            ),

        metadata={
            "compiler":
                "midjourney",

            "execution_available":
                False,
        }
    )


def compile_flux_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any
) -> CompiledPrompt:

    prompt = f"""
{clean_text(request, 8000)}

Scene:
{safe_json(creative_direction, 10000)}

Camera:
{safe_json(camera_direction, 4000)}

Product constraints:
{safe_json(product_lock, 5000)}

Photorealistic high-end advertising photography.
Accurate geometry.
Controlled materials.
Clean commercial lighting.
""".strip()

    return CompiledPrompt(
        target=
            TARGET_FLUX,

        prompt=
            prompt,

        negative_prompt=
            base_negative_prompt(),

        metadata={
            "compiler":
                "flux",

            "execution_available":
                False,
        }
    )


def compile_ideogram_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any
) -> CompiledPrompt:

    return CompiledPrompt(
        target=
            TARGET_IDEOGRAM,

        prompt=f"""
Create a polished commercial campaign visual.

REQUEST:
{clean_text(request, 8000)}

CREATIVE:
{safe_json(creative_direction, 10000)}

BRAND:
{safe_json(brand_context, 8000)}

CAMERA:
{safe_json(camera_direction, 4000)}

If exact headline text is specified, prioritize spelling,
layout clarity and readable typography.
""".strip(),

        negative_prompt=
            base_negative_prompt(),

        metadata={
            "compiler":
                "ideogram",

            "execution_available":
                False,
        }
    )


def compile_video_prompt(
    target: str,
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    camera_direction: Any
) -> CompiledPrompt:

    prompt = f"""
ADVERTISING SCENE:
{clean_text(request, 8000)}

VISUAL DIRECTION:
{safe_json(creative_direction, 12000)}

BRAND:
{safe_json(brand_context, 8000)}

CAMERA:
{safe_json(camera_direction, 5000)}

Describe physically coherent movement,
camera motion, subject motion, lighting continuity,
material consistency and a clear opening/final frame.
""".strip()

    return CompiledPrompt(
        target=
            target,

        prompt=
            prompt,

        negative_prompt=
            (
                "camera teleportation, geometry morphing, "
                "warped hands, product deformation, flicker, "
                "identity drift"
            ),

        metadata={
            "compiler":
                target,

            "execution_available":
                False,
        }
    )


def compile_prompt(
    target: str,
    *,
    request: str,
    creative_direction: Any = None,
    brand_context: Any = None,
    references: Any = None,
    camera_direction: Any = None,
    product_lock: Any = None
) -> CompiledPrompt:

    target = clean_text(
        target,
        100
    ).lower()

    kwargs = {
        "request":
            request,

        "creative_direction":
            creative_direction
            or
            {},

        "brand_context":
            brand_context
            or
            {},

        "references":
            references
            or
            [],

        "camera_direction":
            camera_direction
            or
            {},

        "product_lock":
            product_lock
            or
            {},
    }

    if target == TARGET_GEMINI:

        return compile_gemini_prompt(
            **kwargs
        )

    if target == TARGET_MIDJOURNEY:

        return compile_midjourney_prompt(
            **kwargs
        )

    if target == TARGET_FLUX:

        return compile_flux_prompt(
            **kwargs
        )

    if target == TARGET_IDEOGRAM:

        return compile_ideogram_prompt(
            **kwargs
        )

    if target in {
        TARGET_RUNWAY,
        TARGET_KLING,
        TARGET_SEEDANCE,
    }:

        return compile_video_prompt(
            target,
            request=
                request,
            creative_direction=
                creative_direction
                or
                {},
            brand_context=
                brand_context
                or
                {},
            camera_direction=
                camera_direction
                or
                {}
        )

    return compile_openai_prompt(
        **kwargs
    )


# =========================================================
# REFERENCE LOADING
# =========================================================

def infer_mime_type(
    raw: bytes,
    fallback: str = "image/jpeg"
) -> str:

    if raw.startswith(
        b"\x89PNG\r\n\x1a\n"
    ):

        return "image/png"

    if raw.startswith(
        b"\xff\xd8\xff"
    ):

        return "image/jpeg"

    if raw.startswith(
        b"RIFF"
    ) and b"WEBP" in raw[:16]:

        return "image/webp"

    return fallback


def load_runtime_references(
    core,
    user_id,
    brand_id: str,
    *,
    limit: int = 12
) -> List[ProductionReference]:

    stored = load_visual_references(
        core,
        user_id,
        brand_id=
            brand_id,
        limit=
            limit
    )

    references: List[
        ProductionReference
    ] = []

    for item in stored:

        if not isinstance(
            item,
            dict
        ):

            continue

        file_id = clean_text(
            item.get(
                "telegram_file_id",
                ""
            ),
            1500
        )

        if not file_id:

            continue

        try:

            raw = core.get_telegram_file_bytes(
                file_id
            )

        except Exception as error:

            print(
                (
                    "⚠️ Reference download skipped: "
                    +
                    clean_text(
                        error,
                        1000
                    )
                )
            )

            continue

        if not raw:

            continue

        references.append(
            ProductionReference(
                role=
                    clean_text(
                        item.get(
                            "reference_role",
                            "style_reference"
                        ),
                        100
                    ),

                image_bytes=
                    raw,

                mime_type=
                    infer_mime_type(
                        raw
                    ),

                dna=
                    (
                        item.get(
                            "dna",
                            {}
                        )
                        if isinstance(
                            item.get(
                                "dna",
                                {}
                            ),
                            dict
                        )
                        else
                        {}
                    ),

                product_lock=
                    (
                        item.get(
                            "product_lock",
                            {}
                        )
                        if isinstance(
                            item.get(
                                "product_lock",
                                {}
                            ),
                            dict
                        )
                        else
                        {}
                    ),

                user_note=
                    clean_text(
                        item.get(
                            "user_note",
                            ""
                        ),
                        3000
                    ),

                source_id=
                    str(
                        item.get(
                            "id",
                            ""
                        )
                    ),
            )
        )

    return references


def product_references(
    references: Sequence[
        ProductionReference
    ]
) -> List[
    ProductionReference
]:

    return [
        item
        for item in references
        if item.role == "product_reference"
    ]


def reference_dna_payload(
    references: Sequence[
        ProductionReference
    ]
) -> List[Dict[str, Any]]:

    return [
        {
            "role":
                item.role,

            "dna":
                item.dna,

            "product_lock":
                item.product_lock,

            "user_note":
                item.user_note,
        }
        for item in references
    ]


def combined_product_lock(
    references: Sequence[
        ProductionReference
    ]
) -> Dict[str, Any]:

    locked: List[str] = []

    source_count = 0

    for item in references:

        if item.role != "product_reference":

            continue

        source_count += 1

        product_lock = item.product_lock

        if not isinstance(
            product_lock,
            dict
        ):

            continue

        values = product_lock.get(
            "must_remain_identical",
            []
        )

        if not isinstance(
            values,
            list
        ):

            continue

        for value in values:

            text = clean_text(
                value,
                500
            )

            if (
                text
                and
                text not in locked
            ):

                locked.append(
                    text
                )

    return {
        "enabled":
            bool(
                source_count
            ),

        "reference_count":
            source_count,

        "must_remain_identical":
            locked,

        "environment_may_change":
            True,

        "lighting_may_adapt":
            True,

        "lock_type":
            (
                "high_fidelity_reference"
                if source_count
                else
                "none"
            ),

        "exact_pixel_identity_guaranteed":
            False,
    }


# =========================================================
# MULTI-IMAGE GPT-IMAGE-2 EDIT
# =========================================================

def openai_multi_reference_edit(
    *,
    working_image: Optional[
        GeneratedImage
    ],
    references: Sequence[
        ProductionReference
    ],
    prompt: str,
    aspect_ratio: str,
    final_quality: bool,
    pass_name: str
) -> GeneratedImage:

    if not OPENAI_API_KEY:

        raise RuntimeError(
            "OPENAI_API_KEY missing."
        )

    files: List[
        Tuple[
            str,
            Tuple[
                str,
                bytes,
                str
            ]
        ]
    ] = []

    #
    # FIRST IMAGE:
    # current working composition.
    #

    if working_image is not None:

        files.append(
            (
                "image[]",
                (
                    "working-image"
                    +
                    working_image.extension,

                    working_image.image_bytes,

                    working_image.mime_type
                    or
                    "image/png",
                )
            )
        )

    #
    # FOLLOWING IMAGES:
    # authoritative product references only.
    #

    for index, reference in enumerate(
        references,
        start=1
    ):

        extension = (
            ".png"
            if reference.mime_type
            ==
            "image/png"
            else
            ".jpg"
        )

        files.append(
            (
                "image[]",
                (
                    (
                        "product-reference-"
                        +
                        str(
                            index
                        )
                        +
                        extension
                    ),

                    reference.image_bytes,

                    reference.mime_type,
                )
            )
        )

    if not files:

        raise RuntimeError(
            "No image input supplied to edit."
        )

    #
    # Official API supports:
    #
    # single image:
    #   image
    #
    # multiple images:
    #   image[]
    #
    if len(
        files
    ) == 1:

        field_name, file_tuple = (
            files[0]
        )

        files = [
            (
                "image",
                file_tuple
            )
        ]

    size = production_size_for_ratio(
        aspect_ratio,
        final_quality=
            final_quality
    )

    payload = {
        "model":
            OPENAI_IMAGE_MODEL,

        "prompt":
            clean_text(
                prompt,
                30000
            ),

        "size":
            size,

        "quality":
            (
                "high"
                if final_quality
                else
                "medium"
            ),

        "n":
            "1",
    }

    response = requests.post(
        OPENAI_IMAGE_EDITS_URL,

        headers={
            "Authorization":
                (
                    "Bearer "
                    +
                    OPENAI_API_KEY
                ),
        },

        data=
            payload,

        files=
            files,

        timeout=
            REQUEST_TIMEOUT
    )

    try:

        response_data = response.json()

    except Exception:

        response_data = {
            "raw":
                response.text
        }

    if not response.ok:

        error = response_data.get(
            "error"
        )

        if isinstance(
            error,
            dict
        ):

            message = (
                error.get(
                    "message"
                )
                or
                str(
                    error
                )
            )

        else:

            message = (
                error
                or
                response_data.get(
                    "raw"
                )
                or
                (
                    "HTTP "
                    +
                    str(
                        response.status_code
                    )
                )
            )

        raise RuntimeError(
            (
                "GPT-Image-2 edit failed: "
                +
                clean_text(
                    message,
                    3000
                )
            )
        )

    images = find_images_in_response(
        response_data
    )

    if not images:

        raise RuntimeError(
            "GPT-Image-2 edit returned no image."
        )

    image_bytes, mime_type = (
        images[0]
    )

    request_id = clean_text(
        response.headers.get(
            "x-request-id",
            ""
        ),
        300
    )

    if not request_id:

        request_id = (
            "prod-"
            +
            uuid.uuid4().hex[:12]
        )

    return GeneratedImage(
        image_bytes=
            image_bytes,

        mime_type=
            mime_type
            or
            "image/png",

        provider=
            "xpand_production",

        model=
            OPENAI_IMAGE_MODEL,

        prompt=
            prompt,

        original_prompt=
            prompt,

        aspect_ratio=
            aspect_ratio,

        image_size=
            size,

        quality=
            (
                "high"
                if final_quality
                else
                "medium"
            ),

        route_reason=
            (
                "XPAND Production Pass: "
                +
                pass_name
            ),

        request_id=
            request_id,

        metadata={
            "production_engine":
                ENGINE_VERSION,

            "pass_name":
                pass_name,

            "reference_images":
                len(
                    references
                ),

            "working_image_input":
                bool(
                    working_image
                ),
        },
    )


# =========================================================
# PRODUCTION PASS PROMPTS
# =========================================================

def composition_pass_prompt(
    compiled: CompiledPrompt,
    camera: Any,
    product_lock: Any
) -> str:

    return f"""
CURRENT TASK:
Refine the supplied image into the approved final composition.

MASTER BRIEF:
{compiled.prompt}

CAMERA LOCK:
{safe_json(camera, 6000)}

PRODUCT LOCK:
{safe_json(product_lock, 7000)}

CHANGE ONLY WHAT IMPROVES COMPOSITION:

- lock camera geometry
- lock horizon
- correct vanishing points
- improve foreground / midground / background separation
- improve visual hierarchy
- improve hero-product position
- establish intentional negative space
- remove distracting clutter
- preserve the approved concept

Do NOT add a new idea.
Do NOT redesign the locked product.
""".strip()


def product_pass_prompt(
    compiled: CompiledPrompt,
    product_lock: Any
) -> str:

    return f"""
PRODUCT FIDELITY PASS.

MASTER BRIEF:
{compiled.prompt}

LOCK:
{safe_json(product_lock, 10000)}

The supplied product reference images are authoritative.

Improve the current image while preserving:

- product silhouette
- proportions
- thickness
- corners
- major design geometry
- material
- color relationships
- major graphic placement

Correct:
- warped product edges
- wrong perspective
- inconsistent thickness
- impossible reflections
- bad hand/product contact

Environment can remain as designed.
Lighting can adapt naturally.

Do NOT invent another product.
""".strip()


def lighting_pass_prompt(
    compiled: CompiledPrompt
) -> str:

    return f"""
LIGHTING PASS.

MASTER BRIEF:
{compiled.prompt}

Preserve:
- subject identity
- product geometry
- camera
- composition
- environment structure

Improve only professional lighting behavior:

- motivated key light
- natural fill
- controlled rim / edge light
- realistic falloff
- contact shadows
- ambient occlusion
- believable reflections
- physically coherent highlights
- premium cinematic contrast
- brand-consistent color temperature

Avoid fake glow and excessive wet-looking reflections.
""".strip()


def material_pass_prompt(
    compiled: CompiledPrompt
) -> str:

    return f"""
MATERIAL REALISM PASS.

MASTER BRIEF:
{compiled.prompt}

Preserve camera and composition.

Improve physical realism of:

- metal
- glass
- plastic
- card surfaces
- fabric
- leather
- skin
- architecture
- floors
- walls

Correct:
- plastic-looking skin
- excessive gloss
- impossible reflections
- identical roughness across surfaces
- fake CGI texture

Use realistic microtexture,
roughness variation and physically believable reflections.
""".strip()


def polish_pass_prompt(
    compiled: CompiledPrompt
) -> str:

    return f"""
FINAL ADVERTISING POLISH.

MASTER BRIEF:
{compiled.prompt}

Do NOT redesign the scene.

Preserve all successful elements.

Final corrections only:

- clean artifacts
- improve fine detail
- correct anatomy
- fix edges
- remove random objects
- refine shadows
- refine reflections
- improve commercial color grade
- keep intentional negative space
- preserve locked product
- keep brand consistency
- improve premium campaign finish

The result must look publication-ready,
not like unfinished AI artwork.
""".strip()


# =========================================================
# INITIAL BASE GENERATION
# =========================================================

def generate_base_image(
    *,
    compiled: CompiledPrompt,
    product_refs: Sequence[
        ProductionReference
    ],
    aspect_ratio: str
) -> GeneratedImage:

    if product_refs:

        prompt = (
            compiled.prompt
            +
            "\n\n"
            "BASE GENERATION WITH PRODUCT REFERENCES:\n"
            "Use the attached product reference image(s) as "
            "the authoritative product identity. Build the new "
            "advertising environment around that product."
        )

        return openai_multi_reference_edit(
            working_image=
                None,

            references=
                product_refs,

            prompt=
                prompt,

            aspect_ratio=
                aspect_ratio,

            final_quality=
                False,

            pass_name=
                "concept_base_with_product_lock"
        )

    route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        "XPAND Production base generation.",
        aspect_ratio,
        "2K",
        "medium"
    )

    images = generate_with_openai(
        prompt=
            compiled.prompt,

        original_prompt=
            compiled.prompt,

        route=
            route,

        number=
            1
    )

    if not images:

        raise RuntimeError(
            "Base generation returned no image."
        )

    image = images[0]

    image.provider = (
        "xpand_production"
    )

    image.metadata[
        "production_engine"
    ] = ENGINE_VERSION

    image.metadata[
        "pass_name"
    ] = "concept_base"

    return image


# =========================================================
# QA PROMPT
# =========================================================

def build_qa_prompt(
    *,
    original_request: str,
    compiled_prompt: CompiledPrompt,
    image_metadata: Any,
    product_lock: Any,
    brand_context: Any
) -> str:

    return f"""
You are XPAND Final Visual QA Director.

Evaluate the attached generated advertising image.

Do NOT compliment automatically.

Do NOT expose private chain-of-thought.

Be strict enough for a premium international advertising campaign.

ORIGINAL REQUEST:
{clean_text(original_request, 12000)}

MASTER PRODUCTION BRIEF:
{clean_text(compiled_prompt.prompt, 16000)}

PRODUCT LOCK:
{safe_json(product_lock, 7000)}

BRAND CONTEXT:
{safe_json(brand_context, 10000)}

IMAGE METADATA:
{safe_json(image_metadata, 5000)}

Evaluate 0–100:

1. concept_execution
2. reference_adherence
3. perspective
4. product_fidelity
5. lighting
6. shadows
7. reflections
8. human_anatomy
9. background_cleanliness
10. brand_alignment
11. text_logo_integrity
12. advertising_readiness

IMPORTANT:

If no human appears:
human_anatomy = 100 unless an anatomical object is malformed.

If no readable text/logo is required:
text_logo_integrity should evaluate absence of random/broken text.

If no product reference was supplied:
product_fidelity evaluates product realism and consistency,
not exact reference matching.

Look specifically for:

- warped bank cards
- wrong card thickness
- distorted phones
- impossible fingers
- bad hand contact
- broken reflections
- wet-looking surfaces when not intended
- floating objects without physical logic
- bad perspective
- random decorative brand colors
- generic banking clichés
- unreadable Arabic
- fake logos
- clutter
- cheap CGI feeling

Return JSON only:

{{
  "scores": {{
    "concept_execution": 0,
    "reference_adherence": 0,
    "perspective": 0,
    "product_fidelity": 0,
    "lighting": 0,
    "shadows": 0,
    "reflections": 0,
    "human_anatomy": 0,
    "background_cleanliness": 0,
    "brand_alignment": 0,
    "text_logo_integrity": 0,
    "advertising_readiness": 0
  }},

  "strengths": [],

  "problems": [],

  "correction_instruction": ""
}}

Correction instruction must:
- fix only actual defects
- preserve successful elements
- preserve product identity
- preserve camera and concept unless they are defective
""".strip()


# =========================================================
# QA CALCULATION
# =========================================================

def calculate_qa_score(
    scores: Dict[str, Any]
) -> Tuple[
    float,
    Dict[str, float]
]:

    normalized_scores = {}

    total = 0.0

    for key, weight in QA_WEIGHTS.items():

        value = clamp_score(
            scores.get(
                key,
                0
            )
        )

        normalized_scores[
            key
        ] = value

        total += (
            value
            *
            (
                float(
                    weight
                )
                /
                100.0
            )
        )

    return (
        round(
            total,
            2
        ),
        normalized_scores
    )


# =========================================================
# VISION QA
# =========================================================

def evaluate_generated_image(
    *,
    image: GeneratedImage,
    original_request: str,
    compiled_prompt: CompiledPrompt,
    product_lock: Any,
    brand_context: Any
) -> QAEvaluation:

    qa_prompt = build_qa_prompt(
        original_request=
            original_request,

        compiled_prompt=
            compiled_prompt,

        image_metadata=
            image.metadata,

        product_lock=
            product_lock,

        brand_context=
            brand_context
    )

    raw = call_openai_director(
        qa_prompt,

        image_bytes=
            image.image_bytes,

        image_mime_type=
            image.mime_type
    )

    data = extract_json_object(
        raw
    )

    if not data:

        raise RuntimeError(
            "Visual QA returned invalid JSON."
        )

    scores_raw = data.get(
        "scores",
        {}
    )

    if not isinstance(
        scores_raw,
        dict
    ):

        scores_raw = {}

    score, scores = calculate_qa_score(
        scores_raw
    )

    strengths = data.get(
        "strengths",
        []
    )

    problems = data.get(
        "problems",
        []
    )

    if not isinstance(
        strengths,
        list
    ):

        strengths = []

    if not isinstance(
        problems,
        list
    ):

        problems = []

    return QAEvaluation(
        score=
            score,

        scores=
            scores,

        passed=
            (
                score
                >=
                QA_TARGET_SCORE
            ),

        strengths=[
            clean_text(
                item,
                1000
            )
            for item in strengths
            if clean_text(
                item,
                1000
            )
        ],

        problems=[
            clean_text(
                item,
                1000
            )
            for item in problems
            if clean_text(
                item,
                1000
            )
        ],

        correction_instruction=
            clean_text(
                data.get(
                    "correction_instruction",
                    ""
                ),
                6000
            ),

        raw=
            data,
    )


# =========================================================
# CORRECTION PASS
# =========================================================

def correction_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    product_lock: Any
) -> str:

    return f"""
QUALITY CORRECTION PASS.

CURRENT QA SCORE:
{qa.score}/100

TARGET:
{QA_TARGET_SCORE}/100 or higher.

DETECTED PROBLEMS:
{safe_json(qa.problems, 7000)}

QA CORRECTION INSTRUCTION:
{clean_text(qa.correction_instruction, 7000)}

PRODUCT LOCK:
{safe_json(product_lock, 7000)}

MASTER BRIEF:
{clean_text(compiled.prompt, 14000)}

RULES:

- Fix only the detected problems.
- Preserve all successful parts.
- Do not redesign the concept.
- Do not change the product identity.
- Do not change camera unless QA identified camera/perspective failure.
- Do not introduce new text.
- Do not add decorative objects.
- Improve realism and campaign readiness.
""".strip()


# =========================================================
# PRODUCTION PASS SELECTION
# =========================================================

def production_passes_for_mode(
    mode: str,
    *,
    has_product_reference: bool
) -> List[str]:

    mode = clean_text(
        mode,
        100
    ).lower()

    if mode == MODE_FAST:

        return [
            "final_polish",
        ]

    if mode == MODE_PRO:

        passes = [
            "composition",
        ]

        if has_product_reference:

            passes.append(
                "product"
            )

        passes.extend(
            [
                "lighting",
                "final_polish",
            ]
        )

        return passes

    passes = [
        "composition",
    ]

    if has_product_reference:

        passes.append(
            "product"
        )

    passes.extend(
        [
            "lighting",
            "materials",
            "final_polish",
        ]
    )

    return passes


# =========================================================
# RUN ONE PRODUCTION PASS
# =========================================================

def run_named_pass(
    *,
    pass_name: str,
    working_image: GeneratedImage,
    product_refs: Sequence[
        ProductionReference
    ],
    compiled: CompiledPrompt,
    camera_direction: Any,
    product_lock: Any,
    aspect_ratio: str,
    final_pass: bool
) -> GeneratedImage:

    if pass_name == "composition":

        prompt = composition_pass_prompt(
            compiled,
            camera_direction,
            product_lock
        )

    elif pass_name == "product":

        prompt = product_pass_prompt(
            compiled,
            product_lock
        )

    elif pass_name == "lighting":

        prompt = lighting_pass_prompt(
            compiled
        )

    elif pass_name == "materials":

        prompt = material_pass_prompt(
            compiled
        )

    else:

        prompt = polish_pass_prompt(
            compiled
        )

    return openai_multi_reference_edit(
        working_image=
            working_image,

        references=
            product_refs,

        prompt=
            prompt,

        aspect_ratio=
            aspect_ratio,

        final_quality=
            final_pass,

        pass_name=
            pass_name
    )


# =========================================================
# MASTER PRODUCTION PIPELINE
# =========================================================

def run_production(
    *,
    core,
    user_id,
    brand_id: str,
    original_request: str,
    creative_direction: Any,
    brand_context: Any,
    camera_direction: Any,
    aspect_ratio: str = "4:5",
    mode: str = MODE_MASTERPIECE,
    target_model: str = TARGET_OPENAI
) -> ProductionResult:

    started = time.monotonic()

    errors: List[str] = []

    references = load_runtime_references(
        core,
        user_id,
        brand_id,
        limit=
            12
    )

    product_refs = product_references(
        references
    )

    dna_payload = reference_dna_payload(
        references
    )

    product_lock = combined_product_lock(
        references
    )

    compiled = compile_prompt(
        target_model,

        request=
            original_request,

        creative_direction=
            creative_direction,

        brand_context=
            brand_context,

        references=
            dna_payload,

        camera_direction=
            camera_direction,

        product_lock=
            product_lock
    )

    if compiled.target != TARGET_OPENAI:

        raise RuntimeError(
            (
                "Execution for target '"
                +
                compiled.target
                +
                "' is not connected yet. "
                "Prompt compilation is available, "
                "but production execution is OpenAI-only in V2.0."
            )
        )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V2.0"
    )
    print(
        "=========================================="
    )

    print(
        "Mode:",
        mode
    )

    print(
        "Target:",
        compiled.target
    )

    print(
        "References:",
        len(
            references
        )
    )

    print(
        "Product references:",
        len(
            product_refs
        )
    )

    print(
        "Product Lock:",
        (
            "ACTIVE"
            if product_lock.get(
                "enabled"
            )
            else
            "none"
        )
    )

    print(
        "QA target:",
        QA_TARGET_SCORE
    )

    print("")

    # =====================================================
    # BASE
    # =====================================================

    print(
        "🎬 PASS 0: Concept Base..."
    )

    working = generate_base_image(
        compiled=
            compiled,

        product_refs=
            product_refs,

        aspect_ratio=
            aspect_ratio
    )

    passes: List[
        ProductionPassResult
    ] = [
        ProductionPassResult(
            pass_name=
                "concept_base",

            image=
                working,
        )
    ]

    print(
        "✅ PASS 0: Concept Base"
    )

    # =====================================================
    # MULTI-PASS
    # =====================================================

    pass_names = production_passes_for_mode(
        mode,
        has_product_reference=
            bool(
                product_refs
            )
    )

    for index, pass_name in enumerate(
        pass_names,
        start=1
    ):

        is_final_pass = (
            pass_name
            ==
            pass_names[-1]
        )

        print(
            (
                "🎨 PASS "
                +
                str(
                    index
                )
                +
                ": "
                +
                pass_name
                +
                "..."
            )
        )

        try:

            working = run_named_pass(
                pass_name=
                    pass_name,

                working_image=
                    working,

                product_refs=
                    product_refs,

                compiled=
                    compiled,

                camera_direction=
                    camera_direction,

                product_lock=
                    product_lock,

                aspect_ratio=
                    aspect_ratio,

                final_pass=
                    is_final_pass
            )

            passes.append(
                ProductionPassResult(
                    pass_name=
                        pass_name,

                    image=
                        working,
                )
            )

            print(
                (
                    "✅ PASS "
                    +
                    str(
                        index
                    )
                    +
                    ": "
                    +
                    pass_name
                )
            )

        except Exception as error:

            errors.append(
                (
                    pass_name
                    +
                    ": "
                    +
                    clean_text(
                        error,
                        3000
                    )
                )
            )

            print(
                (
                    "⚠️ PASS FAILED: "
                    +
                    pass_name
                    +
                    " | keeping previous successful image"
                )
            )

    # =====================================================
    # INITIAL QA
    # =====================================================

    print("")
    print(
        "👁️ FINAL VISUAL QA..."
    )

    best_image = (
        working
    )

    best_qa: Optional[
        QAEvaluation
    ] = None

    best_score = 0.0

    try:

        qa = evaluate_generated_image(
            image=
                working,

            original_request=
                original_request,

            compiled_prompt=
                compiled,

            product_lock=
                product_lock,

            brand_context=
                brand_context
        )

        best_qa = qa

        best_score = qa.score

        passes[-1].qa = qa

        print(
            (
                "📊 QA SCORE: "
                +
                str(
                    qa.score
                )
                +
                "/100"
            )
        )

    except Exception as error:

        errors.append(
            (
                "qa_initial: "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )

        print(
            (
                "⚠️ QA unavailable: "
                +
                clean_text(
                    error,
                    1000
                )
            )
        )

    # =====================================================
    # AUTO-CORRECTION LOOP
    # =====================================================

    correction_round = 0

    current_image = (
        working
    )

    current_qa = (
        best_qa
    )

    while (
        current_qa is not None
        and
        current_qa.score
        <
        QA_TARGET_SCORE
        and
        correction_round
        <
        QA_MAX_CORRECTIONS
    ):

        correction_round += 1

        print(
            (
                "🛠️ CORRECTION ROUND "
                +
                str(
                    correction_round
                )
                +
                "..."
            )
        )

        prompt = correction_prompt(
            qa=
                current_qa,

            compiled=
                compiled,

            product_lock=
                product_lock
        )

        try:

            corrected = openai_multi_reference_edit(
                working_image=
                    current_image,

                references=
                    product_refs,

                prompt=
                    prompt,

                aspect_ratio=
                    aspect_ratio,

                final_quality=
                    True,

                pass_name=
                    (
                        "qa_correction_"
                        +
                        str(
                            correction_round
                        )
                    )
            )

            corrected_qa = (
                evaluate_generated_image(
                    image=
                        corrected,

                    original_request=
                        original_request,

                    compiled_prompt=
                        compiled,

                    product_lock=
                        product_lock,

                    brand_context=
                        brand_context
                )
            )

            passes.append(
                ProductionPassResult(
                    pass_name=
                        (
                            "qa_correction_"
                            +
                            str(
                                correction_round
                            )
                        ),

                    image=
                        corrected,

                    qa=
                        corrected_qa,
                )
            )

            print(
                (
                    "📊 CORRECTED SCORE: "
                    +
                    str(
                        corrected_qa.score
                    )
                    +
                    "/100"
                )
            )

            #
            # NEVER lose the better image.
            #

            if (
                corrected_qa.score
                >
                best_score
            ):

                best_score = (
                    corrected_qa.score
                )

                best_image = (
                    corrected
                )

                best_qa = (
                    corrected_qa
                )

            current_image = (
                corrected
            )

            current_qa = (
                corrected_qa
            )

            if corrected_qa.passed:

                print(
                    "✅ QA TARGET REACHED"
                )

                break

        except Exception as error:

            errors.append(
                (
                    "qa_correction_"
                    +
                    str(
                        correction_round
                    )
                    +
                    ": "
                    +
                    clean_text(
                        error,
                        3000
                    )
                )
            )

            print(
                (
                    "⚠️ Correction failed; "
                    "keeping best previous version."
                )
            )

            break

    # =====================================================
    # FINAL METADATA
    # =====================================================

    best_image.provider = (
        "xpand_masterpiece"
        if mode == MODE_MASTERPIECE
        else
        "xpand_production"
    )

    best_image.model = (
        "XPAND Production V2 → "
        +
        OPENAI_IMAGE_MODEL
    )

    best_image.metadata[
        "production_engine"
    ] = ENGINE_VERSION

    best_image.metadata[
        "production_mode"
    ] = mode

    best_image.metadata[
        "qa_score"
    ] = best_score

    best_image.metadata[
        "qa_target"
    ] = QA_TARGET_SCORE

    best_image.metadata[
        "qa_passed"
    ] = bool(
        best_qa
        and
        best_qa.passed
    )

    best_image.metadata[
        "product_lock"
    ] = product_lock

    best_image.metadata[
        "production_passes"
    ] = [
        item.pass_name
        for item in passes
    ]

    elapsed = round(
        time.monotonic()
        -
        started,
        3
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND PRODUCTION COMPLETE"
    )
    print(
        "=========================================="
    )

    print(
        "Best score:",
        best_score
    )

    print(
        "Target:",
        QA_TARGET_SCORE
    )

    print(
        "Passes:",
        len(
            passes
        )
    )

    print(
        "Elapsed:",
        elapsed,
        "seconds"
    )

    print("")

    return ProductionResult(
        ok=
            True,

        final_image=
            best_image,

        best_score=
            best_score,

        qa=
            best_qa,

        passes=
            passes,

        compiled_prompt=
            compiled,

        references_used=
            len(
                references
            ),

        product_references_used=
            len(
                product_refs
            ),

        elapsed_seconds=
            elapsed,

        errors=
            errors,
    )


# =========================================================
# SELF TEST
#
# IMPORTANT:
# - NO API calls
# - NO image generation
# - NO database access
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V2.0"
    )
    print(
        "=========================================="
    )
    print("")

    print(
        "QA target:",
        QA_TARGET_SCORE
    )

    print(
        "QA max corrections:",
        QA_MAX_CORRECTIONS
    )

    print(
        "QA weights:",
        sum(
            QA_WEIGHTS.values()
        ),
        "%"
    )

    print("")

    for ratio in [
        "1:1",
        "4:5",
        "9:16",
        "16:9",
        "2:3",
        "3:2",
    ]:

        print(
            (
                ratio
                +
                " → "
                +
                production_size_for_ratio(
                    ratio,
                    final_quality=
                        True
                )
            )
        )

    print("")

    no_product = production_passes_for_mode(
        MODE_MASTERPIECE,
        has_product_reference=
            False
    )

    with_product = production_passes_for_mode(
        MODE_MASTERPIECE,
        has_product_reference=
            True
    )

    print(
        "Masterpiece without product reference:"
    )

    print(
        " - concept_base"
    )

    for value in no_product:

        print(
            " -",
            value
        )

    print("")

    print(
        "Masterpiece WITH product reference:"
    )

    print(
        " - concept_base_with_product_lock"
    )

    for value in with_product:

        print(
            " -",
            value
        )

    print("")

    dummy_compiler = compile_prompt(
        TARGET_OPENAI,

        request=
            (
                "STC Bank premium travel advertising scene"
            ),

        creative_direction={
            "idea":
                "test"
        },

        brand_context={
            "brand":
                "STC Bank"
        },

        references=[],

        camera_direction={
            "camera":
                "three-quarter hero"
        },

        product_lock={}
    )

    print(
        "Prompt compiler:",
        dummy_compiler.target
    )

    print("")

    print(
        "Prepared compilers:"
    )

    for target in [
        TARGET_OPENAI,
        TARGET_GEMINI,
        TARGET_MIDJOURNEY,
        TARGET_FLUX,
        TARGET_IDEOGRAM,
        TARGET_RUNWAY,
        TARGET_KLING,
        TARGET_SEEDANCE,
    ]:

        print(
            " -",
            target
        )

    print("")

    print(
        "✅ Model-specific Prompt Compiler"
    )

    print(
        "✅ High-Fidelity Product Reference Lock"
    )

    print(
        "✅ Multi-reference GPT-Image-2 editing"
    )

    print(
        "✅ Composition Pass"
    )

    print(
        "✅ Product Fidelity Pass"
    )

    print(
        "✅ Lighting Pass"
    )

    print(
        "✅ Material Pass"
    )

    print(
        "✅ Final Polish"
    )

    print(
        "✅ Vision QA /100"
    )

    print(
        "✅ QA threshold correction loop"
    )

    print(
        "✅ Best-version preservation"
    )

    print(
        "✅ High-resolution output mapping"
    )

    print(
        "🚫 No API calls were made"
    )

    print("")
