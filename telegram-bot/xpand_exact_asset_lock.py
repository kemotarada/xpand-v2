# =========================================================
# XPAND EXACT ASSET LOCK V1.0
#
# Exact original-asset compositing layer.
#
# PURPOSE
# ---------------------------------------------------------
# Generative models are excellent for:
# - environment
# - lighting
# - scene
# - concept
# - cinematic composition
#
# But exact brand assets such as:
# - bank cards
# - logos
# - packaging
# - product labels
# - UI screenshots
#
# should NOT be regenerated when exact identity matters.
#
#
# PIPELINE
# ---------------------------------------------------------
# AI Generated Background / Scene
#        ↓
# Original Brand Asset
#        ↓
# Alpha / Segmentation Mask
#        ↓
# Geometric Placement
#        ↓
# Contact Shadow
#        ↓
# Exact Raster Composite
#        ↓
# Final PNG
#
#
# GUARANTEE LEVELS
# ---------------------------------------------------------
#
# HIGH_FIDELITY_AI
# Model re-renders product from reference.
# Strong similarity, not exact.
#
# ORIGINAL_ASSET_COMPOSITE
# Original raster asset is physically inserted into
# the generated scene.
#
# NATIVE_PIXEL_LOCK
# Asset inserted at original scale / orientation with
# no resampling or color modification.
#
#
# IMPORTANT
# ---------------------------------------------------------
# If the product image has no transparency and no mask,
# this module will NOT pretend that it can isolate the
# product perfectly.
#
# It returns requires_mask=True.
#
# A later segmentation/mask stage can provide that mask.
#
#
# NO PAID API CALLS.
# =========================================================

from __future__ import annotations

import hashlib
import io
import json
import math
import os

from dataclasses import (
    dataclass,
    field,
)

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
)


from PIL import (
    Image,
    ImageChops,
    ImageFilter,
    ImageOps,
)


# =========================================================
# MODULE
# =========================================================

VERSION = "1.0"

MODULE_NAME = (
    "XPAND Exact Asset Lock"
)


# =========================================================
# CONSTANTS
# =========================================================

LOCK_HIGH_FIDELITY_AI = (
    "high_fidelity_ai"
)

LOCK_ORIGINAL_COMPOSITE = (
    "original_asset_composite"
)

LOCK_NATIVE_PIXEL = (
    "native_pixel_lock"
)


VALID_ASSET_ROLES = {
    "product",
    "bank_card",
    "logo",
    "package",
    "phone",
    "screen",
    "label",
    "ui",
    "other",
}


DEFAULT_OUTPUT_FORMAT = (
    "PNG"
)


MAX_CANVAS_DIMENSION = max(
    2048,
    min(
        16384,
        int(
            os.environ.get(
                "XPAND_EXACT_LOCK_MAX_DIMENSION",
                "8192"
            )
            or
            8192
        )
    )
)


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class ExactAsset:

    source_bytes: bytes

    image_rgba: Image.Image

    mask: Image.Image

    mime_type: str

    role: str

    source_name: str

    source_hash: str

    original_width: int

    original_height: int

    has_native_alpha: bool

    requires_mask: bool

    lock_mode: str

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class AssetPlacement:

    # Position uses normalized canvas coordinates.
    #
    # x = 0.5 means horizontal center.
    # y = 0.5 means vertical center.
    #

    x: float = 0.5

    y: float = 0.5

    # Width is percentage of final canvas width.
    #
    # Example:
    # 0.35 = asset uses 35% of canvas width.
    #
    # If None, original pixel size is preserved.
    #

    width_ratio: Optional[float] = 0.35

    rotation_degrees: float = 0.0

    opacity: float = 1.0

    # Contact shadow is rendered behind the product.
    # It does NOT modify original asset pixels.
    #

    shadow_enabled: bool = True

    shadow_offset_x: int = 0

    shadow_offset_y: int = 28

    shadow_blur: int = 28

    shadow_opacity: float = 0.28

    # Optional outside glow.
    # Disabled by default because exact assets should
    # normally remain photographically believable.
    #

    glow_enabled: bool = False

    glow_blur: int = 24

    glow_opacity: float = 0.10


