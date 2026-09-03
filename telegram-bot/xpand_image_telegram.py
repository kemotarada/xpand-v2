# =========================================================
# XPAND TELEGRAM IMAGE STUDIO V1.1
#
# Compatible with:
# - XPAND Smart Image Engine V1.3+
# - OpenAI GPT-Image-2
# - GPT-5.6 Sol visual director / critic
# - Nano Banana Pro
# - Nano Banana 2
# - OpenAI Fusion fallback
#
# Supports:
# - Natural Telegram text requests
# - Telegram voice requests
# - AUTO / FAST / PRO / BEST / COMPARE
# - Preview image
# - Original-quality document
# - PostgreSQL image metadata
# - Backward-compatible status keys
# =========================================================

from __future__ import annotations

import io
import os
import re

from typing import (
    Any,
    Dict,
    List,
    Optional,
)

import requests

from xpand_image_engine import (
    ENGINE_VERSION,
    generate_image,
    get_image_engine_status,
)


# =========================================================
# MODULE
# =========================================================

VERSION = "1.1"

MODULE_NAME = (
    "XPAND Telegram Image Studio"
)


# =========================================================
# SETTINGS
# =========================================================

SEND_PREVIEW = str(
    os.environ.get(
        "XPAND_IMAGE_SEND_PREVIEW",
        "true"
    )
).strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}


SEND_ORIGINAL = str(
    os.environ.get(
        "XPAND_IMAGE_SEND_ORIGINAL",
        "true"
    )
).strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}


MAX_GENERATED_IMAGES = max(
    1,
    min(
        4,
        int(
            os.environ.get(
                "XPAND_IMAGE_MAX_IMAGES",
                "4"
            )
            or
            4
        )
    )
)


TELEGRAM_TIMEOUT = max(
    60,
    int(
        os.environ.get(
            "XPAND_IMAGE_TELEGRAM_TIMEOUT",
            "240"
        )
        or
        240
    )
)


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 12000
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


def normalized(
    value: Any
) -> str:

    text = clean_text(
        value,
        12000
    ).lower()


    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    }


    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )


    text = re.sub(
        r"[\u064B-\u065F]",
        "",
        text
    )


    text = re.sub(
        r"\s+",
        " ",
        text
    )


    return text.strip()


def contains_any(
    text: str,
    markers: List[str]
) -> bool:

    source = normalized(
        text
    )


    return any(
        normalized(
            marker
        )
        in source
        for marker in markers
    )


# =========================================================
# IMAGE INTENT
# =========================================================

IMAGE_ACTION_MARKERS = [
    "اعمللي",
    "اعمل لي",
    "اعمل",
    "سويلي",
    "سوي لي",
    "سوي",
    "صمملي",
    "صمم لي",
    "صمم",
    "انشئ",
    "أنشئ",
    "ولدلي",
    "ولد لي",
    "ولد",
    "ولّد",
    "generate",
    "create",
    "design",
    "make",
]


IMAGE_ASSET_MARKERS = [
    "صوره",
    "صورة",
    "صور",
    "image",
    "picture",
    "بوستر",
    "poster",
    "اعلان",
    "إعلان",
    "advertisement",
    "ad",
    "بانر",
    "banner",
    "ثامبنيل",
    "thumbnail",
    "ستوري",
    "story",
    "كفر",
    "cover",
    "مشهد",
    "scene",
    "رندر",
    "render",
    "visual",
    "key visual",
    "منتج",
    "product",
]


IMAGE_QUESTION_MARKERS = [
    "اشرحلي",
    "اشرح لي",
    "شو افضل موديل",
    "شو أفضل موديل",
    "ايش افضل موديل",
    "أي موديل",
    "كيف بتشتغل",
    "كيف تعمل",
    "شو يعني",
    "ما معنى",
]


