# =========================================================
# XPAND GPT-IMAGE-2 REAL TEST V1.0
#
# PURPOSE:
# - Generate exactly ONE paid image
# - Use GPT-Image-2 only
# - Disable Gemini fallback
# - Send preview + original file to Ihab on Telegram
#
# Run:
# python test_xpand_image_openai.py
# =========================================================

from __future__ import annotations

import io
import os
import sys
import time

import requests

from xpand_image_engine import (
    generate_image,
)


# =========================================================
# ENV
# =========================================================

TELEGRAM_BOT_TOKEN = str(
    os.environ.get(
        "TELEGRAM_BOT_TOKEN",
        ""
    )
).strip()


TELEGRAM_ALLOWED_USER_ID = str(
    os.environ.get(
        "TELEGRAM_ALLOWED_USER_ID",
        ""
    )
).strip()


# =========================================================
# TEST PROMPT
# =========================================================

TEST_PROMPT = """
اعمل صورة إعلان احترافية جداً لعطر فاخر.

المنتج:
زجاجة عطر سوداء فخمة بتصميم minimal وأنيق.

المشهد:
خلفية سوداء داكنة جداً،
سطح أسود لامع مع انعكاس خفيف للزجاجة،
ضوء ذهبي سينمائي من الخلف والجوانب،
ضباب خفيف جداً في الجو،
ظلال دقيقة وعميقة.

الستايل:
إعلان عالمي فاخر لبراند عطور premium،
تصوير منتجات تجاري واقعي جداً،
تفاصيل نظيفة،
مواد واقعية،
إضاءة استوديو عالية المستوى،
لون أسود وذهبي،
تكوين بصري قوي.

مهم:
بدون أي كتابة.
بدون شعارات.
بدون watermark.
بدون عناصر إضافية مشتتة.

الصورة لازم تبدو كأنها حملة إعلانية احترافية
تم تصويرها في استوديو عالمي.
""".strip()


# =========================================================
# TELEGRAM
# =========================================================

def telegram_api_url(
    method: str
) -> str:

    return (
        "https://api.telegram.org/bot"
        +
        TELEGRAM_BOT_TOKEN
        +
        "/"
        +
        method
    )


def send_telegram_message(
    text: str
) -> None:

    response = requests.post(
        telegram_api_url(
            "sendMessage"
        ),
        json={
            "chat_id":
                TELEGRAM_ALLOWED_USER_ID,

            "text":
                text,
        },
        timeout=60
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
                "Telegram sendMessage failed: "
                +
                str(
                    data
                )
            )
        )


def send_preview(
    image_bytes: bytes,
    filename: str,
    caption: str
) -> None:

    buffer = io.BytesIO(
        image_bytes
    )

    buffer.name = filename


    response = requests.post(
        telegram_api_url(
            "sendPhoto"
        ),
        data={
            "chat_id":
                TELEGRAM_ALLOWED_USER_ID,

            "caption":
                caption,
        },
        files={
            "photo": (
                filename,
                buffer,
                "image/png"
            )
        },
        timeout=120
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
                str(
                    data
                )
            )
        )


def send_original(
    image_bytes: bytes,
    filename: str,
    mime_type: str,
    caption: str
) -> None:

    buffer = io.BytesIO(
        image_bytes
    )

    buffer.name = filename


    response = requests.post(
        telegram_api_url(
            "sendDocument"
        ),
        data={
            "chat_id":
                TELEGRAM_ALLOWED_USER_ID,

            "caption":
                caption,
        },
        files={
            "document": (
                filename,
                buffer,
                mime_type
            )
        },
        timeout=180
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
                str(
                    data
                )
            )
        )


# =========================================================
# VALIDATION
# =========================================================

def validate_environment() -> None:

    missing = []


    if not TELEGRAM_BOT_TOKEN:

        missing.append(
            "TELEGRAM_BOT_TOKEN"
        )


    if not TELEGRAM_ALLOWED_USER_ID:

        missing.append(
            "TELEGRAM_ALLOWED_USER_ID"
        )


    if not str(
        os.environ.get(
            "OPENAI_API_KEY",
            ""
        )
    ).strip():

        missing.append(
            "OPENAI_API_KEY"
        )


    if missing:

        raise RuntimeError(
            (
                "Missing environment variables: "
                +
                ", ".join(
                    missing
                )
            )
        )


# =========================================================
# MAIN
# =========================================================

def main() -> int:

    validate_environment()


    print("")
    print(
        "========================================"
    )
    print(
        " XPAND GPT-IMAGE-2 REAL TEST V1.0"
    )
    print(
        " EXACTLY ONE IMAGE GENERATION REQUEST"
    )
    print(
        "========================================"
    )
    print("")


    print(
        "🎨 Model: gpt-image-2"
    )


    print(
        "🎯 Provider: OpenAI only"
    )


    print(
        "🖼️ Images requested: 1"
    )


    print(
        "💎 Quality: high"
    )


    print(
        "🚫 Gemini fallback: disabled"
    )


    print("")
    print(
        "⏳ Generating image..."
    )


    started = time.monotonic()


    try:

        result = generate_image(
            TEST_PROMPT,

            mode="openai",

            aspect_ratio="1:1",

            image_size="1K",

            quality="high",

            number=1,

            reference_count=0,

            allow_fallback=False,
        )


    except Exception as error:

        print("")
        print(
            "❌ GENERATION FAILED"
        )
        print(
            str(
                error
            )
        )
        print("")

        return 1


    if (
        not result.ok
        or
        not result.images
    ):

        print(
            "❌ No image returned."
        )

        return 1


    image = result.images[0]


    elapsed = round(
        time.monotonic()
        -
        started,
        2
    )


    print("")
    print(
        "✅ IMAGE GENERATED"
    )


    print(
        (
            "✅ Provider: "
            +
            image.provider
        )
    )


    print(
        (
            "✅ Model: "
            +
            image.model
        )
    )


    print(
        (
            "✅ Bytes: "
            +
            str(
                len(
                    image.image_bytes
                )
            )
        )
    )


    print(
        (
            "✅ Mime: "
            +
            image.mime_type
        )
    )


    print(
        (
            "✅ Time: "
            +
            str(
                elapsed
            )
            +
            " sec"
        )
    )


    print("")
    print(
        "📤 Sending preview to Telegram..."
    )


    preview_caption = (
        "🎨 XPAND Image Test\n\n"
        "الموديل: GPT-Image-2\n"
        "الجودة: High\n"
        "الوضع: OpenAI فقط"
    )


    try:

        send_preview(
            image.image_bytes,
            image.filename,
            preview_caption
        )


        print(
            "✅ Preview sent"
        )


    except Exception as error:

        #
        # Preview failure should NOT trigger another image.
        #
        print(
            (
                "⚠️ Preview failed: "
                +
                str(
                    error
                )
            )
        )


    print("")
    print(
        "📦 Sending original file..."
    )


    try:

        send_original(
            image.image_bytes,
            image.filename,
            image.mime_type,
            (
                "📦 XPAND Original Image\n"
                "النسخة الأصلية بدون إعادة توليد."
            )
        )


        print(
            "✅ Original sent"
        )


    except Exception as error:

        print("")
        print(
            "❌ Original Telegram upload failed"
        )
        print(
            str(
                error
            )
        )

        return 1


    print("")
    print(
        "========================================"
    )
    print(
        " XPAND IMAGE TEST PASSED ✅"
    )
    print(
        "========================================"
    )
    print("")

    return 0


# =========================================================
# ENTRYPOINT
# =========================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