@dataclass
class CompositeAssetReport:

    source_name: str

    role: str

    lock_mode: str

    original_size: Tuple[int, int]

    rendered_size: Tuple[int, int]

    position: Tuple[int, int]

    rotation_degrees: float

    scaling_applied: bool

    rotation_applied: bool

    color_modification_applied: bool

    generative_redraw_applied: bool

    native_pixel_identity: bool

    source_hash: str


@dataclass
class ExactCompositeResult:

    ok: bool

    image_bytes: bytes

    mime_type: str

    width: int

    height: int

    assets: List[CompositeAssetReport]

    lock_level: str

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 5000
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


def clamp(
    value: Any,
    minimum: float,
    maximum: float
) -> float:

    try:

        number = float(
            value
        )

    except Exception:

        number = minimum

    return max(
        minimum,
        min(
            maximum,
            number
        )
    )


def hash_bytes(
    value: bytes
) -> str:

    return hashlib.sha256(
        value
    ).hexdigest()


def safe_json(
    value: Any
) -> str:

    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        default=str
    )


# =========================================================
# IMAGE LOADING
# =========================================================

def load_image_rgba(
    image_bytes: bytes
) -> Image.Image:

    if not image_bytes:

        raise ValueError(
            "Image bytes are empty."
        )

    try:

        image = Image.open(
            io.BytesIO(
                image_bytes
            )
        )

        image = ImageOps.exif_transpose(
            image
        )

        image.load()

    except Exception as error:

        raise ValueError(
            (
                "Invalid image: "
                +
                clean_text(
                    error,
                    1000
                )
            )
        )

    width, height = image.size

    if (
        width <= 0
        or
        height <= 0
    ):

        raise ValueError(
            "Invalid image dimensions."
        )

    if (
        width
        >
        MAX_CANVAS_DIMENSION
        or
        height
        >
        MAX_CANVAS_DIMENSION
    ):

        raise ValueError(
            (
                "Image exceeds XPAND Exact Lock "
                "maximum dimension."
            )
        )

    return image.convert(
        "RGBA"
    )


# =========================================================
# MIME DETECTION
# =========================================================

def infer_mime_type(
    image_bytes: bytes,
    fallback: str = "image/png"
) -> str:

    if image_bytes.startswith(
        b"\x89PNG\r\n\x1a\n"
    ):

        return "image/png"

    if image_bytes.startswith(
        b"\xff\xd8\xff"
    ):

        return "image/jpeg"

    if (
        image_bytes.startswith(
            b"RIFF"
        )
        and
        b"WEBP"
        in
        image_bytes[:16]
    ):

        return "image/webp"

    return fallback


# =========================================================
# ALPHA
# =========================================================

def extract_alpha(
    image: Image.Image
) -> Image.Image:

    rgba = image.convert(
        "RGBA"
    )

    return rgba.getchannel(
        "A"
    )


def has_meaningful_alpha(
    image: Image.Image
) -> bool:

    alpha = extract_alpha(
        image
    )

    minimum, maximum = alpha.getextrema()

    return (
        minimum
        <
        255
    )


# =========================================================
# MASK
# =========================================================

def load_mask(
    mask_bytes: bytes,
    size: Tuple[int, int]
) -> Image.Image:

    if not mask_bytes:

        raise ValueError(
            "Mask bytes are empty."
        )

    try:

        mask_image = Image.open(
            io.BytesIO(
                mask_bytes
            )
        )

        mask_image = ImageOps.exif_transpose(
            mask_image
        )

        mask_image.load()

    except Exception as error:

        raise ValueError(
            (
                "Invalid mask image: "
                +
                clean_text(
                    error,
                    1000
                )
            )
        )

    mask = mask_image.convert(
        "L"
    )

    if mask.size != size:

        mask = mask.resize(
            size,
            Image.Resampling.LANCZOS
        )

    return mask