def looks_like_image_generation_request(
    text: str
) -> bool:

    value = clean_text(
        text,
        12000
    )


    if not value:

        return False


    source = normalized(
        value
    )


    if source.startswith(
        "/image"
    ):

        return True


    if contains_any(
        value,
        IMAGE_QUESTION_MARKERS
    ):

        return False


    has_action = contains_any(
        value,
        IMAGE_ACTION_MARKERS
    )


    has_asset = contains_any(
        value,
        IMAGE_ASSET_MARKERS
    )


    return (
        has_action
        and
        has_asset
    )


# =========================================================
# MODE DETECTION
# =========================================================

def detect_generation_mode(
    text: str
) -> str:

    if contains_any(
        text,
        [
            "compare",
            "قارن الموديلات",
            "قارنلي الموديلات",
            "كل موديل لحاله",
            "كل موديل لوحده",
            "نسخه من كل موديل",
            "نسخة من كل موديل",
        ]
    ):

        return "compare"


    if contains_any(
        text,
        [
            "best mode",
            "وضع best",
            "افضل نتيجه ممكنه",
            "أفضل نتيجة ممكنة",
            "اقوى نتيجه",
            "أقوى نتيجة",
            "اقوى شيء",
            "أقوى شيء",
            "اعلى مستوى ممكن",
            "أعلى مستوى ممكن",
            "كل قواك",
            "ultimate",
            "max quality",
        ]
    ):

        return "best"


    if contains_any(
        text,
        [
            "pro mode",
            "وضع pro",
            "fusion",
            "فيوجن",
        ]
    ):

        return "pro"


    if contains_any(
        text,
        [
            "gpt-image-2",
            "gpt image 2",
            "openai",
            "اوبن اي اي",
        ]
    ):

        return "openai"


    if contains_any(
        text,
        [
            "nano banana pro",
            "نانو بنانا برو",
            "gemini 3 pro image",
        ]
    ):

        return "google_pro"


    if contains_any(
        text,
        [
            "nano banana 2",
            "نانو بنانا 2",
            "gemini 3.1 flash image",
        ]
    ):

        return "google_fast"


    if contains_any(
        text,
        [
            "سريع",
            "fast mode",
            "وضع سريع",
        ]
    ):

        return "fast"


    return "auto"


# =========================================================
# IMAGE COUNT
# =========================================================

NUMBER_WORDS = {
    "واحد": 1,
    "واحده": 1,
    "وحده": 1,

    "اثنين": 2,
    "اتنين": 2,
    "ثنتين": 2,
    "صورتين": 2,

    "ثلاث": 3,
    "ثلاثه": 3,
    "ثلاثة": 3,

    "اربع": 4,
    "اربعه": 4,
    "أربع": 4,
    "أربعة": 4,
}


def detect_requested_image_count(
    text: str
) -> int:

    source = normalized(
        text
    )


    patterns = [
        (
            r"\b([1-4])\s*"
            r"(?:صور|صوره|صورة|نسخ|خيارات)\b"
        ),

        (
            r"\b(?:صور|نسخ|خيارات)\s*"
            r"([1-4])\b"
        ),
    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            source
        )


        if match:

            return max(
                1,
                min(
                    MAX_GENERATED_IMAGES,
                    int(
                        match.group(
                            1
                        )
                    )
                )
            )


    for marker, value in NUMBER_WORDS.items():

        if (
            normalized(
                marker
            )
            in
            source
            and
            contains_any(
                source,
                [
                    "صور",
                    "صوره",
                    "صورة",
                    "نسخ",
                    "خيارات",
                ]
            )
        ):

            return max(
                1,
                min(
                    MAX_GENERATED_IMAGES,
                    value
                )
            )


    return 1


# =========================================================
# PROMPT
# =========================================================

def extract_image_prompt(
    text: str
) -> str:

    value = clean_text(
        text,
        10000
    )


    if value.lower().startswith(
        "/image"
    ):

        value = value[
            len(
                "/image"
            ):
        ].strip()


    return value


