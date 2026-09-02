# =========================================================
# XPAND TELEGRAM IMAGE STUDIO V1.0.1
#
# Connects XPAND Smart Image Engine to Telegram.
#
# Supports:
# - Natural Arabic image requests
# - Telegram text
# - Telegram voice after transcription
# - AUTO / BEST / GPT / Nano Banana routing
# - Preview image
# - Original-quality document
# - Image metadata persistence
# - Foundation for "edit last image"
#
# Requires:
# - xpand_image_engine.py
# - requests
#
# Does NOT modify legacy main.py directly.
# Installed from main_xpand.py.
# =========================================================

from __future__ import annotations

import io
import os
import re
from typing import Any, Dict, List, Optional

import requests

from xpand_image_engine import (
    ENGINE_VERSION,
    generate_image,
    get_image_engine_status,
)


# =========================================================
# VERSION
# =========================================================

VERSION = "1.0.1"

MODULE_NAME = "XPAND Telegram Image Studio"


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
# NORMALIZATION
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
    "بنر",
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
]


IMAGE_QUESTION_MARKERS = [
    "شو يعني",
    "ما معنى",
    "اشرحلي",
    "اشرح لي",
    "كيف بتشتغل",
    "كيف تعمل",
    "شو افضل موديل",
    "شو أفضل موديل",
    "ايش افضل موديل",
    "أي موديل",
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
# EXPLICIT MODEL / MODE
# =========================================================

def detect_generation_mode(
    text: str
) -> str:

    if contains_any(
        text,
        [
            "best mode",
            "وضع best",
            "موديلين",
            "موديلين مختلفين",
            "اقوى نتيجه",
            "أقوى نتيجة",
            "اقوى شيء",
            "أقوى شيء",
            "افضل نتيجه ممكنه",
            "أفضل نتيجة ممكنة",
            "اعلى مستوى ممكن",
            "أعلى مستوى ممكن",
        ]
    ):

        return "best"

    if contains_any(
        text,
        [
            "gpt-image-2",
            "gpt image 2",
            "جي بي تي ايمج",
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
            "نانو بنانا pro",
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
    "ثلاث صور": 3,
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
        r"\b([1-4])\s*(?:صور|صوره|صورة|نسخ|خيارات)\b",
        r"\b(?:صور|نسخ|خيارات)\s*([1-4])\b",
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

        if normalized(
            marker
        ) in source:

            if contains_any(
                source,
                [
                    "صور",
                    "صوره",
                    "صورة",
                    "نسخ",
                    "خيارات",
                ]
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
# PROMPT CLEANUP
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
        timeout=TELEGRAM_TIMEOUT
    )

    data = response.json()

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
        timeout=TELEGRAM_TIMEOUT
    )

    data = response.json()

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
            "file_id": "",
            "file_unique_id": "",
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
# IMAGE DB
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
                    VALUES (
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
                            200
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
                            2000
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
# LABELS
# =========================================================

def provider_label(
    provider: str,
    model: str
) -> str:

    if provider == "openai":

        return "GPT-Image-2"

    if provider == "google_fast":

        return "Nano Banana 2"

    if provider == "google_pro":

        return "Nano Banana Pro"

    return clean_text(
        model,
        100
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
        f" | {index}/{total}"
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
        "الموديل: "
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
            30
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
                30
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

    image_db_id = save_image_record(
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

    core.send_action(
        chat_id,
        "upload_photo"
    )

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
        mode=mode,
        number=number,
        allow_fallback=True,
    )

    if (
        not result.ok
        or
        not result.images
    ):

        raise RuntimeError(
            "ما رجعت صورة من محرك التوليد."
        )

    delivered = []

    total = len(
        result.images
    )

    for index, image in enumerate(
        result.images,
        start=1
    ):

        core.send_action(
            chat_id,
            "upload_photo"
        )

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

    models = []

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
        " | الموديل: "
        +
        ", ".join(
            models
        )
    )

    core.save_message(
        chat_id,
        "assistant",
        summary
    )

    core.record_event(
        user_id,
        chat_id,
        "image_generated",
        summary,
        {
            "mode":
                mode,

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
                    for item
                    in delivered
                    if item.get(
                        "image_id"
                    )
                    is not None
                ],
        }
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
            " | models="
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
                    "⚠️ Image fallback info: "
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

        core.send_message(
            chat_id,
            (
                "صار خلل بتوليد الصورة.\n"
                "ما عملت حالي إنها نجحت.\n\n"
                "الخطأ: "
                +
                clean_text(
                    error,
                    1200
                )
            )
        )

    return True


# =========================================================
# INSTALL HOOKS
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

    # -----------------------------------------------------
    # TEXT
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # VOICE
    # -----------------------------------------------------

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

                models = result.get(
                    "models",
                    []
                )

                if models:

                    return (
                        "تم. ولّدتلك الصورة "
                        "وبعثتلك المعاينة والنسخة الأصلية."
                    )

                return (
                    "تم، ولّدتلك الصورة وبعثتلك إياها."
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

    status = get_image_engine_status()

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND TELEGRAM IMAGE STUDIO V1.0.1"
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
                if status[
                    "providers"
                ][
                    "openai"
                ][
                    "configured"
                ]
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
                "READY"
                if status[
                    "providers"
                ][
                    "google_fast"
                ][
                    "configured"
                ]
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
                "READY"
                if status[
                    "providers"
                ][
                    "google_pro"
                ][
                    "configured"
                ]
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
                if status[
                    "supports_best_mode"
                ]
                else
                "not ready"
            )
        )
    )
    print("")

    return {
        "ok":
            True,

        "already_installed":
            False,

        "status":
            status,
    }


# =========================================================
# SELF TEST
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND TELEGRAM IMAGE STUDIO V1.0.1"
    )
    print(
        "=========================================="
    )
    print("")

    status = get_image_engine_status()

    print(
        "Image engine:",
        (
            "READY"
            if status.get(
                "ok"
            )
            else
            "NOT READY"
        )
    )

    print(
        "OpenAI:",
        (
            "READY"
            if status[
                "providers"
            ][
                "openai"
            ][
                "configured"
            ]
            else
            "missing"
        )
    )

    print(
        "Nano Banana 2:",
        (
            "READY"
            if status[
                "providers"
            ][
                "google_fast"
            ][
                "configured"
            ]
            else
            "missing"
        )
    )

    print(
        "Nano Banana Pro:",
        (
            "READY"
            if status[
                "providers"
            ][
                "google_pro"
            ][
                "configured"
            ]
            else
            "missing"
        )
    )

    print(
        "BEST mode:",
        (
            "READY"
            if status.get(
                "supports_best_mode"
            )
            else
            "not ready"
        )
    )

    print("")

    tests = [
        (
            "اعمللي صورة إعلان عطر فاخر 4K",
            True
        ),
        (
            "صمملي بوستر احترافي لشركة XPAND",
            True
        ),
        (
            "ولدلي صورة سيارة سوداء بالليل",
            True
        ),
        (
            "/image قهوة عربية على طاولة خشب",
            True
        ),
        (
            "اشرحلي شو افضل موديل للصور",
            False
        ),
        (
            "شو رأيك بهاي الصورة؟",
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