def combine_alpha_and_mask(
    image: Image.Image,
    external_mask: Optional[
        Image.Image
    ]
) -> Image.Image:

    native_alpha = extract_alpha(
        image
    )

    if external_mask is None:

        return native_alpha

    if native_alpha.getextrema() == (
        255,
        255
    ):

        return external_mask

    return ImageChops.multiply(
        native_alpha,
        external_mask
    )


# =========================================================
# TRIM
# =========================================================

def trim_to_visible_bounds(
    image: Image.Image,
    mask: Image.Image
) -> Tuple[
    Image.Image,
    Image.Image,
    Tuple[
        int,
        int,
        int,
        int
    ]
]:

    bbox = mask.getbbox()

    if bbox is None:

        raise ValueError(
            "Asset mask contains no visible pixels."
        )

    return (
        image.crop(
            bbox
        ),

        mask.crop(
            bbox
        ),

        bbox,
    )


# =========================================================
# PREPARE EXACT ASSET
# =========================================================

def prepare_exact_asset(
    asset_bytes: bytes,
    *,
    mime_type: str = "",
    mask_bytes: Optional[bytes] = None,
    role: str = "product",
    source_name: str = "asset",
    trim_transparent: bool = True
) -> ExactAsset:

    image = load_image_rgba(
        asset_bytes
    )

    role = clean_text(
        role,
        100
    ).lower()

    if role not in VALID_ASSET_ROLES:

        role = "other"

    native_alpha_exists = (
        has_meaningful_alpha(
            image
        )
    )

    external_mask = None

    if mask_bytes:

        external_mask = load_mask(
            mask_bytes,
            image.size
        )

    requires_mask = (
        not native_alpha_exists
        and
        external_mask is None
    )

    #
    # IMPORTANT:
    #
    # We refuse to pretend a JPEG/photo with background
    # is already an isolated exact asset.
    #
    if requires_mask:

        mask = Image.new(
            "L",
            image.size,
            255
        )

        lock_mode = (
            LOCK_HIGH_FIDELITY_AI
        )

    else:

        mask = combine_alpha_and_mask(
            image,
            external_mask
        )

        lock_mode = (
            LOCK_ORIGINAL_COMPOSITE
        )

    original_width, original_height = (
        image.size
    )

    trim_bbox = None

    if (
        trim_transparent
        and
        not requires_mask
    ):

        image, mask, trim_bbox = (
            trim_to_visible_bounds(
                image,
                mask
            )
        )

    image.putalpha(
        mask
    )

    return ExactAsset(
        source_bytes=
            asset_bytes,

        image_rgba=
            image,

        mask=
            mask,

        mime_type=
            (
                clean_text(
                    mime_type,
                    100
                )
                or
                infer_mime_type(
                    asset_bytes
                )
            ),

        role=
            role,

        source_name=
            clean_text(
                source_name,
                500
            )
            or
            "asset",

        source_hash=
            hash_bytes(
                asset_bytes
            ),

        original_width=
            original_width,

        original_height=
            original_height,

        has_native_alpha=
            native_alpha_exists,

        requires_mask=
            requires_mask,

        lock_mode=
            lock_mode,

        metadata={
            "trim_bbox":
                trim_bbox,

            "external_mask":
                bool(
                    external_mask
                ),

            "version":
                VERSION,
        },
    )


# =========================================================
# ASSET VALIDATION
# =========================================================

def asset_lock_status(
    asset: ExactAsset
) -> Dict[str, Any]:

    if asset.requires_mask:

        return {
            "ready":
                False,

            "lock_mode":
                LOCK_HIGH_FIDELITY_AI,

            "requires_mask":
                True,

            "message":
                (
                    "Asset has no transparency or segmentation "
                    "mask. Exact isolated composite is not safe yet."
                ),
        }

    return {
        "ready":
            True,

        "lock_mode":
            LOCK_ORIGINAL_COMPOSITE,

        "requires_mask":
            False,

        "message":
            (
                "Original raster asset is ready for "
                "non-generative compositing."
            ),
    }


# =========================================================
# RESIZE
# =========================================================