# =========================================================
# TELEGRAM API
# =========================================================

def telegram_api_url(
    core,
    method: str
) -> str:

    token = clean_text(
        getattr(
            core,
            "TELEGRAM_BOT_TOKEN",
            ""
        ),
        1000
    )


    if not token:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN missing"
        )


    return (
        "https://api.telegram.org/bot"
        +
        token
        +
        "/"
        +
        method
    )


def send_photo_bytes(
    core,
    chat_id,
    image_bytes: bytes,
    filename: str,
    mime_type: str,
    caption: str
) -> Dict[str, Any]:

    buffer = io.BytesIO(
        image_bytes
    )


    buffer.name = filename


    response = requests.post(
        telegram_api_url(
            core,
            "sendPhoto"
        ),

        data={
            "chat_id":
                str(
                    chat_id
                ),

            "caption":
                clean_text(
                    caption,
                    1000
                ),
        },

        files={
            "photo": (
                filename,
                buffer,
                mime_type
                or
                "image/png"
            )
        },

        timeout=
            TELEGRAM_TIMEOUT
    )


    try:

        data = response.json()


    except Exception:

        data = {
            "ok":
                False,

            "description":
                response.text,
        }


    if (
        not response.ok
        or
        not data.get(
            "ok"
        )
    ):

        raise RuntimeError(
            (
                "Telegram sendPhoto failed: "
                +
                clean_text(
                    data,
                    3000
                )
            )
        )


    return data


def send_document_bytes(
    core,
    chat_id,
    image_bytes: bytes,
    filename: str,
    mime_type: str,
    caption: str
) -> Dict[str, Any]:

    buffer = io.BytesIO(
        image_bytes
    )


    buffer.name = filename


    response = requests.post(
        telegram_api_url(
            core,
            "sendDocument"
        ),

        data={
            "chat_id":
                str(
                    chat_id
                ),

            "caption":
                clean_text(
                    caption,
                    1000
                ),
        },

        files={
            "document": (
                filename,
                buffer,
                mime_type
                or
                "application/octet-stream"
            )
        },

        timeout=
            TELEGRAM_TIMEOUT
    )


    try:

        data = response.json()


    except Exception:

        data = {
            "ok":
                False,

            "description":
                response.text,
        }


    if (
        not response.ok
        or
        not data.get(
            "ok"
        )
    ):

        raise RuntimeError(
            (
                "Telegram sendDocument failed: "
                +
                clean_text(
                    data,
                    3000
                )
            )
        )


    return data


# =========================================================
# TELEGRAM FILE IDS
# =========================================================

def extract_photo_file_id(
    response: Dict[str, Any]
) -> str:

    photos = (
        response
        .get(
            "result",
            {}
        )
        .get(
            "photo",
            []
        )
    )


    if (
        not isinstance(
            photos,
            list
        )
        or
        not photos
    ):

        return ""


    return clean_text(
        photos[-1].get(
            "file_id"
        ),
        1000
    )


def extract_document_info(
    response: Dict[str, Any]
) -> Dict[str, str]:

    document = (
        response
        .get(
            "result",
            {}
        )
        .get(
            "document",
            {}
        )
    )


    if not isinstance(
        document,
        dict
    ):

        return {
            "file_id":
                "",

            "file_unique_id":
                "",
        }


    return {
        "file_id":
            clean_text(
                document.get(
                    "file_id"
                ),
                1000
            ),

        "file_unique_id":
            clean_text(
                document.get(
                    "file_unique_id"
                ),
                1000
            ),
    }


# =========================================================
# DATABASE
# =========================================================

def ensure_image_table(
    core
) -> None:

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS xpand_images (
                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    chat_id BIGINT NOT NULL,

                    provider TEXT NOT NULL,

                    model TEXT NOT NULL,

                    request_id TEXT NOT NULL DEFAULT '',

                    prompt TEXT NOT NULL,

                    enhanced_prompt TEXT NOT NULL DEFAULT '',

                    aspect_ratio TEXT NOT NULL DEFAULT '',

                    image_size TEXT NOT NULL DEFAULT '',

                    quality TEXT NOT NULL DEFAULT '',

                    mime_type TEXT NOT NULL DEFAULT '',

                    original_filename TEXT NOT NULL DEFAULT '',

                    byte_size BIGINT NOT NULL DEFAULT 0,

                    route_reason TEXT NOT NULL DEFAULT '',

                    telegram_photo_file_id TEXT NOT NULL DEFAULT '',

                    telegram_document_file_id TEXT NOT NULL DEFAULT '',

                    telegram_document_file_unique_id TEXT NOT NULL DEFAULT '',

                    source_channel TEXT NOT NULL DEFAULT 'telegram_text',

                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_xpand_images_user_created
                ON xpand_images(
                    user_id,
                    created_at DESC
                );
                """
            )


def save_image_record(
    core,
    *,
    user_id,
    chat_id,
    image,
    enhanced_prompt,
    photo_file_id,
    document_file_id,
    document_file_unique_id,
    source_channel
) -> Optional[int]:

    try:

        ensure_image_table(
            core
        )


        with core.db_connect() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO xpand_images
                    (
                        user_id,
                        chat_id,
                        provider,
                        model,
                        request_id,
                        prompt,
                        enhanced_prompt,
                        aspect_ratio,
                        image_size,
                        quality,
                        mime_type,
                        original_filename,
                        byte_size,
                        route_reason,
                        telegram_photo_file_id,
                        telegram_document_file_id,
                        telegram_document_file_unique_id,
                        source_channel
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id;
                    """,

                    (
                        user_id,

                        chat_id,

                        clean_text(
                            image.provider,
                            100
                        ),

                        clean_text(
                            image.model,
                            500
                        ),

                        clean_text(
                            image.request_id,
                            500
                        ),

                        clean_text(
                            image.original_prompt,
                            12000
                        ),

                        clean_text(
                            enhanced_prompt,
                            30000
                        ),

                        clean_text(
                            image.aspect_ratio,
                            50
                        ),

                        clean_text(
                            image.image_size,
                            100
                        ),

                        clean_text(
                            image.quality,
                            100
                        ),

                        clean_text(
                            image.mime_type,
                            100
                        ),

                        clean_text(
                            image.filename,
                            500
                        ),

                        len(
                            image.image_bytes
                        ),

                        clean_text(
                            image.route_reason,
                            3000
                        ),

                        clean_text(
                            photo_file_id,
                            1000
                        ),

                        clean_text(
                            document_file_id,
                            1000
                        ),

                        clean_text(
                            document_file_unique_id,
                            1000
                        ),

                        clean_text(
                            source_channel,
                            100
                        ),
                    )
                )


                row = cur.fetchone()


                return (
                    int(
                        row[0]
                    )
                    if row
                    else
                    None
                )


    except Exception as error:

        print(
            (
                "⚠️ XPAND image DB: "
                +
                str(
                    error
                )
            )
        )


        return None


# =========================================================
# PROVIDER LABEL
# =========================================================

def provider_label(
    provider: str,
    model: str
) -> str:

    provider = clean_text(
        provider,
        100
    )


    if provider == "openai":

        return "GPT-Image-2"


    if provider == "google_fast":

        return "Nano Banana 2"


    if provider == "google_pro":

        return "Nano Banana Pro"


    if provider == "fusion_pro":

        return (
            "PRO Fusion | "
            "Nano Banana Pro → GPT-Image-2"
        )


    if provider == "fusion_best":

        return (
            "BEST Fusion | "
            "Nano Banana Pro + OpenAI"
        )


    if provider == "openai_fusion":

        return (
            "BEST OpenAI Fusion | "
            "GPT-5.6 Sol + GPT-Image-2"
        )


    return clean_text(
        model,
        300
    )