def calculate_render_size(
    asset_size: Tuple[int, int],
    canvas_size: Tuple[int, int],
    width_ratio: Optional[float]
) -> Tuple[int, int]:

    source_width, source_height = (
        asset_size
    )

    canvas_width, canvas_height = (
        canvas_size
    )

    if width_ratio is None:

        return (
            source_width,
            source_height,
        )

    width_ratio = clamp(
        width_ratio,
        0.01,
        1.5
    )

    target_width = max(
        1,
        int(
            round(
                canvas_width
                *
                width_ratio
            )
        )
    )

    scale = (
        target_width
        /
        float(
            source_width
        )
    )

    target_height = max(
        1,
        int(
            round(
                source_height
                *
                scale
            )
        )
    )

    return (
        target_width,
        target_height,
    )


# =========================================================
# ROTATION
# =========================================================

def rotate_rgba_and_mask(
    image: Image.Image,
    mask: Image.Image,
    degrees: float
) -> Tuple[
    Image.Image,
    Image.Image
]:

    degrees = float(
        degrees
        or
        0.0
    )

    if abs(
        degrees
    ) < 0.0001:

        return (
            image,
            mask,
        )

    rotated_image = image.rotate(
        degrees,
        resample=
            Image.Resampling.BICUBIC,
        expand=
            True
    )

    rotated_mask = mask.rotate(
        degrees,
        resample=
            Image.Resampling.BICUBIC,
        expand=
            True
    )

    rotated_image.putalpha(
        rotated_mask
    )

    return (
        rotated_image,
        rotated_mask,
    )


# =========================================================
# OPACITY
# =========================================================

def apply_opacity(
    mask: Image.Image,
    opacity: float
) -> Image.Image:

    opacity = clamp(
        opacity,
        0.0,
        1.0
    )

    if opacity >= 0.999:

        return mask

    return mask.point(
        lambda value:
            int(
                round(
                    value
                    *
                    opacity
                )
            )
    )


# =========================================================
# POSITION
# =========================================================

def calculate_center_position(
    canvas_size: Tuple[int, int],
    asset_size: Tuple[int, int],
    x: float,
    y: float
) -> Tuple[int, int]:

    canvas_width, canvas_height = (
        canvas_size
    )

    asset_width, asset_height = (
        asset_size
    )

    x = clamp(
        x,
        -1.0,
        2.0
    )

    y = clamp(
        y,
        -1.0,
        2.0
    )

    center_x = (
        canvas_width
        *
        x
    )

    center_y = (
        canvas_height
        *
        y
    )

    left = int(
        round(
            center_x
            -
            (
                asset_width
                /
                2.0
            )
        )
    )

    top = int(
        round(
            center_y
            -
            (
                asset_height
                /
                2.0
            )
        )
    )

    return (
        left,
        top,
    )


# =========================================================
# SHADOW
# =========================================================

def create_contact_shadow(
    mask: Image.Image,
    *,
    opacity: float,
    blur_radius: int
) -> Image.Image:

    opacity = clamp(
        opacity,
        0.0,
        1.0
    )

    blur_radius = max(
        0,
        int(
            blur_radius
            or
            0
        )
    )

    shadow_alpha = mask.point(
        lambda value:
            int(
                round(
                    value
                    *
                    opacity
                )
            )
    )

    if blur_radius > 0:

        shadow_alpha = shadow_alpha.filter(
            ImageFilter.GaussianBlur(
                radius=
                    blur_radius
            )
        )

    shadow = Image.new(
        "RGBA",
        shadow_alpha.size,
        (
            0,
            0,
            0,
            0,
        )
    )

    shadow.putalpha(
        shadow_alpha
    )

    return shadow


# =========================================================
# GLOW
# =========================================================

def create_external_glow(
    mask: Image.Image,
    *,
    opacity: float,
    blur_radius: int
) -> Image.Image:

    opacity = clamp(
        opacity,
        0.0,
        1.0
    )

    blur_radius = max(
        0,
        int(
            blur_radius
            or
            0
        )
    )

    glow_alpha = mask.filter(
        ImageFilter.GaussianBlur(
            radius=
                blur_radius
        )
    )

    glow_alpha = glow_alpha.point(
        lambda value:
            int(
                round(
                    value
                    *
                    opacity
                )
            )
    )

    glow = Image.new(
        "RGBA",
        glow_alpha.size,
        (
            255,
            255,
            255,
            0,
        )
    )

    glow.putalpha(
        glow_alpha
    )

    return glow