# =========================================================
# DELIVERY
# =========================================================

def deliver_generated_image(
    core,
    *,
    chat_id,
    user_id,
    image,
    enhanced_prompt,
    source_channel,
    index,
    total
) -> Dict[str, Any]:

    label = provider_label(
        image.provider,
        image.model
    )


    counter = (
        (
            f" | {index}/{total}"
        )
        if total > 1
        else
        ""
    )


    caption = (
        "🎨 XPAND Image"
        +
        counter
        +
        "\n\n"
        +
        "المحرك: "
        +
        label
        +
        "\n"
        +
        "النسبة: "
        +
        clean_text(
            image.aspect_ratio,
            30
        )
        +
        "\n"
        +
        "الجودة: "
        +
        clean_text(
            image.image_size,
            50
        )
    )


    photo_file_id = ""

    document_file_id = ""

    document_file_unique_id = ""


    # -----------------------------------------------------
    # PREVIEW
    # -----------------------------------------------------

    if SEND_PREVIEW:

        try:

            photo_response = (
                send_photo_bytes(
                    core,
                    chat_id,
                    image.image_bytes,
                    image.filename,
                    image.mime_type,
                    caption
                )
            )


            photo_file_id = (
                extract_photo_file_id(
                    photo_response
                )
            )


        except Exception as error:

            #
            # Preview failure should never prevent
            # original-quality delivery.
            #

            print(
                (
                    "⚠️ XPAND image preview: "
                    +
                    str(
                        error
                    )
                )
            )


    # -----------------------------------------------------
    # ORIGINAL
    # -----------------------------------------------------

    if SEND_ORIGINAL:

        document_caption = (
            "📦 XPAND Original"
            +
            counter
            +
            "\n"
            +
            label
            +
            " | "
            +
            clean_text(
                image.aspect_ratio,
                30
            )
            +
            " | "
            +
            clean_text(
                image.image_size,
                50
            )
        )


        document_response = (
            send_document_bytes(
                core,
                chat_id,
                image.image_bytes,
                image.filename,
                image.mime_type,
                document_caption
            )
        )


        document_info = (
            extract_document_info(
                document_response
            )
        )


        document_file_id = (
            document_info[
                "file_id"
            ]
        )


        document_file_unique_id = (
            document_info[
                "file_unique_id"
            ]
        )


    image_db_id = (
        save_image_record(
            core,

            user_id=
                user_id,

            chat_id=
                chat_id,

            image=
                image,

            enhanced_prompt=
                enhanced_prompt,

            photo_file_id=
                photo_file_id,

            document_file_id=
                document_file_id,

            document_file_unique_id=
                document_file_unique_id,

            source_channel=
                source_channel
        )
    )


    return {
        "image_id":
            image_db_id,

        "provider":
            image.provider,

        "model":
            image.model,

        "filename":
            image.filename,

        "photo_file_id":
            photo_file_id,

        "document_file_id":
            document_file_id,
    }


# =========================================================
# GENERATE + DELIVER
# =========================================================