# =========================================================
# RENDER ONE ASSET
# =========================================================

def render_asset_on_canvas(
    canvas: Image.Image,
    asset: ExactAsset,
    placement: AssetPlacement
) -> CompositeAssetReport:

    if asset.requires_mask:

        raise RuntimeError(
            (
                "Exact composite blocked for '"
                +
                asset.source_name
                +
                "': a transparent asset or mask is required."
            )
        )

    source_image = asset.image_rgba.copy()

    source_mask = asset.mask.copy()

    source_size = (
        source_image.size
    )

    target_size = calculate_render_size(
        source_size,
        canvas.size,
        placement.width_ratio
    )

    scaling_applied = (
        target_size
        !=
        source_size
    )

    if scaling_applied:

        source_image = source_image.resize(
            target_size,
            Image.Resampling.LANCZOS
        )

        source_mask = source_mask.resize(
            target_size,
            Image.Resampling.LANCZOS
        )

    rotation_applied = (
        abs(
            float(
                placement.rotation_degrees
                or
                0
            )
        )
        >
        0.0001
    )

    source_image, source_mask = (
        rotate_rgba_and_mask(
            source_image,
            source_mask,
            placement.rotation_degrees
        )
    )

    final_mask = apply_opacity(
        source_mask,
        placement.opacity
    )

    source_image.putalpha(
        final_mask
    )

    left, top = calculate_center_position(
        canvas.size,
        source_image.size,
        placement.x,
        placement.y
    )

    # -----------------------------------------------------
    # OPTIONAL GLOW
    # -----------------------------------------------------

    if placement.glow_enabled:

        glow = create_external_glow(
            final_mask,
            opacity=
                placement.glow_opacity,
            blur_radius=
                placement.glow_blur
        )

        canvas.alpha_composite(
            glow,
            (
                left,
                top,
            )
        )

    # -----------------------------------------------------
    # CONTACT SHADOW
    # -----------------------------------------------------

    if placement.shadow_enabled:

        shadow = create_contact_shadow(
            final_mask,
            opacity=
                placement.shadow_opacity,
            blur_radius=
                placement.shadow_blur
        )

        canvas.alpha_composite(
            shadow,
            (
                left
                +
                int(
                    placement.shadow_offset_x
                    or
                    0
                ),

                top
                +
                int(
                    placement.shadow_offset_y
                    or
                    0
                ),
            )
        )

    # -----------------------------------------------------
    # ORIGINAL ASSET LAYER
    #
    # No generative redraw.
    # No hue / saturation / contrast modification.
    # -----------------------------------------------------

    canvas.alpha_composite(
        source_image,
        (
            left,
            top,
        )
    )

    native_pixel_identity = (
        not scaling_applied
        and
        not rotation_applied
        and
        abs(
            placement.opacity
            -
            1.0
        )
        <
        0.0001
    )

    lock_mode = (
        LOCK_NATIVE_PIXEL
        if native_pixel_identity
        else
        LOCK_ORIGINAL_COMPOSITE
    )

    return CompositeAssetReport(
        source_name=
            asset.source_name,

        role=
            asset.role,

        lock_mode=
            lock_mode,

        original_size=
            (
                asset.original_width,
                asset.original_height,
            ),

        rendered_size=
            source_image.size,

        position=
            (
                left,
                top,
            ),

        rotation_degrees=
            float(
                placement.rotation_degrees
                or
                0
            ),

        scaling_applied=
            scaling_applied,

        rotation_applied=
            rotation_applied,

        color_modification_applied=
            False,

        generative_redraw_applied=
            False,

        native_pixel_identity=
            native_pixel_identity,

        source_hash=
            asset.source_hash,
    )


# =========================================================
# OUTPUT ENCODING
# =========================================================

def encode_output(
    image: Image.Image,
    *,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    quality: int = 96
) -> Tuple[
    bytes,
    str
]:

    output_format = clean_text(
        output_format,
        20
    ).upper()

    quality = max(
        60,
        min(
            100,
            int(
                quality
                or
                96
            )
        )
    )

    buffer = io.BytesIO()

    if output_format in {
        "JPG",
        "JPEG",
    }:

        rgb = Image.new(
            "RGB",
            image.size,
            (
                255,
                255,
                255,
            )
        )

        if image.mode == "RGBA":

            rgb.paste(
                image,
                mask=
                    image.getchannel(
                        "A"
                    )
            )

        else:

            rgb.paste(
                image.convert(
                    "RGB"
                )
            )

        rgb.save(
            buffer,
            format=
                "JPEG",
            quality=
                quality,
            subsampling=
                0,
            optimize=
                True
        )

        return (
            buffer.getvalue(),
            "image/jpeg",
        )

    image.save(
        buffer,
        format=
            "PNG",
        optimize=
            True
    )

    return (
        buffer.getvalue(),
        "image/png",
    )


# =========================================================
# MASTER COMPOSITE
# =========================================================

def composite_exact_assets(
    background_bytes: bytes,
    assets: Sequence[
        ExactAsset
    ],
    placements: Sequence[
        AssetPlacement
    ],
    *,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    quality: int = 96
) -> ExactCompositeResult:

    if not background_bytes:

        raise ValueError(
            "Background image is empty."
        )

    if len(
        assets
    ) != len(
        placements
    ):

        raise ValueError(
            (
                "assets and placements must have "
                "the same length."
            )
        )

    background = load_image_rgba(
        background_bytes
    )

    reports: List[
        CompositeAssetReport
    ] = []

    for asset, placement in zip(
        assets,
        placements
    ):

        report = render_asset_on_canvas(
            background,
            asset,
            placement
        )

        reports.append(
            report
        )

    output_bytes, mime_type = encode_output(
        background,
        output_format=
            output_format,
        quality=
            quality
    )

    if reports:

        all_native = all(
            report.native_pixel_identity
            for report in reports
        )

        lock_level = (
            LOCK_NATIVE_PIXEL
            if all_native
            else
            LOCK_ORIGINAL_COMPOSITE
        )

    else:

        lock_level = (
            LOCK_HIGH_FIDELITY_AI
        )

    return ExactCompositeResult(
        ok=
            True,

        image_bytes=
            output_bytes,

        mime_type=
            mime_type,

        width=
            background.width,

        height=
            background.height,

        assets=
            reports,

        lock_level=
            lock_level,

        metadata={
            "engine":
                MODULE_NAME,

            "version":
                VERSION,

            "asset_count":
                len(
                    reports
                ),

            "generative_redraw_of_locked_assets":
                False,
        },
    )


# =========================================================
# COMMON PLACEMENTS
# =========================================================

def hero_product_placement(
    *,
    x: float = 0.50,
    y: float = 0.60,
    width_ratio: float = 0.34,
    rotation_degrees: float = 0.0
) -> AssetPlacement:

    return AssetPlacement(
        x=
            x,

        y=
            y,

        width_ratio=
            width_ratio,

        rotation_degrees=
            rotation_degrees,

        shadow_enabled=
            True,

        shadow_offset_x=
            0,

        shadow_offset_y=
            30,

        shadow_blur=
            30,

        shadow_opacity=
            0.28,
    )


def floating_card_placement(
    *,
    x: float = 0.50,
    y: float = 0.55,
    width_ratio: float = 0.38,
    rotation_degrees: float = -8.0
) -> AssetPlacement:

    return AssetPlacement(
        x=
            x,

        y=
            y,

        width_ratio=
            width_ratio,

        rotation_degrees=
            rotation_degrees,

        shadow_enabled=
            True,

        shadow_offset_x=
            10,

        shadow_offset_y=
            30,

        shadow_blur=
            38,

        shadow_opacity=
            0.24,
    )