def generate_and_deliver(
    core,
    chat_id,
    user_id,
    text,
    source_channel="telegram_text"
) -> Dict[str, Any]:

    prompt = extract_image_prompt(
        text
    )


    if not prompt:

        raise RuntimeError(
            "اكتبلي وصف الصورة اللي بدك إياها."
        )


    mode = detect_generation_mode(
        prompt
    )


    number = detect_requested_image_count(
        prompt
    )


    try:

        core.send_action(
            chat_id,
            "upload_photo"
        )


    except Exception:

        pass


    print("")
    print(
        (
            "🎨 XPAND IMAGE REQUEST"
            +
            " | mode="
            +
            mode
            +
            " | count="
            +
            str(
                number
            )
        )
    )


    result = generate_image(
        prompt,

        mode=
            mode,

        number=
            number,

        allow_fallback=
            True,
    )


    if (
        not result.ok
        or
        not result.images
    ):

        raise RuntimeError(
            "ما رجعت صورة من محرك التوليد."
        )


    delivered: List[
        Dict[
            str,
            Any
        ]
    ] = []


    total = len(
        result.images
    )


    for index, image in enumerate(
        result.images,
        start=1
    ):

        try:

            core.send_action(
                chat_id,
                "upload_photo"
            )


        except Exception:

            pass


        delivered.append(
            deliver_generated_image(
                core,

                chat_id=
                    chat_id,

                user_id=
                    user_id,

                image=
                    image,

                enhanced_prompt=
                    result.enhanced_prompt,

                source_channel=
                    source_channel,

                index=
                    index,

                total=
                    total
            )
        )


    models: List[str] = []


    for image in result.images:

        model_name = provider_label(
            image.provider,
            image.model
        )


        if model_name not in models:

            models.append(
                model_name
            )


    summary = (
        "تم إنشاء صورة بواسطة XPAND Image Studio. "
        +
        "الوصف: "
        +
        clean_text(
            prompt,
            1000
        )
        +
        " | المحرك: "
        +
        ", ".join(
            models
        )
    )


    try:

        core.save_message(
            chat_id,
            "assistant",
            summary
        )


    except Exception as error:

        print(
            (
                "⚠️ Image conversation save: "
                +
                str(
                    error
                )
            )
        )


    try:

        core.record_event(
            user_id,
            chat_id,
            "image_generated",
            summary,
            {
                "mode":
                    mode,

                "selected_route":
                    clean_text(
                        getattr(
                            result,
                            "selected_route",
                            ""
                        ),
                        100
                    ),

                "number":
                    len(
                        result.images
                    ),

                "models":
                    models,

                "source_channel":
                    source_channel,

                "engine_version":
                    ENGINE_VERSION,

                "telegram_image_module":
                    VERSION,

                "image_ids":
                    [
                        item.get(
                            "image_id"
                        )
                        for item in delivered
                        if item.get(
                            "image_id"
                        )
                        is not None
                    ],
            }
        )


    except Exception as error:

        print(
            (
                "⚠️ Image event save: "
                +
                str(
                    error
                )
            )
        )


    print(
        (
            "✅ XPAND IMAGE DELIVERED"
            +
            " | images="
            +
            str(
                len(
                    result.images
                )
            )
            +
            " | engines="
            +
            ", ".join(
                models
            )
        )
    )


    return {
        "ok":
            True,

        "count":
            len(
                result.images
            ),

        "models":
            models,

        "delivered":
            delivered,

        "elapsed_seconds":
            result.elapsed_seconds,

        "errors":
            result.errors,

        "selected_route":
            getattr(
                result,
                "selected_route",
                ""
            ),
    }


# =========================================================
# TEXT HANDLER
# =========================================================

def handle_text_image_request(
    core,
    chat_id,
    user_id,
    text
) -> bool:

    if not looks_like_image_generation_request(
        text
    ):

        return False


    try:

        result = generate_and_deliver(
            core,
            chat_id,
            user_id,
            text,
            source_channel=
                "telegram_text"
        )


        if result.get(
            "errors"
        ):

            print(
                (
                    "⚠️ XPAND IMAGE PIPELINE INFO: "
                    +
                    str(
                        result[
                            "errors"
                        ]
                    )
                )
            )


    except Exception as error:

        print(
            (
                "❌ XPAND IMAGE TEXT: "
                +
                str(
                    error
                )
            )
        )


        try:

            core.record_event(
                user_id,
                chat_id,
                "image_generation_error",
                str(
                    error
                ),
                {
                    "source_channel":
                        "telegram_text"
                }
            )


        except Exception:

            pass


        core.send_message(
            chat_id,
            (
                "صار خلل بتوليد الصورة.\n"
                "ما رح أحكيلك إنها نجحت وهي ما نجحت.\n\n"
                "الخطأ: "
                +
                clean_text(
                    error,
                    1500
                )
            )
        )


    return True


# =========================================================
# STATUS COMPATIBILITY
# =========================================================

def status_flag(
    status: Dict[str, Any],
    key: str,
    fallback_key: str = ""
) -> bool:

    if key in status:

        return bool(
            status.get(
                key
            )
        )


    if fallback_key:

        return bool(
            status.get(
                fallback_key
            )
        )


    return False


def provider_ready(
    status: Dict[str, Any],
    provider_name: str
) -> bool:

    providers = status.get(
        "providers",
        {}
    )


    provider = providers.get(
        provider_name,
        {}
    )


    if not isinstance(
        provider,
        dict
    ):

        return False


    return bool(
        provider.get(
            "configured"
        )
    )


# =========================================================
# INSTALL
# =========================================================

def install(
    core
) -> Dict[str, Any]:

    if getattr(
        core,
        "_XPAND_IMAGE_TELEGRAM_INSTALLED",
        False
    ):

        return {
            "ok":
                True,

            "already_installed":
                True,
        }


    # =====================================================
    # TEXT HOOK
    # =====================================================

    original_handle_command = (
        core.handle_command
    )


    def xpand_image_handle_command(
        chat_id,
        user_id,
        text
    ):

        if handle_text_image_request(
            core,
            chat_id,
            user_id,
            text
        ):

            return True


        return original_handle_command(
            chat_id,
            user_id,
            text
        )


    core.handle_command = (
        xpand_image_handle_command
    )


    # =====================================================
    # VOICE HOOK
    # =====================================================

    original_ask = (
        core.ask_kemo
    )


    def xpand_image_ask(
        chat_id,
        user_id,
        user_message
    ):

        if looks_like_image_generation_request(
            user_message
        ):

            try:

                result = generate_and_deliver(
                    core,
                    chat_id,
                    user_id,
                    user_message,
                    source_channel=
                        "telegram_voice"
                )


                if result.get(
                    "selected_route"
                ) == "best":

                    return (
                        "تم. شغلت أقوى مسار للصور "
                        "وبعثتلك النتيجة النهائية عالشات."
                    )


                return (
                    "تم، ولّدتلك الصورة "
                    "وبعثتلك المعاينة والنسخة الأصلية."
                )


            except Exception as error:

                print(
                    (
                        "❌ XPAND IMAGE VOICE: "
                        +
                        str(
                            error
                        )
                    )
                )


                try:

                    core.record_event(
                        user_id,
                        chat_id,
                        "image_generation_error",
                        str(
                            error
                        ),
                        {
                            "source_channel":
                                "telegram_voice"
                        }
                    )


                except Exception:

                    pass


                return (
                    "صار خلل بتوليد الصورة، "
                    "وما رح أحكيلك إنها نجحت وهي ما نجحت."
                )


        return original_ask(
            chat_id,
            user_id,
            user_message
        )


    core.ask_kemo = (
        xpand_image_ask
    )


    core._XPAND_IMAGE_TELEGRAM_INSTALLED = (
        True
    )


    # =====================================================
    # STATUS
    # =====================================================

    status = get_image_engine_status()


    openai_ready = provider_ready(
        status,
        "openai"
    )


    nano_fast_ready = provider_ready(
        status,
        "google_fast"
    )


    nano_pro_ready = provider_ready(
        status,
        "google_pro"
    )


    #
    # IMPORTANT COMPATIBILITY FIX:
    #
    # Old engine:
    # supports_best_mode
    #
    # New V1.3:
    # supports_openai_fusion
    #
    best_ready = status_flag(
        status,
        "supports_best_mode",
        "supports_openai_fusion"
    )


    google_openai_fusion_ready = (
        status_flag(
            status,
            "supports_google_openai_fusion"
        )
    )


    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND TELEGRAM IMAGE STUDIO V1.1"
    )
    print(
        "=========================================="
    )

    print(
        "✅ Natural image requests"
    )

    print(
        "✅ Telegram text generation"
    )

    print(
        "✅ Telegram voice generation"
    )

    print(
        "✅ Preview delivery"
    )

    print(
        "✅ Original-quality delivery"
    )

    print(
        "✅ Image metadata persistence"
    )

    print(
        (
            "✅ OpenAI: "
            +
            (
                "READY"
                if openai_ready
                else
                "missing"
            )
        )
    )

    print(
        (
            "✅ Nano Banana 2: "
            +
            (
                "CONFIGURED"
                if nano_fast_ready
                else
                "missing"
            )
        )
    )

    print(
        (
            "✅ Nano Banana Pro: "
            +
            (
                "CONFIGURED"
                if nano_pro_ready
                else
                "missing"
            )
        )
    )

    print(
        (
            "✅ BEST mode: "
            +
            (
                "READY"
                if best_ready
                else
                "not ready"
            )
        )
    )

    print(
        (
            "✅ OpenAI Fusion fallback: "
            +
            (
                "READY"
                if status_flag(
                    status,
                    "supports_openai_fusion"
                )
                else
                "not ready"
            )
        )
    )

    print(
        (
            "✅ Google + OpenAI Fusion: "
            +
            (
                "CONFIGURED"
                if google_openai_fusion_ready
                else
                "not configured"
            )
        )
    )

    print(
        (
            "✅ Google optional: "
            +
            str(
                bool(
                    status.get(
                        "google_optional",
                        False
                    )
                )
            )
        )
    )

    print(
        "✅ Engine status compatibility fixed"
    )

    print("")


    return {
        "ok":
            True,

        "already_installed":
            False,

        "status":
            status,

        "best_ready":
            best_ready,
    }