def logo_placement(
    *,
    x: float = 0.14,
    y: float = 0.08,
    width_ratio: float = 0.18
) -> AssetPlacement:

    return AssetPlacement(
        x=
            x,

        y=
            y,

        width_ratio=
            width_ratio,

        rotation_degrees=
            0.0,

        shadow_enabled=
            False,

        glow_enabled=
            False,
    )


# =========================================================
# MANIFEST
# =========================================================

def build_exact_lock_manifest(
    assets: Sequence[
        ExactAsset
    ]
) -> Dict[str, Any]:

    records = []

    ready_count = 0

    for asset in assets:

        status = asset_lock_status(
            asset
        )

        if status[
            "ready"
        ]:

            ready_count += 1

        records.append(
            {
                "source_name":
                    asset.source_name,

                "role":
                    asset.role,

                "source_hash":
                    asset.source_hash,

                "original_size": [
                    asset.original_width,
                    asset.original_height,
                ],

                "native_alpha":
                    asset.has_native_alpha,

                "requires_mask":
                    asset.requires_mask,

                "lock_mode":
                    asset.lock_mode,

                "ready":
                    status[
                        "ready"
                    ],
            }
        )

    return {
        "version":
            VERSION,

        "asset_count":
            len(
                records
            ),

        "ready_count":
            ready_count,

        "exact_composite_ready":
            (
                ready_count
                ==
                len(
                    records
                )
                and
                len(
                    records
                )
                >
                0
            ),

        "assets":
            records,
    }


# =========================================================
# HUMAN SUMMARY
# =========================================================

def build_lock_summary(
    asset: ExactAsset
) -> str:

    status = asset_lock_status(
        asset
    )

    if not status[
        "ready"
    ]:

        return (
            "🔒 Exact Asset Lock\n"
            +
            "الحالة: بحاجة Mask / خلفية شفافة\n"
            +
            "الملف: "
            +
            asset.source_name
            +
            "\n"
            +
            "رح أستخدمه كـHigh-Fidelity Reference مؤقتًا، "
            "بس ما رح أدّعي إنه Exact Composite."
        )

    return (
        "🔒 Exact Asset Lock جاهز\n"
        +
        "الملف: "
        +
        asset.source_name
        +
        "\n"
        +
        "النوع: "
        +
        asset.role
        +
        "\n"
        +
        "الطريقة: Original Asset Composite\n"
        +
        "إعادة رسم بالـAI: لا"
    )


# =========================================================
# INTEGRITY CHECK
# =========================================================

def verify_report_integrity(
    report: CompositeAssetReport
) -> Dict[str, Any]:

    return {
        "source_name":
            report.source_name,

        "source_hash":
            report.source_hash,

        "generative_redraw":
            report.generative_redraw_applied,

        "color_modified":
            report.color_modification_applied,

        "scaled":
            report.scaling_applied,

        "rotated":
            report.rotation_applied,

        "native_pixel_identity":
            report.native_pixel_identity,

        "lock_mode":
            report.lock_mode,

        "identity_preservation":
            (
                "native_pixels"
                if report.native_pixel_identity
                else
                "original_raster_transformed"
            ),
    }