# =========================================================
# SELF TEST
#
# NO IMAGE GENERATION.
# NO PAID API REQUEST.
# =========================================================

if __name__ == "__main__":

    status = get_image_engine_status()


    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND TELEGRAM IMAGE STUDIO V1.1"
    )
    print(
        "=========================================="
    )
    print("")


    print(
        "Engine version:",
        ENGINE_VERSION
    )


    print(
        "OpenAI:",
        (
            "READY"
            if provider_ready(
                status,
                "openai"
            )
            else
            "missing"
        )
    )


    print(
        "Nano Banana 2:",
        (
            "CONFIGURED"
            if provider_ready(
                status,
                "google_fast"
            )
            else
            "missing"
        )
    )


    print(
        "Nano Banana Pro:",
        (
            "CONFIGURED"
            if provider_ready(
                status,
                "google_pro"
            )
            else
            "missing"
        )
    )


    best_ready = status_flag(
        status,
        "supports_best_mode",
        "supports_openai_fusion"
    )


    print(
        "BEST:",
        (
            "READY"
            if best_ready
            else
            "not ready"
        )
    )


    print(
        "OpenAI Fusion:",
        (
            "READY"
            if status_flag(
                status,
                "supports_openai_fusion"
            )
            else
            "not ready"
        )
    )


    print("")


    tests = [
        (
            "اعمللي صورة سيارة سوداء بالليل",
            True
        ),

        (
            "اعمللي بوستر منتج بأفضل نتيجة ممكنة",
            True
        ),

        (
            "صمملي إعلان عطر فاخر",
            True
        ),

        (
            "/image ساعة فخمة",
            True
        ),

        (
            "شو أفضل موديل للصور؟",
            False
        ),
    ]


    for text, expected in tests:

        actual = (
            looks_like_image_generation_request(
                text
            )
        )


        print(
            (
                "✅"
                if actual == expected
                else
                "❌"
            ),
            actual,
            "|",
            text
        )


    print("")

    print(
        "✅ No supports_best_mode KeyError"
    )

    print("")