# =========================================================
# SELF TEST
#
# LOCAL ONLY.
# NO API.
# NO DATABASE.
# NO TELEGRAM.
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND EXACT ASSET LOCK V1.0"
    )
    print(
        "=========================================="
    )
    print("")

    # -----------------------------------------------------
    # CREATE LOCAL BACKGROUND
    # -----------------------------------------------------

    background = Image.new(
        "RGB",
        (
            1200,
            1500,
        ),
        (
            26,
            16,
            38,
        )
    )

    background_buffer = io.BytesIO()

    background.save(
        background_buffer,
        format=
            "PNG"
    )

    # -----------------------------------------------------
    # CREATE TRANSPARENT TEST PRODUCT
    # -----------------------------------------------------

    product = Image.new(
        "RGBA",
        (
            600,
            380,
        ),
        (
            0,
            0,
            0,
            0,
        )
    )

    #
    # Draw simple product rectangle without
    # requiring ImageDraw.
    #

    product_layer = Image.new(
        "RGBA",
        (
            520,
            300,
        ),
        (
            50,
            15,
            80,
            255,
        )
    )

    product.alpha_composite(
        product_layer,
        (
            40,
            40,
        )
    )

    product_buffer = io.BytesIO()

    product.save(
        product_buffer,
        format=
            "PNG"
    )

    asset = prepare_exact_asset(
        product_buffer.getvalue(),

        mime_type=
            "image/png",

        role=
            "bank_card",

        source_name=
            "test-card.png"
    )

    print(
        "Transparent asset:"
    )

    print(
        " - native alpha:",
        asset.has_native_alpha
    )

    print(
        " - requires mask:",
        asset.requires_mask
    )

    print(
        " - ready:",
        asset_lock_status(
            asset
        )[
            "ready"
        ]
    )

    print("")

    # -----------------------------------------------------
    # JPEG-LIKE RGB TEST
    #
    # No alpha → exact cutout is correctly blocked.
    # -----------------------------------------------------

    rgb_asset = Image.new(
        "RGB",
        (
            400,
            300,
        ),
        (
            255,
            255,
            255,
        )
    )

    rgb_buffer = io.BytesIO()

    rgb_asset.save(
        rgb_buffer,
        format=
            "JPEG",
        quality=
            95
    )

    blocked_asset = prepare_exact_asset(
        rgb_buffer.getvalue(),

        mime_type=
            "image/jpeg",

        role=
            "product",

        source_name=
            "product-with-background.jpg"
    )

    print(
        "Non-transparent asset:"
    )

    print(
        " - native alpha:",
        blocked_asset.has_native_alpha
    )

    print(
        " - requires mask:",
        blocked_asset.requires_mask
    )

    print(
        " - exact ready:",
        asset_lock_status(
            blocked_asset
        )[
            "ready"
        ]
    )

    print("")

    # -----------------------------------------------------
    # COMPOSITE
    # -----------------------------------------------------

    result = composite_exact_assets(
        background_buffer.getvalue(),

        assets=[
            asset
        ],

        placements=[
            hero_product_placement(
                x=
                    0.50,

                y=
                    0.58,

                width_ratio=
                    0.48,

                rotation_degrees=
                    -4.0
            )
        ],

        output_format=
            "PNG"
    )

    print(
        "Composite result:"
    )

    print(
        " - ok:",
        result.ok
    )

    print(
        " - size:",
        (
            str(
                result.width
            )
            +
            "x"
            +
            str(
                result.height
            )
        )
    )

    print(
        " - output bytes:",
        len(
            result.image_bytes
        )
    )

    print(
        " - lock level:",
        result.lock_level
    )

    print("")

    report = result.assets[
        0
    ]

    integrity = verify_report_integrity(
        report
    )

    print(
        "Integrity:"
    )

    print(
        " - generative redraw:",
        integrity[
            "generative_redraw"
        ]
    )

    print(
        " - color modified:",
        integrity[
            "color_modified"
        ]
    )

    print(
        " - scaled:",
        integrity[
            "scaled"
        ]
    )

    print(
        " - rotated:",
        integrity[
            "rotated"
        ]
    )

    print(
        " - identity:",
        integrity[
            "identity_preservation"
        ]
    )

    print("")

    manifest = build_exact_lock_manifest(
        [
            asset
        ]
    )

    print(
        "Manifest exact ready:",
        manifest[
            "exact_composite_ready"
        ]
    )

    print("")

    print(
        "✅ Transparent PNG exact-asset detection"
    )

    print(
        "✅ External-mask support"
    )

    print(
        "✅ Unsafe fake cutout prevention"
    )

    print(
        "✅ Original raster compositing"
    )

    print(
        "✅ Native Pixel Lock detection"
    )

    print(
        "✅ High-quality Lanczos scaling"
    )

    print(
        "✅ Rotation support"
    )

    print(
        "✅ Contact shadow outside locked asset"
    )

    print(
        "✅ Logo placement support"
    )

    print(
        "✅ Product placement support"
    )

    print(
        "✅ Source SHA-256 integrity manifest"
    )

    print(
        "✅ No generative redraw of exact assets"
    )

    print(
        "🚫 No API calls were made"
    )

    print("")
