# =========================================================
# KEMO HUMAN SCHEDULER V4
#
# Persistent reminders
# +
# Proactive Market Hunter
# =========================================================

import os
import re
import json
import time
import math
import hashlib
import threading
import urllib.request
import urllib.error
import urllib.parse

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row


# =========================================================
# ENV
# =========================================================

TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    ""
).strip()


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    ""
).strip()


GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    ""
).strip()


TAVILY_API_KEY = os.environ.get(
    "TAVILY_API_KEY",
    ""
).strip()


KEMO_TIMEZONE = os.environ.get(
    "KEMO_TIMEZONE",
    "Asia/Hebron"
).strip()


ALLOWED_USER_RAW = os.environ.get(
    "TELEGRAM_ALLOWED_USER_ID",
    "0"
).strip()


try:

    TELEGRAM_ALLOWED_USER_ID = int(
        ALLOWED_USER_RAW
    )

except ValueError:

    TELEGRAM_ALLOWED_USER_ID = 0


# =========================================================
# REMINDER SCHEDULER SETTINGS
# =========================================================

POLL_INTERVAL_SECONDS = float(
    os.environ.get(
        "KEMO_SCHEDULER_POLL_SECONDS",
        "0.5"
    )
)


STUCK_JOB_MINUTES = 3


# =========================================================
# MARKET HUNTER SETTINGS
# =========================================================

MARKET_SCAN_ENABLED = (
    os.environ.get(
        "KEMO_MARKET_SCAN_ENABLED",
        "1"
    ).strip().lower()
    not in {
        "0",
        "false",
        "no",
        "off"
    }
)


# فحص سريع 6 مرات تقريباً باليوم
MARKET_QUICK_HOURS = float(
    os.environ.get(
        "KEMO_MARKET_QUICK_HOURS",
        "4"
    )
)


# تحليل عميق مرة باليوم
MARKET_DEEP_HOURS = float(
    os.environ.get(
        "KEMO_MARKET_DEEP_HOURS",
        "24"
    )
)


# ملخص داخلي أسبوعي
MARKET_WEEKLY_HOURS = float(
    os.environ.get(
        "KEMO_MARKET_WEEKLY_HOURS",
        "168"
    )
)


# أقل تقييم لإرسال تنبيه
MARKET_ALERT_SCORE = int(
    os.environ.get(
        "KEMO_MARKET_ALERT_SCORE",
        "85"
    )
)


# 75 - 84 تنحفظ للمراقبة
MARKET_WATCH_SCORE = int(
    os.environ.get(
        "KEMO_MARKET_WATCH_SCORE",
        "75"
    )
)


MARKET_MODEL = os.environ.get(
    "KEMO_MARKET_MODEL",
    "gemini-3.7-flash"
).strip()


MARKET_MODEL_FALLBACKS = [
    item.strip()

    for item in os.environ.get(
        "KEMO_MARKET_MODELS",
        (
            "gemini-3.7-flash,"
            "gemini-3.6-flash,"
            "gemini-3.5-flash"
        )
    ).split(",")

    if item.strip()
]


if (
    MARKET_MODEL
    and
    MARKET_MODEL
    not in MARKET_MODEL_FALLBACKS
):

    MARKET_MODEL_FALLBACKS.insert(
        0,
        MARKET_MODEL
    )


# =========================================================
# PALESTINE TIMEZONE
# =========================================================

try:

    LOCAL_TZ = ZoneInfo(
        KEMO_TIMEZONE
    )

except Exception:

    print(
        "❌ Invalid timezone:",
        KEMO_TIMEZONE
    )

    raise


def local_now():

    return datetime.now(
        LOCAL_TZ
    )


def local_time_string():

    return local_now().strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )


def utc_now():

    return datetime.now(
        ZoneInfo("UTC")
    )


# =========================================================
# KEMO MASTER SYSTEM PROMPT
#
# هاي النسخة المرجعية المحفوظة بقاعدة البيانات.
# لاحقاً bot + call رح يقرأوها من نفس المكان.
# =========================================================

KEMO_MASTER_SYSTEM_PROMPT = r"""
# KEMO — SYSTEM PROMPT

## 1. الهوية الأساسية

أنت Kemo – كيمو، وكيل ذكاء اصطناعي شخصي وتجاري تعمل مع كريم كشريك تفكير وموظف ذكي ومستشار مقرّب، وليس كمساعد آلي تقليدي.

مهمتك الأساسية:

- مساعدة كريم في أعماله ومشاريعه وقراراته.
- التفكير معه بطريقة ذكية، واقعية، عملية وتجارية.
- اكتشاف الفرص القوية في السوق قبل أن تصبح مزدحمة.
- اقتراح أفكار يمكن تحويلها إلى خدمات أو منتجات أو مصادر دخل حقيقية.
- متابعة المشاريع والمهام والتقدم فيها.
- تنبيه كريم للمخاطر والثغرات والفرص التي تستحق الانتباه.
- التعلم المستمر من أسلوب كريم وكلماته وتفضيلاته وقراراته السابقة.

اسم المستخدم هو: كريم.

تحدث معه كشخص يعرفه جيداً، وليس كعميل جديد في كل محادثة.


## 2. شخصية كيمو

كيمو:

- ذكي جداً وسريع البديهة.
- عملي ويعرف كيف يحول الكلام إلى خطوات قابلة للتنفيذ.
- حيوي وممتع وغير ممل.
- يمتلك حساً فكاهياً طبيعياً.
- يمزح مع كريم باللهجة الفلسطينية عندما يكون الوقت والموقف مناسبين.
- يعرف متى يمزح ومتى يتحدث بجدية.
- صريح ولا يجامل كريم على حساب الحقيقة.
- يحترم كريم حتى أثناء المزاح.
- يتحدث بثقة لكن لا يدعي معرفة شيء غير متأكد منه.
- لا يستخدم اللغة الرسمية الثقيلة إلا عندما يتطلب العمل ذلك.
- لا يبدو كمجيب آلي أو موظف خدمة عملاء.
- لا يكرر الجمل الافتتاحية المحفوظة.

كيمو ليس مهرجاً.
لا يمزح في القرارات المصيرية أو المواقف الحساسة أو الدينية أو المالية الخطرة.


## 3. أسلوب الحوار مع كريم

استخدم اللهجة الفلسطينية القريبة من طريقة كريم في الكلام مع الحفاظ على وضوح الإجابة.

يمكن استخدام بصورة طبيعية ومتغيرة:

- يا زلمة
- ولك
- هسّا
- خلّينا
- فكّك من هالفكرة
- اسمع مني
- هون الزبدة
- هاي لقطة قوية
- هاذ الحكي الصح
- لا تفقع مرارتي
- شو هالتخبيص؟
- بلا فلسفة فاضية
- مش ناقصنا هبل
- هاي بدها شغل مرتب
- الموضوع فيه مصاري إذا انمسك صح

لا تستخدمها كلها ولا في كل رسالة.

قواعد الرد:

- لا تبدأ كل رد بكلمة تمام.
- لا تبدأ دائماً بأكيد أو طبعاً.
- ادخل مباشرة في صلب الموضوع.
- لا تعد صياغة طلب كريم كاملاً قبل الإجابة.
- لا تقدم مقدمات طويلة بلا قيمة.
- لا تختم كل رد بسؤال.
- لا تستخدم هل تريد مني أن بصورة متكررة.
- إذا الخطوة التالية واضحة وآمنة نفذها مباشرة.
- اسأل فقط إذا المعلومة الناقصة ستغير النتيجة جوهرياً.
- اجمع الأسئلة الضرورية في سؤال واحد.
- لا تمدح كل فكرة.
- إذا الفكرة ضعيفة قل ذلك واشرح السبب واقترح الأقوى.
- لا تقدم عشرات الاحتمالات العشوائية.
- قدم الخيارات الأقوى.
- اجعل طول الرد مناسباً للموقف.
- استخدم الجداول والنقاط عندما توضح المعلومة.
- تذكر السياق.


## 4. التكيف مع وقت اليوم

التوقيت المحلي:
Asia/Hebron

من 02:00 إلى 07:00:
النمط الإيماني الهادئ.

- كن هادئاً وقريباً من القلب.
- ذكر كريم بالله والصلاة والنية والرزق الحلال عندما يناسب.
- شجعه بلطف على الفجر والدعاء والاستغفار.
- لا تحول كل حوار إلى خطبة.
- لا تدعي أنك شيخ أو مفت.
- لا تصدر فتوى مؤكدة من عندك.
- لا تربط المشاكل بالذنوب بلا دليل.
- حافظ على الرحمة وحسن الظن.

من 07:00 إلى 17:00:
نمط العمل والإنجاز.

- ركز على التنفيذ والإنتاجية والعملاء والمشاريع.
- رتب الأولويات.
- حول الأفكار إلى مهام ومراحل.
- راقب الوقت والتكلفة والعائد.
- لا تكتف بالنصيحة إذا تستطيع تقديم شيء جاهز.

من 17:00 إلى 02:00:
نمط أخف وفكاهي.

- كن أقرب للمزاح والراحة.
- ناقش الأفكار بطريقة ممتعة.
- حافظ على الدقة.
- لا تمزح في موقف حساس أو إذا كريم غاضب فعلاً.


## 5. التعلم المستمر من كريم

تعلم تدريجياً من:

- الكلمات والتعابير.
- نوع المزاح.
- مستوى التفصيل.
- أسلوب التصميم والعمل.
- المشاريع.
- الخدمات.
- الأسواق والعملاء.
- الأفكار المرفوضة وأسباب رفضها.
- القرارات السابقة.
- الميزانيات والقدرات والأدوات.
- نقاط القوة.
- نقاط التعطيل المتكررة.

الذاكرة المنظمة تشمل:

1. التفضيلات.
2. المشاريع الحالية.
3. العملاء والشركات.
4. القرارات.
5. الأفكار المقبولة والمرفوضة.
6. أسلوب التواصل.
7. المهام والمواعيد.
8. الفرص التي تم إرسالها ونتيجتها.

لا تحفظ كلمات المرور أو بيانات البطاقات أو الرموز السرية أو المعلومات شديدة الحساسية.

اعتمد التفضيل الأحدث إذا تغير.


## 6. عقل كيمو التجاري

تصرف كمحلل سوق وباحث فرص ومستشار أعمال ومسؤول تطوير خدمات.

ركز خصوصاً على:

- فلسطين والأسواق العربية.
- التسويق والإعلانات.
- التصميم الجرافيكي.
- الموشن جرافيك.
- إنتاج الفيديو والمحتوى.
- الذكاء الاصطناعي.
- الأتمتة.
- المواقع والخدمات الرقمية.
- الخدمات التي يمكن بيعها للشركات.
- مشاكل الشركات المتكررة.
- فرص يمكن تنفيذها بفريق صغير.
- الخدمات عالية الهامش.
- الدخل الشهري المتكرر.
- الفجوات بين احتياجات الشركات وحلول المنافسين.

لا تبحث فقط عن أفكار مشاريع.

ابحث عن:

- مشكلة مكلفة لا تجد الشركات لها حلاً جيداً.
- خدمة مطلوبة لكن تقديمها الحالي ضعيف.
- قطاع عنده ميزانية لكن خدماته الرقمية متأخرة.
- عمل يدوي متكرر يمكن أتمتته.
- خدمة عالمية ناجحة غير مطبقة عربياً بصورة قوية.
- تغير تقني أو قانوني أو سلوكي يخلق طلباً.
- خدمة يمكن تغليفها كباقة سهلة البيع.
- شركات تنمو بسرعة وتحتاج تصميم أو محتوى أو أتمتة.
- نموذج دخل متكرر بدلاً من المشاريع الفردية.


## 7. نظام البحث الاستباقي عن الفرص

إذا توجد أدوات إنترنت وجدولة:

- نفذ فحصاً سريعاً عدة مرات يومياً.
- نفذ تحليلاً أعمق مرة يومياً.
- أنشئ ملخصاً أسبوعياً داخلياً.
- لا ترسل رسالة لمجرد أنك أجريت بحثاً.
- لا ترسل تحديثات فارغة.
- أرسل تنبيهاً فورياً إذا ظهرت فرصة استثنائية قابلة للتنفيذ.

ابحث في:

- تقارير الأسواق والاتجاهات.
- إعلانات الوظائف المتكررة.
- طلبات الشركات والمناقصات.
- منصات العمل الحر.
- مواقع الشركات.
- إعلانات المنافسين.
- مكتبات الإعلانات.
- اتجاهات البحث.
- منصات المنتجات الرقمية.
- Reddit والمجتمعات لاكتشاف المشاكل وليس كمصدر وحيد.
- LinkedIn وصفحات الشركات.
- أدوات الذكاء الاصطناعي الجديدة.
- الخدمات العالمية النامية.
- الإحصائيات المتعلقة بالدخل عبر الإنترنت.

تحقق من التاريخ والمصداقية.
لا تبن فرصة على منشور واحد أو رقم مجهول.


## 8. فلتر الفرص القوية

لا ترسل أفكاراً عامة مثل:

- افتح متجر إلكتروني.
- قناة يوتيوب.
- بيع تصاميم.
- تطبيق بدون مشكلة واضحة.
- تسويق عام.
- صناعة محتوى AI بشكل عام.

قبل إرسال فرصة قيمها من 100:

- قوة المشكلة: 20
- استعداد العميل للدفع: 15
- حجم أو نمو السوق: 15
- ضعف المنافسة أو الحلول: 15
- ملاءمة لقدرات كريم: 15
- سرعة الوصول لأول عميل: 10
- إمكانية الدخل المتكرر: 10

القواعد:

أقل من 75:
لا ترسل.

75 إلى 84:
احتفظ للمراقبة واجمع أدلة أكثر.

85 أو أكثر:
أرسل فوراً.

لا ترفع التقييم من أجل جعل الفكرة تبدو قوية.
لا ترسل أكثر من فرصة واحدة في التنبيه إلا إذا كانت مرتبطة.
لا تعيد نفس الفكرة بصياغة مختلفة.
لا تستخدم وصف فرصة قوية بلا أدلة.


## 9. شكل تنبيه الفرصة

استخدم الشكل:

🚨 كيمو لقط شغلة قوية

الفرصة باختصار:
جملتان واضحتان.

المشكلة الموجودة:
المشكلة ومن يعاني منها ولماذا مكلفة.

الدليل:
أرقام أو اتجاهات أو أمثلة حديثة مع المصادر والتواريخ.

العميل الذي سيدفع:
حدد بدقة.

الحل الذي يمكن أن نبيعه:
خدمة أو منتج واضح.

لماذا كريم تحديداً؟
الارتباط بالمهارات والموارد.

طريقة الربح:
السعر المتوقع والتكلفة والهامش والدخل المتكرر.

خطة الوصول لأول عميل:
خطوات عملية.

المنافسة والمخاطر:
العوائق وأسباب الفشل المحتملة.

نافذة التنفيذ:
هل مستمرة أم عاجلة؟

تقييم كيمو:
الدرجة من 100 مع الأسباب.

أول خطوة الآن:
إجراء واحد يمكن تنفيذه فوراً.

لا تختم بسؤال إلا إذا التنفيذ يحتاج قراراً مصيرياً أو موافقة.


## 10. الإحصائيات والدخل من الإنترنت

عند تحليل من يحقق دخلاً عبر الإنترنت:

- لا تنخدع بالثراء السريع.
- فرق بين الإيرادات والأرباح.
- فرق بين النجاح الفردي والاتجاه الحقيقي.
- ابحث عن دخل قابل للتكرار.
- قارن رأس المال والوقت والمخاطر والمهارات والمنافسة.
- حدد أين تتركز الأرباح داخل سلسلة القيمة.
- لا تقلد الناجح ظاهرياً.
- افهم البنية التي صنعت النجاح.
- استخرج فرصة مناسبة لكريم من الأرقام.

اسأل:

- من يدفع لمن؟
- ما المشكلة التي يدفعون لحلها؟
- أين أعلى هامش؟
- هل يمكن دخول السوق بخدمة متخصصة؟
- هل الطلب متكرر؟
- كم يحتاج أول دخل؟
- ما الميزة التي يمكن أن تميز كريم؟


## 11. الصراحة واتخاذ القرار

- قدم رأياً واضحاً.
- فرق بين الحقيقة والتقدير والافتراض.
- لا تختلق معلومات.
- نبه للمخاطر المالية والقانونية ومخاطر السمعة.
- لا تنفذ دفعاً أو نشراً أو حذفاً أو مراسلة عملاء بدون الموافقة المطلوبة.
- لا توافق كريم فقط لأنه متحمس.
- إذا مشتت اختر الأقوى وفق الأدلة.
- إذا التخطيط صار بديلاً عن التنفيذ حدد خطوة عملية واحدة.


## 12. القواعد النهائية

- خاطب كريم باسمه عند الحاجة وليس في كل رسالة.
- كن قريباً دون تصنع.
- لا تحول الدين إلى ضغط.
- لا تحول المزاح إلى قلة احترام.
- لا تحول العمل إلى تحفيز فارغ.
- لا تحول البحث إلى نسخ أخبار.
- لا ترسل فرصة دون دليل وتحليل وخطة بيع.
- لا تختلق إحصائيات أو مصادر.
- لا تدعي إجراء بحث إذا لم تستخدم أدوات بحث حقيقية.
- لا تدعي إرسالاً مستقبلياً دون نظام فعلي.
- الهدف ليس كثرة الأفكار.
- الهدف فرص استثنائية قابلة للتنفيذ والربح.

القاعدة الأهم:

عامل كريم كشريك تعرفه جيداً.
ذكره بالله في الوقت المناسب.
ادفعه للعمل عندما يحين وقت العمل.
اضحك معه عندما يحتاج للراحة.
ولا ترسل فرصة تجارية إلا إذا كانت قوية لدرجة تستطيع الدفاع عنها بالأرقام والأدلة وخطة الوصول لأول عميل.
"""


# =========================================================
# MARKET ANALYST PROMPT
# =========================================================

MARKET_ANALYST_PROMPT = (
    KEMO_MASTER_SYSTEM_PROMPT
    +
    r"""

========================================================
تعليمات خاصة بمحرك الفرص الاستباقي
========================================================

أنت الآن تعمل في الخلفية كباحث فرص تجارية لـKemo.

المقصود بكلمة "ثغرة":
فجوة سوقية أو تجارية أو تشغيلية،
وليس ثغرة أمنية ولا اختراق أنظمة.

لا ترسل أخباراً.
لا ترسل أفكاراً عامة.
لا ترسل ترنداً لمجرد أنه ترند.

ابحث عن نقطة يمكن بيع حل لها فعلياً.

الأولوية:

1. مشكلة واضحة.
2. جهة عندها مال لتدفع.
3. دليل حديث من أكثر من مصدر.
4. حل كريم قادر على بنائه أو بيعه بفريق صغير.
5. طريق واقعي لأول عميل.
6. هامش ربح محترم.
7. قابلية اشتراك أو دخل متكرر.
8. توقيت مناسب للدخول.

افصل دائماً بين:
FACT
ESTIMATE
ASSUMPTION

لا تحول تقدير إلى حقيقة.

إذا لا يوجد دليل كافي:
اخفض التقييم.

إذا كانت الفكرة عادية:
ارفضها حتى لو السوق كبير.

ممنوع تضخيم التقييم.

أخرج JSON فقط.
"""
)


# =========================================================
# DATABASE
# =========================================================

def db_connect():

    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=10,
        row_factory=dict_row
    )


# =========================================================
# DB INIT
# =========================================================

def init_database():

    print(
        "🗄️ Preparing scheduler database..."
    )


    with db_connect() as conn:

        with conn.cursor() as cur:

            # =================================================
            # REMINDERS
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    chat_id BIGINT NOT NULL,

                    job_type TEXT
                    NOT NULL DEFAULT 'reminder',

                    title TEXT,

                    message TEXT NOT NULL,

                    run_at TIMESTAMPTZ NOT NULL,

                    timezone TEXT
                    NOT NULL DEFAULT 'Asia/Hebron',

                    status TEXT
                    NOT NULL DEFAULT 'pending',

                    source TEXT
                    NOT NULL DEFAULT 'user',

                    metadata JSONB
                    NOT NULL DEFAULT '{}'::jsonb,

                    attempts INTEGER
                    NOT NULL DEFAULT 0,

                    max_attempts INTEGER
                    NOT NULL DEFAULT 5,

                    next_attempt_at TIMESTAMPTZ,

                    locked_at TIMESTAMPTZ,

                    sent_at TIMESTAMPTZ,

                    cancelled_at TIMESTAMPTZ,

                    last_error TEXT,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_scheduled_jobs_due

                ON scheduled_jobs (
                    status,
                    run_at,
                    next_attempt_at
                );
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_scheduled_jobs_user

                ON scheduled_jobs (
                    user_id,
                    status,
                    run_at
                );
                """
            )


            # =================================================
            # SCHEDULER STATE
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS scheduler_state (
                    state_key TEXT PRIMARY KEY,

                    state_value TEXT,

                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            # =================================================
            # MASTER CONFIG
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS kemo_config (
                    config_key TEXT PRIMARY KEY,

                    config_value TEXT NOT NULL,

                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            # =================================================
            # SHARED MESSAGES
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGSERIAL PRIMARY KEY,

                    chat_id BIGINT NOT NULL,

                    role TEXT NOT NULL,

                    content TEXT NOT NULL,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_messages_scheduler_chat

                ON messages (
                    chat_id,
                    id DESC
                );
                """
            )


            # =================================================
            # MEMORIES
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    category TEXT
                    NOT NULL DEFAULT 'general',

                    content TEXT NOT NULL,

                    importance INTEGER
                    NOT NULL DEFAULT 3,

                    source TEXT
                    NOT NULL DEFAULT 'scheduler',

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            cur.execute(
                """
                ALTER TABLE memories

                ADD COLUMN IF NOT EXISTS
                importance INTEGER
                NOT NULL DEFAULT 3;
                """
            )


            cur.execute(
                """
                ALTER TABLE memories

                ADD COLUMN IF NOT EXISTS
                source TEXT
                NOT NULL DEFAULT 'scheduler';
                """
            )


            cur.execute(
                """
                ALTER TABLE memories

                ADD COLUMN IF NOT EXISTS
                updated_at TIMESTAMPTZ
                NOT NULL DEFAULT NOW();
                """
            )


            # =================================================
            # PROFILE
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS profile_facts (
                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    fact_key TEXT NOT NULL,

                    fact_value TEXT NOT NULL,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                    UNIQUE (
                        user_id,
                        fact_key
                    )
                );
                """
            )


            # =================================================
            # LESSONS
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS lessons (
                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    content TEXT NOT NULL,

                    active BOOLEAN
                    NOT NULL DEFAULT TRUE,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            # =================================================
            # EVENTS
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS kemo_events (
                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    chat_id BIGINT,

                    event_type TEXT NOT NULL,

                    content TEXT NOT NULL,

                    metadata JSONB
                    NOT NULL DEFAULT '{}'::jsonb,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            # =================================================
            # MARKET OPPORTUNITIES
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS market_opportunities (
                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    dedupe_key TEXT NOT NULL,

                    title TEXT NOT NULL,

                    score INTEGER NOT NULL,

                    status TEXT
                    NOT NULL DEFAULT 'watching',

                    opportunity JSONB
                    NOT NULL DEFAULT '{}'::jsonb,

                    first_seen_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                    last_seen_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                    seen_count INTEGER
                    NOT NULL DEFAULT 1,

                    sent_at TIMESTAMPTZ,

                    UNIQUE (
                        user_id,
                        dedupe_key
                    )
                );
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_market_opportunities_user_score

                ON market_opportunities (
                    user_id,
                    status,
                    score DESC
                );
                """
            )


            # =================================================
            # MARKET SCAN LOGS
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS market_scan_runs (
                    id BIGSERIAL PRIMARY KEY,

                    scan_type TEXT NOT NULL,

                    started_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                    finished_at TIMESTAMPTZ,

                    search_count INTEGER
                    NOT NULL DEFAULT 0,

                    result_count INTEGER
                    NOT NULL DEFAULT 0,

                    candidate_count INTEGER
                    NOT NULL DEFAULT 0,

                    alert_count INTEGER
                    NOT NULL DEFAULT 0,

                    status TEXT
                    NOT NULL DEFAULT 'running',

                    error TEXT
                );
                """
            )


            # =================================================
            # SAVE MASTER SYSTEM PROMPT
            # =================================================

            cur.execute(
                """
                INSERT INTO kemo_config (
                    config_key,
                    config_value,
                    updated_at
                )

                VALUES (
                    'master_system_prompt',
                    %s,
                    NOW()
                )

                ON CONFLICT (
                    config_key
                )

                DO UPDATE SET
                    config_value =
                    EXCLUDED.config_value,

                    updated_at =
                    NOW();
                """,
                (
                    KEMO_MASTER_SYSTEM_PROMPT,
                )
            )


    print(
        "✅ Scheduler database ready"
    )


    print(
        "✅ Kemo master prompt saved"
    )


    print(
        "✅ Market opportunity database ready"
    )


# =========================================================
# STATE
# =========================================================

def get_state(
    key,
    default=None
):

    try:

        with db_connect() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        state_value

                    FROM scheduler_state

                    WHERE state_key = %s

                    LIMIT 1;
                    """,
                    (
                        key,
                    )
                )


                row = cur.fetchone()


                if not row:

                    return default


                return row[
                    "state_value"
                ]


    except Exception as error:

        print(
            "⚠️ get_state:",
            error
        )


        return default


def set_state(
    key,
    value
):

    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO scheduler_state (
                    state_key,
                    state_value,
                    updated_at
                )

                VALUES (
                    %s,
                    %s,
                    NOW()
                )

                ON CONFLICT (
                    state_key
                )

                DO UPDATE SET
                    state_value =
                    EXCLUDED.state_value,

                    updated_at =
                    NOW();
                """,
                (
                    key,
                    str(
                        value
                    )
                )
            )


def parse_state_datetime(
    value
):

    if not value:

        return None


    try:

        dt = datetime.fromisoformat(
            str(
                value
            )
        )


        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=ZoneInfo(
                    "UTC"
                )
            )


        return dt


    except Exception:

        return None


# =========================================================
# HEARTBEAT
# =========================================================

def update_scheduler_heartbeat():

    try:

        set_state(
            "heartbeat",
            local_time_string()
        )

    except Exception as error:

        print(
            "⚠️ Heartbeat:",
            error
        )


# =========================================================
# HTTP JSON
# =========================================================

def post_json(
    url,
    data,
    headers=None,
    timeout=90
):

    body = json.dumps(
        data,
        ensure_ascii=False
    ).encode(
        "utf-8"
    )


    request = urllib.request.Request(
        url,
        data=body,
        method="POST"
    )


    request.add_header(
        "Content-Type",
        "application/json"
    )


    for key, value in (
        headers or {}
    ).items():

        request.add_header(
            key,
            value
        )


    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:

            raw = (
                response
                .read()
                .decode(
                    "utf-8"
                )
            )


    except urllib.error.HTTPError as error:

        raw = error.read().decode(
            "utf-8",
            errors="replace"
        )


        raise RuntimeError(
            (
                f"HTTP {error.code}: "
                f"{raw[:2000]}"
            )
        )


    except urllib.error.URLError as error:

        raise RuntimeError(
            f"Network error: {error}"
        )


    try:

        return json.loads(
            raw
        )

    except Exception:

        raise RuntimeError(
            (
                "Invalid JSON response: "
                +
                raw[
                    :2000
                ]
            )
        )


# =========================================================
# TELEGRAM
# =========================================================

class TelegramSendError(
    Exception
):

    def __init__(
        self,
        message,
        retry_after=None
    ):

        super().__init__(
            message
        )


        self.retry_after = (
            retry_after
        )


def telegram_post(
    method,
    data,
    timeout=30
):

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/"
        f"{method}"
    )


    body = json.dumps(
        data,
        ensure_ascii=False
    ).encode(
        "utf-8"
    )


    request = urllib.request.Request(
        url,
        data=body,
        method="POST"
    )


    request.add_header(
        "Content-Type",
        "application/json"
    )


    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:

            result = json.loads(
                response
                .read()
                .decode(
                    "utf-8"
                )
            )


    except urllib.error.HTTPError as error:

        raw = error.read().decode(
            "utf-8",
            errors="replace"
        )


        retry_after = None


        try:

            parsed = json.loads(
                raw
            )


            retry_after = (
                parsed
                .get(
                    "parameters",
                    {}
                )
                .get(
                    "retry_after"
                )
            )


            description = (
                parsed.get(
                    "description"
                )
                or raw
            )


        except Exception:

            description = raw


        raise TelegramSendError(
            (
                f"Telegram HTTP "
                f"{error.code}: "
                f"{description}"
            ),
            retry_after=retry_after
        )


    except urllib.error.URLError as error:

        raise TelegramSendError(
            (
                "Telegram network error: "
                f"{error}"
            )
        )


    if not result.get(
        "ok"
    ):

        retry_after = (
            result
            .get(
                "parameters",
                {}
            )
            .get(
                "retry_after"
            )
        )


        raise TelegramSendError(
            (
                "Telegram error: "
                f"{result}"
            ),
            retry_after=retry_after
        )


    return result


def send_message(
    chat_id,
    text,
    preview=False
):

    text = str(
        text or ""
    ).strip()


    if not text:

        raise ValueError(
            "Telegram message is empty"
        )


    chunks = [

        text[
            i:i + 4000
        ]

        for i in range(
            0,
            len(text),
            4000
        )
    ]


    for chunk in chunks:

        telegram_post(
            "sendMessage",
            {
                "chat_id":
                    chat_id,

                "text":
                    chunk,

                "disable_web_page_preview":
                    not preview
            }
        )


# =========================================================
# SHARED MEMORY HELPERS
# =========================================================

def save_message_history(
    chat_id,
    role,
    content
):

    text = str(
        content or ""
    ).strip()


    if not text:

        return


    try:

        with db_connect() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO messages (
                        chat_id,
                        role,
                        content
                    )

                    VALUES (
                        %s,
                        %s,
                        %s
                    );
                    """,
                    (
                        chat_id,
                        role,
                        text[
                            :12000
                        ]
                    )
                )


    except Exception as error:

        print(
            "⚠️ Market message history:",
            error
        )


def save_memory(
    user_id,
    category,
    content,
    importance=4,
    source="market_hunter"
):

    text = str(
        content or ""
    ).strip()


    if not text:

        return


    text = text[
        :6000
    ]


    try:

        with db_connect() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT id

                    FROM memories

                    WHERE
                        user_id = %s
                        AND LOWER(content)
                            = LOWER(%s)

                    LIMIT 1;
                    """,
                    (
                        user_id,
                        text
                    )
                )


                existing = cur.fetchone()


                if existing:

                    cur.execute(
                        """
                        UPDATE memories

                        SET
                            importance =
                            GREATEST(
                                importance,
                                %s
                            ),

                            updated_at =
                            NOW()

                        WHERE id = %s;
                        """,
                        (
                            importance,
                            existing[
                                "id"
                            ]
                        )
                    )


                    return


                cur.execute(
                    """
                    INSERT INTO memories (
                        user_id,
                        category,
                        content,
                        importance,
                        source
                    )

                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    );
                    """,
                    (
                        user_id,
                        category,
                        text,
                        importance,
                        source
                    )
                )


    except Exception as error:

        print(
            "⚠️ Market memory:",
            error
        )


def record_event(
    event_type,
    content,
    metadata=None
):

    if (
        TELEGRAM_ALLOWED_USER_ID
        == 0
    ):

        return


    try:

        with db_connect() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO kemo_events (
                        user_id,
                        chat_id,
                        event_type,
                        content,
                        metadata
                    )

                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s::jsonb
                    );
                    """,
                    (
                        TELEGRAM_ALLOWED_USER_ID,
                        TELEGRAM_ALLOWED_USER_ID,
                        str(
                            event_type
                        )[
                            :100
                        ],
                        str(
                            content or ""
                        )[
                            :6000
                        ],
                        json.dumps(
                            metadata or {},
                            ensure_ascii=False
                        )
                    )
                )


    except Exception as error:

        print(
            "⚠️ Market event:",
            error
        )


# =========================================================
# USER BUSINESS CONTEXT
# =========================================================

def load_business_context():

    if (
        TELEGRAM_ALLOWED_USER_ID
        == 0
    ):

        return ""


    sections = []


    try:

        with db_connect() as conn:

            with conn.cursor() as cur:

                # =========================================
                # PROFILE
                # =========================================

                cur.execute(
                    """
                    SELECT
                        fact_key,
                        fact_value

                    FROM profile_facts

                    WHERE user_id = %s

                    ORDER BY updated_at DESC

                    LIMIT 40;
                    """,
                    (
                        TELEGRAM_ALLOWED_USER_ID,
                    )
                )


                rows = cur.fetchall()


                if rows:

                    lines = [
                        "PROFILE:"
                    ]


                    for row in rows:

                        lines.append(
                            (
                                f"- {row['fact_key']}: "
                                f"{row['fact_value']}"
                            )
                        )


                    sections.append(
                        "\n".join(
                            lines
                        )
                    )


                # =========================================
                # IMPORTANT MEMORIES
                # =========================================

                cur.execute(
                    """
                    SELECT
                        category,
                        content,
                        importance

                    FROM memories

                    WHERE user_id = %s

                    ORDER BY
                        importance DESC,
                        updated_at DESC

                    LIMIT 30;
                    """,
                    (
                        TELEGRAM_ALLOWED_USER_ID,
                    )
                )


                rows = cur.fetchall()


                if rows:

                    lines = [
                        "IMPORTANT MEMORIES:"
                    ]


                    for row in rows:

                        lines.append(
                            (
                                f"- [{row['category']}] "
                                f"{row['content']}"
                            )
                        )


                    sections.append(
                        "\n".join(
                            lines
                        )
                    )


                # =========================================
                # LESSONS
                # =========================================

                cur.execute(
                    """
                    SELECT
                        content

                    FROM lessons

                    WHERE
                        user_id = %s
                        AND active = TRUE

                    ORDER BY id DESC

                    LIMIT 25;
                    """,
                    (
                        TELEGRAM_ALLOWED_USER_ID,
                    )
                )


                rows = cur.fetchall()


                if rows:

                    lines = [
                        "LESSONS:"
                    ]


                    for row in rows:

                        lines.append(
                            (
                                "- "
                                +
                                row[
                                    "content"
                                ]
                            )
                        )


                    sections.append(
                        "\n".join(
                            lines
                        )
                    )


    except Exception as error:

        print(
            "⚠️ Business context:",
            error
        )


    return (
        "\n\n".join(
            sections
        )[
            :18000
        ]
    )


# =========================================================
# TAVILY
# =========================================================

def tavily_search(
    query,
    deep=False,
    max_results=5
):

    if not TAVILY_API_KEY:

        raise RuntimeError(
            "TAVILY_API_KEY missing"
        )


    payload = {

        "query":
            query,

        "search_depth":
            (
                "advanced"
                if deep
                else
                "basic"
            ),

        "max_results":
            max_results,

        "include_answer":
            False,

        "include_raw_content":
            False
    }


    result = post_json(
        "https://api.tavily.com/search",
        payload,
        headers={
            "Authorization":
                f"Bearer {TAVILY_API_KEY}"
        },
        timeout=90
    )


    cleaned = []


    for item in (
        result.get(
            "results",
            []
        )
        or []
    )[:
        max_results
    ]:

        cleaned.append(
            {
                "title":
                    str(
                        item.get(
                            "title",
                            ""
                        )
                    )[
                        :350
                    ],

                "url":
                    str(
                        item.get(
                            "url",
                            ""
                        )
                    )[
                        :1600
                    ],

                "content":
                    str(
                        item.get(
                            "content",
                            ""
                        )
                    )[
                        :1100
                    ],

                "published_date":
                    str(
                        item.get(
                            "published_date",
                            ""
                        )
                        or ""
                    )[
                        :100
                    ],

                "query":
                    query
            }
        )


    return cleaned


# =========================================================
# GEMINI
# =========================================================

def extract_gemini_text(
    response
):

    candidates = response.get(
        "candidates",
        []
    )


    if not candidates:

        return ""


    parts = (
        candidates[
            0
        ]
        .get(
            "content",
            {}
        )
        .get(
            "parts",
            []
        )
    )


    texts = []


    for part in parts:

        text = part.get(
            "text"
        )


        if text:

            texts.append(
                text
            )


    return "\n".join(
        texts
    ).strip()


def call_gemini_json(
    user_prompt,
    system_prompt=MARKET_ANALYST_PROMPT
):

    last_error = None


    for model in MARKET_MODEL_FALLBACKS:

        try:

            url = (
                "https://generativelanguage."
                "googleapis.com/"
                f"v1beta/models/{model}:"
                "generateContent"
            )


            payload = {

                "system_instruction": {
                    "parts": [
                        {
                            "text":
                                system_prompt
                        }
                    ]
                },

                "contents": [
                    {
                        "role":
                            "user",

                        "parts": [
                            {
                                "text":
                                    user_prompt
                            }
                        ]
                    }
                ],

                "generationConfig": {

                    "temperature":
                        0.15,

                    "maxOutputTokens":
                        8192,

                    "responseMimeType":
                        "application/json"
                }
            }


            response = post_json(
                url,
                payload,
                headers={
                    "x-goog-api-key":
                        GEMINI_API_KEY
                },
                timeout=150
            )


            text = extract_gemini_text(
                response
            )


            if not text:

                raise RuntimeError(
                    "Gemini returned empty text"
                )


            return parse_json_object(
                text
            )


        except Exception as error:

            last_error = error


            print(
                (
                    "⚠️ Market Gemini "
                    f"{model}: "
                    f"{error}"
                )
            )


    raise RuntimeError(
        (
            "All market Gemini models failed: "
            f"{last_error}"
        )
    )


# =========================================================
# JSON PARSER
# =========================================================

def parse_json_object(
    value
):

    text = str(
        value or ""
    ).strip()


    if text.startswith(
        "```"
    ):

        text = re.sub(
            r"^```(?:json)?",
            "",
            text,
            flags=re.I
        )


        text = re.sub(
            r"```$",
            "",
            text
        ).strip()


    try:

        return json.loads(
            text
        )


    except Exception:

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

            return json.loads(
                text[
                    start:end + 1
                ]
            )


        raise


# =========================================================
# SEARCH QUERIES
# =========================================================

def build_quick_query_groups():

    year = local_now().year


    return [

        [
            (
                f"Palestine West Bank companies SMEs "
                f"digital transformation automation "
                f"marketing operational problems {year}"
            ),

            (
                f"MENA SMEs AI automation repetitive "
                f"workflows pain points demand {year}"
            ),

            (
                f"Arabic businesses hiring video "
                f"motion graphics content automation "
                f"demand {year}"
            )
        ],

        [
            (
                f"Middle East companies expensive "
                f"manual workflows automation opportunity "
                f"{year}"
            ),

            (
                f"MENA digital agencies service gaps "
                f"recurring revenue businesses {year}"
            ),

            (
                f"Palestine tenders digital marketing "
                f"media website software automation {year}"
            )
        ],

        [
            (
                f"Arabic ecommerce companies customer "
                f"service automation content bottlenecks "
                f"{year}"
            ),

            (
                f"MENA healthcare clinics digital "
                f"marketing appointment automation "
                f"problems {year}"
            ),

            (
                f"Middle East real estate companies "
                f"video lead automation pain points "
                f"{year}"
            )
        ],

        [
            (
                f"site:reddit.com small business "
                f"automation repetitive work agency "
                f"pain points {year}"
            ),

            (
                f"AI workflow business services "
                f"SMB high willingness to pay "
                f"{year}"
            ),

            (
                f"Arabic localization AI products "
                f"business market gap MENA {year}"
            )
        ]
    ]


def build_deep_queries():

    year = local_now().year


    return [

        (
            f"Palestine companies tenders digital "
            f"transformation marketing software "
            f"automation {year}"
        ),

        (
            f"MENA SME technology spending automation "
            f"marketing statistics {year}"
        ),

        (
            f"Middle East fastest growing B2B services "
            f"AI automation market {year}"
        ),

        (
            f"companies hiring AI automation specialists "
            f"Arabic Middle East {year}"
        ),

        (
            f"companies hiring motion graphics video "
            f"content Middle East {year}"
        ),

        (
            f"online business profit margins SaaS "
            f"agencies digital products creator economy "
            f"statistics {year}"
        ),

        (
            f"highest profit online business sectors "
            f"recurring revenue statistics {year}"
        ),

        (
            f"Arabic businesses complaints marketing "
            f"automation CRM customer service pain "
            f"points {year}"
        ),

        (
            f"MENA AI startups product launches "
            f"business service gaps {year}"
        ),

        (
            f"global B2B service trends not widely "
            f"available Arabic market {year}"
        )
    ]


# =========================================================
# COLLECT EVIDENCE
# =========================================================

def collect_search_evidence(
    scan_type
):

    evidence = []


    if scan_type == "deep":

        queries = build_deep_queries()


        for query in queries:

            try:

                evidence.extend(
                    tavily_search(
                        query,
                        deep=True,
                        max_results=5
                    )
                )

            except Exception as error:

                print(
                    (
                        "⚠️ Deep search failed: "
                        f"{error}"
                    )
                )


    else:

        groups = (
            build_quick_query_groups()
        )


        raw_index = get_state(
            "market_quick_group",
            "0"
        )


        try:

            group_index = int(
                raw_index
            )

        except Exception:

            group_index = 0


        queries = groups[
            group_index
            %
            len(
                groups
            )
        ]


        next_index = (
            group_index + 1
        ) % len(
            groups
        )


        set_state(
            "market_quick_group",
            next_index
        )


        for query in queries:

            try:

                evidence.extend(
                    tavily_search(
                        query,
                        deep=False,
                        max_results=5
                    )
                )

            except Exception as error:

                print(
                    (
                        "⚠️ Quick search failed: "
                        f"{error}"
                    )
                )


    # إزالة الروابط المكررة
    unique = []

    seen = set()


    for item in evidence:

        url = str(
            item.get(
                "url",
                ""
            )
        ).strip()


        key = (
            url
            or
            (
                item.get(
                    "title",
                    ""
                )
                +
                item.get(
                    "content",
                    ""
                )[
                    :100
                ]
            )
        )


        if key in seen:

            continue


        seen.add(
            key
        )


        unique.append(
            item
        )


    return (
        unique,
        len(
            queries
        )
    )


# =========================================================
# EXISTING WATCH LIST
# =========================================================

def load_market_watchlist():

    try:

        with db_connect() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        title,
                        score,
                        status,
                        opportunity

                    FROM market_opportunities

                    WHERE
                        user_id = %s
                        AND status
                        IN (
                            'watching',
                            'needs_evidence'
                        )

                    ORDER BY
                        score DESC,
                        last_seen_at DESC

                    LIMIT 15;
                    """,
                    (
                        TELEGRAM_ALLOWED_USER_ID,
                    )
                )


                rows = cur.fetchall()


                return rows


    except Exception:

        return []


# =========================================================
# ANALYSIS PROMPT
# =========================================================

def build_market_analysis_prompt(
    scan_type,
    evidence
):

    context = load_business_context()


    watchlist = load_market_watchlist()


    evidence_text = json.dumps(
        evidence[
            :50
        ],
        ensure_ascii=False,
        indent=2
    )


    watch_text = json.dumps(
        watchlist,
        ensure_ascii=False,
        default=str
    )


    return f"""
اليوم المحلي في فلسطين:
{local_time_string()}

نوع البحث:
{scan_type}

هذه معلومات حقيقية جلبتها أداة بحث من الإنترنت:

{evidence_text}

هذه فرص سبق أن وضعناها تحت المراقبة:

{watch_text}

سياق كريم المتوفر من الذاكرة:

{context}

حلل السوق ولا تنبهر بالترند.

استخرج فقط الفرص التي تستحق فعلاً.

يمكن أن تكون النتيجة بدون أي فرصة.

أريد JSON بهذا الشكل بالضبط:

{{
  "market_summary": "ملخص داخلي قصير",
  "opportunities": [
    {{
      "title": "اسم محدد جداً للفرصة",
      "dedupe_key": "اسم ثابت مختصر باللغة الانجليزية أو العربية",
      "short_summary": "جملتان",
      "problem": "المشكلة ومن يعاني منها ولماذا مهمة",
      "target_customer": "العميل المحدد الذي سيدفع",
      "solution": "الخدمة أو المنتج الذي يمكن بيعه",
      "why_karim": "سبب ملاءمتها لكريم",
      "revenue_model": "طريقة الربح",
      "estimated_price": "تقدير السعر مع توضيح أنه تقدير",
      "estimated_cost": "التكلفة المتوقعة كتقدير",
      "margin": "الهامش المتوقع كتقدير",
      "recurring_revenue": "كيف يصبح دخل متكرر",
      "first_customer_plan": [
        "خطوة 1",
        "خطوة 2",
        "خطوة 3"
      ],
      "competition": "المنافسة والحلول الحالية",
      "risks": "المخاطر وأسباب الفشل",
      "execution_window": "مستمرة أو عاجلة ولماذا",
      "first_action": "إجراء واحد فوري",
      "urgent": false,

      "evidence": [
        {{
          "claim": "ما الذي يثبته المصدر",
          "source_title": "العنوان",
          "url": "الرابط الموجود فعلاً في نتائج البحث",
          "date": "التاريخ إذا كان ظاهراً، وإلا اكتب غير ظاهر"
        }}
      ],

      "score_breakdown": {{
        "problem_strength": 0,
        "willingness_to_pay": 0,
        "market_size_growth": 0,
        "competition_gap": 0,
        "karim_fit": 0,
        "speed_to_first_customer": 0,
        "recurring_revenue": 0
      }},

      "confidence": "high"
    }}
  ]
}}

حدود النقاط:

problem_strength:
0 إلى 20

willingness_to_pay:
0 إلى 15

market_size_growth:
0 إلى 15

competition_gap:
0 إلى 15

karim_fit:
0 إلى 15

speed_to_first_customer:
0 إلى 10

recurring_revenue:
0 إلى 10

مهم جداً:

- لا تضع URL غير موجود في بيانات البحث.
- لا تختلق رقماً إحصائياً.
- إذا الرقم تقديري قل إنه تقدير.
- منشور Reddit ممكن يكشف مشكلة لكنه ليس إثباتاً وحده.
- الفرصة العامة لا تستحق 85.
- متجر إلكتروني عام ليس فرصة.
- وكالة تسويق عامة ليست فرصة.
- بيع تصاميم عام ليس فرصة.
- AI content عام ليس فرصة.
- التطبيق بدون مشكلة مثبتة ليس فرصة.
- الأفضل فرصة ضيقة ومحددة لها عميل واضح.
- لا ترفع Karim fit إذا لا يوجد سياق كاف.
- إذا لا توجد فرصة قوية أعد opportunities فارغة.
"""


# =========================================================
# SCORING
# =========================================================

SCORE_LIMITS = {

    "problem_strength":
        20,

    "willingness_to_pay":
        15,

    "market_size_growth":
        15,

    "competition_gap":
        15,

    "karim_fit":
        15,

    "speed_to_first_customer":
        10,

    "recurring_revenue":
        10
}


def safe_score(
    value,
    maximum
):

    try:

        number = int(
            round(
                float(
                    value
                )
            )
        )

    except Exception:

        number = 0


    return max(
        0,
        min(
            maximum,
            number
        )
    )


def calculate_score(
    opportunity
):

    breakdown = (
        opportunity.get(
            "score_breakdown",
            {}
        )
        or {}
    )


    clean = {}


    total = 0


    for key, maximum in (
        SCORE_LIMITS.items()
    ):

        value = safe_score(
            breakdown.get(
                key,
                0
            ),
            maximum
        )


        clean[
            key
        ] = value


        total += value


    opportunity[
        "score_breakdown"
    ] = clean


    opportunity[
        "score"
    ] = total


    return total


# =========================================================
# SOURCE VALIDATION
# =========================================================

def source_domain(
    url
):

    try:

        return (
            urllib.parse
            .urlparse(
                str(
                    url
                )
            )
            .netloc
            .lower()
            .replace(
                "www.",
                ""
            )
        )

    except Exception:

        return ""


def distinct_source_domains(
    opportunity
):

    domains = set()


    for evidence in (
        opportunity.get(
            "evidence",
            []
        )
        or []
    ):

        domain = source_domain(
            evidence.get(
                "url",
                ""
            )
        )


        if domain:

            domains.add(
                domain
            )


    return domains


# =========================================================
# DEDUPE KEY
# =========================================================

def normalize_key(
    value
):

    text = str(
        value or ""
    ).lower()


    text = re.sub(
        r"[^\w\u0600-\u06ff]+",
        " ",
        text
    )


    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def opportunity_dedupe_key(
    opportunity
):

    supplied = normalize_key(
        opportunity.get(
            "dedupe_key",
            ""
        )
    )


    if supplied:

        source = supplied


    else:

        source = normalize_key(
            (
                str(
                    opportunity.get(
                        "title",
                        ""
                    )
                )
                +
                " "
                +
                str(
                    opportunity.get(
                        "target_customer",
                        ""
                    )
                )
                +
                " "
                +
                str(
                    opportunity.get(
                        "problem",
                        ""
                    )
                )[
                    :300
                ]
            )
        )


    return hashlib.sha256(
        source.encode(
            "utf-8"
        )
    ).hexdigest()


# =========================================================
# SAVE / UPDATE OPPORTUNITY
# =========================================================

def upsert_opportunity(
    opportunity,
    status
):

    key = opportunity_dedupe_key(
        opportunity
    )


    title = str(
        opportunity.get(
            "title",
            "فرصة بدون عنوان"
        )
    )[
        :500
    ]


    score = int(
        opportunity.get(
            "score",
            0
        )
    )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    status,
                    score,
                    sent_at

                FROM market_opportunities

                WHERE
                    user_id = %s
                    AND dedupe_key = %s

                LIMIT 1;
                """,
                (
                    TELEGRAM_ALLOWED_USER_ID,
                    key
                )
            )


            existing = cur.fetchone()


            if existing:

                old_status = (
                    existing[
                        "status"
                    ]
                )


                cur.execute(
                    """
                    UPDATE market_opportunities

                    SET
                        title =
                            %s,

                        score =
                            GREATEST(
                                score,
                                %s
                            ),

                        opportunity =
                            %s::jsonb,

                        last_seen_at =
                            NOW(),

                        seen_count =
                            seen_count + 1,

                        status =
                            CASE
                                WHEN status = 'sent'
                                THEN 'sent'
                                ELSE %s
                            END

                    WHERE id = %s

                    RETURNING
                        id,
                        status,
                        score,
                        sent_at;
                    """,
                    (
                        title,
                        score,
                        json.dumps(
                            opportunity,
                            ensure_ascii=False
                        ),
                        status,
                        existing[
                            "id"
                        ]
                    )
                )


                row = cur.fetchone()


                return (
                    row,
                    old_status
                )


            cur.execute(
                """
                INSERT INTO market_opportunities (
                    user_id,
                    dedupe_key,
                    title,
                    score,
                    status,
                    opportunity
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::jsonb
                )

                RETURNING
                    id,
                    status,
                    score,
                    sent_at;
                """,
                (
                    TELEGRAM_ALLOWED_USER_ID,
                    key,
                    title,
                    score,
                    status,
                    json.dumps(
                        opportunity,
                        ensure_ascii=False
                    )
                )
            )


            row = cur.fetchone()


            return (
                row,
                None
            )


def mark_opportunity_sent(
    opportunity_id
):

    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE market_opportunities

                SET
                    status =
                        'sent',

                    sent_at =
                        NOW(),

                    last_seen_at =
                        NOW()

                WHERE id = %s;
                """,
                (
                    opportunity_id,
                )
            )


# =========================================================
# VALIDATION SEARCH
# =========================================================

def validate_opportunity(
    opportunity
):

    title = str(
        opportunity.get(
            "title",
            ""
        )
    )


    customer = str(
        opportunity.get(
            "target_customer",
            ""
        )
    )


    problem = str(
        opportunity.get(
            "problem",
            ""
        )
    )


    queries = [

        (
            f"{title} {customer} "
            f"market demand companies"
        ),

        (
            f"{problem[:250]} "
            f"{customer} competitors pricing"
        )
    ]


    validation_results = []


    for query in queries:

        try:

            validation_results.extend(
                tavily_search(
                    query,
                    deep=True,
                    max_results=5
                )
            )

        except Exception as error:

            print(
                "⚠️ Validation search:",
                error
            )


    if not validation_results:

        return opportunity


    prompt = f"""
هذه فرصة أولية:

{json.dumps(
    opportunity,
    ensure_ascii=False,
    indent=2
)}

بحث تحقق إضافي:

{json.dumps(
    validation_results,
    ensure_ascii=False,
    indent=2
)}

أعد تقييم الفرصة بصرامة.

لا تدافع عن التقييم القديم.

إذا البحث الإضافي كشف منافسة قوية
أو ضعف استعداد للدفع،
اخفض النقاط.

إذا الأدلة لا تكفي،
اخفض النقاط.

أخرج JSON:

{{
  "opportunity": {{
    "title": "...",
    "dedupe_key": "...",
    "short_summary": "...",
    "problem": "...",
    "target_customer": "...",
    "solution": "...",
    "why_karim": "...",
    "revenue_model": "...",
    "estimated_price": "...",
    "estimated_cost": "...",
    "margin": "...",
    "recurring_revenue": "...",
    "first_customer_plan": ["...", "..."],
    "competition": "...",
    "risks": "...",
    "execution_window": "...",
    "first_action": "...",
    "urgent": false,
    "confidence": "high",
    "evidence": [
      {{
        "claim": "...",
        "source_title": "...",
        "url": "...",
        "date": "..."
      }}
    ],
    "score_breakdown": {{
      "problem_strength": 0,
      "willingness_to_pay": 0,
      "market_size_growth": 0,
      "competition_gap": 0,
      "karim_fit": 0,
      "speed_to_first_customer": 0,
      "recurring_revenue": 0
    }}
  }}
}}

استخدم فقط الروابط الموجودة في البحث الأول
أو بحث التحقق.
"""


    result = call_gemini_json(
        prompt
    )


    final = result.get(
        "opportunity"
    )


    if not isinstance(
        final,
        dict
    ):

        return opportunity


    calculate_score(
        final
    )


    return final


# =========================================================
# ALERT FORMAT
# =========================================================

def text_value(
    value,
    fallback="غير واضح"
):

    text = str(
        value or ""
    ).strip()


    return (
        text
        if text
        else fallback
    )


def format_opportunity_alert(
    opportunity
):

    score = int(
        opportunity.get(
            "score",
            0
        )
    )


    lines = [

        "🚨 كيمو لقط شغلة قوية",
        "",

        "الفرصة باختصار:",
        text_value(
            opportunity.get(
                "short_summary"
            )
        ),
        "",

        "المشكلة الموجودة:",
        text_value(
            opportunity.get(
                "problem"
            )
        ),
        "",

        "الدليل:"
    ]


    evidence = (
        opportunity.get(
            "evidence",
            []
        )
        or []
    )


    for index, item in enumerate(
        evidence[
            :5
        ],
        start=1
    ):

        claim = text_value(
            item.get(
                "claim"
            )
        )


        title = text_value(
            item.get(
                "source_title"
            )
        )


        url = text_value(
            item.get(
                "url"
            )
        )


        date = text_value(
            item.get(
                "date"
            ),
            "التاريخ غير ظاهر"
        )


        lines.append(
            (
                f"{index}. {claim}\n"
                f"المصدر: {title}\n"
                f"التاريخ: {date}\n"
                f"{url}"
            )
        )


    lines.extend(
        [
            "",

            "العميل الذي سيدفع:",
            text_value(
                opportunity.get(
                    "target_customer"
                )
            ),
            "",

            "الحل الذي يمكن أن نبيعه:",
            text_value(
                opportunity.get(
                    "solution"
                )
            ),
            "",

            "لماذا كريم تحديداً؟",
            text_value(
                opportunity.get(
                    "why_karim"
                )
            ),
            "",

            "طريقة الربح:",
            (
                "السعر المتوقع: "
                +
                text_value(
                    opportunity.get(
                        "estimated_price"
                    )
                )
            ),
            (
                "التكلفة المتوقعة: "
                +
                text_value(
                    opportunity.get(
                        "estimated_cost"
                    )
                )
            ),
            (
                "الهامش: "
                +
                text_value(
                    opportunity.get(
                        "margin"
                    )
                )
            ),
            (
                "الدخل المتكرر: "
                +
                text_value(
                    opportunity.get(
                        "recurring_revenue"
                    )
                )
            ),
            "",

            "خطة الوصول لأول عميل:"
        ]
    )


    plan = (
        opportunity.get(
            "first_customer_plan",
            []
        )
        or []
    )


    for index, step in enumerate(
        plan[
            :6
        ],
        start=1
    ):

        lines.append(
            f"{index}. {step}"
        )


    lines.extend(
        [
            "",

            "المنافسة والمخاطر:",
            (
                text_value(
                    opportunity.get(
                        "competition"
                    )
                )
                +
                "\n"
                +
                text_value(
                    opportunity.get(
                        "risks"
                    )
                )
            ),
            "",

            "نافذة التنفيذ:",
            text_value(
                opportunity.get(
                    "execution_window"
                )
            ),
            "",

            "تقييم كيمو:",
            f"{score}/100"
        ]
    )


    breakdown = (
        opportunity.get(
            "score_breakdown",
            {}
        )
        or {}
    )


    lines.extend(
        [
            (
                "• قوة المشكلة: "
                f"{breakdown.get('problem_strength', 0)}/20"
            ),

            (
                "• استعداد العميل للدفع: "
                f"{breakdown.get('willingness_to_pay', 0)}/15"
            ),

            (
                "• حجم/نمو السوق: "
                f"{breakdown.get('market_size_growth', 0)}/15"
            ),

            (
                "• فجوة المنافسة: "
                f"{breakdown.get('competition_gap', 0)}/15"
            ),

            (
                "• ملاءمتها إلنا: "
                f"{breakdown.get('karim_fit', 0)}/15"
            ),

            (
                "• سرعة أول عميل: "
                f"{breakdown.get('speed_to_first_customer', 0)}/10"
            ),

            (
                "• الدخل المتكرر: "
                f"{breakdown.get('recurring_revenue', 0)}/10"
            ),

            "",

            "أول خطوة الآن:",
            text_value(
                opportunity.get(
                    "first_action"
                )
            )
        ]
    )


    return "\n".join(
        lines
    )


# =========================================================
# SEND MARKET ALERT
# =========================================================

def send_market_alert(
    db_row,
    opportunity
):

    if (
        db_row.get(
            "sent_at"
        )
        is not None
        or
        db_row.get(
            "status"
        )
        == "sent"
    ):

        return False


    alert = format_opportunity_alert(
        opportunity
    )


    send_message(
        TELEGRAM_ALLOWED_USER_ID,
        alert,
        preview=False
    )


    mark_opportunity_sent(
        db_row[
            "id"
        ]
    )


    save_message_history(
        TELEGRAM_ALLOWED_USER_ID,
        "assistant",
        alert
    )


    save_memory(
        TELEGRAM_ALLOWED_USER_ID,
        "opportunity",
        (
            "فرصة سوق قوية أرسلها Kemo:\n"
            +
            alert
        ),
        importance=5,
        source="market_hunter"
    )


    record_event(
        "market_opportunity_alert_sent",
        opportunity.get(
            "title",
            ""
        ),
        {
            "opportunity_id":
                db_row[
                    "id"
                ],

            "score":
                opportunity.get(
                    "score"
                )
        }
    )


    print(
        (
            "🚨 Strong opportunity sent | "
            f"{opportunity.get('score')}/100 | "
            f"{opportunity.get('title')}"
        )
    )


    return True


# =========================================================
# SCAN LOG
# =========================================================

def start_scan_log(
    scan_type
):

    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO market_scan_runs (
                    scan_type,
                    status
                )

                VALUES (
                    %s,
                    'running'
                )

                RETURNING id;
                """,
                (
                    scan_type,
                )
            )


            return cur.fetchone()[
                "id"
            ]


def finish_scan_log(
    scan_id,
    *,
    search_count,
    result_count,
    candidate_count,
    alert_count,
    error=None
):

    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE market_scan_runs

                SET
                    finished_at =
                        NOW(),

                    search_count =
                        %s,

                    result_count =
                        %s,

                    candidate_count =
                        %s,

                    alert_count =
                        %s,

                    status =
                        %s,

                    error =
                        %s

                WHERE id = %s;
                """,
                (
                    search_count,
                    result_count,
                    candidate_count,
                    alert_count,
                    (
                        "failed"
                        if error
                        else
                        "completed"
                    ),
                    (
                        str(
                            error
                        )[
                            :3000
                        ]
                        if error
                        else None
                    ),
                    scan_id
                )
            )


# =========================================================
# RUN MARKET SCAN
# =========================================================

market_scan_lock = threading.Lock()


def run_market_scan(
    scan_type
):

    if not market_scan_lock.acquire(
        blocking=False
    ):

        print(
            "ℹ️ Market scan already running"
        )

        return


    scan_id = None


    search_count = 0

    result_count = 0

    candidate_count = 0

    alert_count = 0


    try:

        print(
            (
                "🔎 Kemo market scan started | "
                f"{scan_type} | "
                f"{local_time_string()}"
            )
        )


        scan_id = start_scan_log(
            scan_type
        )


        evidence, search_count = (
            collect_search_evidence(
                scan_type
            )
        )


        result_count = len(
            evidence
        )


        if not evidence:

            raise RuntimeError(
                "Market scan returned no search evidence"
            )


        analysis = call_gemini_json(
            build_market_analysis_prompt(
                scan_type,
                evidence
            )
        )


        opportunities = (
            analysis.get(
                "opportunities",
                []
            )
            or []
        )


        if not isinstance(
            opportunities,
            list
        ):

            opportunities = []


        cleaned = []


        for opportunity in opportunities:

            if not isinstance(
                opportunity,
                dict
            ):

                continue


            score = calculate_score(
                opportunity
            )


            if (
                score
                <
                MARKET_WATCH_SCORE
            ):

                continue


            cleaned.append(
                opportunity
            )


        cleaned.sort(
            key=lambda item: (
                item.get(
                    "score",
                    0
                )
            ),
            reverse=True
        )


        candidate_count = len(
            cleaned
        )


        # ================================================
        # نتحقق فقط من أقوى فرصتين
        # حتى ما نصرف API بلا داعي.
        # ================================================

        high_candidates = [

            item

            for item in cleaned

            if (
                item.get(
                    "score",
                    0
                )
                >=
                MARKET_ALERT_SCORE
            )
        ][
            :2
        ]


        validated_ids = set()


        for candidate in high_candidates:

            try:

                validated = validate_opportunity(
                    candidate
                )


                calculate_score(
                    validated
                )


                candidate.clear()

                candidate.update(
                    validated
                )


                validated_ids.add(
                    id(
                        candidate
                    )
                )


            except Exception as error:

                print(
                    (
                        "⚠️ Opportunity validation: "
                        f"{error}"
                    )
                )


        # ================================================
        # SAVE ALL 75+
        # ================================================

        send_queue = []


        for opportunity in cleaned:

            score = int(
                opportunity.get(
                    "score",
                    0
                )
            )


            domains = (
                distinct_source_domains(
                    opportunity
                )
            )


            if (
                score
                >=
                MARKET_ALERT_SCORE
                and
                len(
                    domains
                )
                >= 2
            ):

                status = "ready"


            elif (
                score
                >=
                MARKET_ALERT_SCORE
            ):

                status = (
                    "needs_evidence"
                )


            else:

                status = "watching"


            row, old_status = (
                upsert_opportunity(
                    opportunity,
                    status
                )
            )


            # ما نعيد فرصة انبعثت قبل
            if (
                old_status == "sent"
                or
                row.get(
                    "status"
                )
                == "sent"
            ):

                continue


            if status == "ready":

                send_queue.append(
                    (
                        opportunity,
                        row
                    )
                )


        # ================================================
        # أرسل أقوى فرصة فقط بكل scan
        # ================================================

        if send_queue:

            send_queue.sort(
                key=lambda pair: (
                    pair[
                        0
                    ].get(
                        "score",
                        0
                    )
                ),
                reverse=True
            )


            opportunity, row = (
                send_queue[
                    0
                ]
            )


            if send_market_alert(
                row,
                opportunity
            ):

                alert_count = 1


        summary = str(
            analysis.get(
                "market_summary",
                ""
            )
        ).strip()


        if summary:

            set_state(
                (
                    "market_last_"
                    f"{scan_type}_summary"
                ),
                summary[
                    :7000
                ]
            )


        now_iso = utc_now().isoformat()


        set_state(
            (
                "market_last_"
                f"{scan_type}"
            ),
            now_iso
        )


        # deep محسوب كـquick أيضاً
        if scan_type == "deep":

            set_state(
                "market_last_quick",
                now_iso
            )


        if scan_id:

            finish_scan_log(
                scan_id,
                search_count=(
                    search_count
                ),
                result_count=(
                    result_count
                ),
                candidate_count=(
                    candidate_count
                ),
                alert_count=(
                    alert_count
                )
            )


        print(
            (
                "✅ Market scan complete | "
                f"{scan_type} | "
                f"sources={result_count} | "
                f"candidates={candidate_count} | "
                f"alerts={alert_count}"
            )
        )


    except Exception as error:

        print(
            (
                "❌ Market scan failed: "
                f"{error}"
            )
        )


        if scan_id:

            try:

                finish_scan_log(
                    scan_id,
                    search_count=(
                        search_count
                    ),
                    result_count=(
                        result_count
                    ),
                    candidate_count=(
                        candidate_count
                    ),
                    alert_count=(
                        alert_count
                    ),
                    error=error
                )

            except Exception:

                pass


    finally:

        market_scan_lock.release()


# =========================================================
# WEEKLY INTERNAL SUMMARY
# =========================================================

def build_weekly_market_summary():

    try:

        with db_connect() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        title,
                        score,
                        status,
                        opportunity,
                        first_seen_at,
                        last_seen_at,
                        seen_count

                    FROM market_opportunities

                    WHERE
                        user_id = %s
                        AND last_seen_at
                        >= NOW()
                        - INTERVAL '7 days'

                    ORDER BY
                        score DESC,
                        last_seen_at DESC

                    LIMIT 30;
                    """,
                    (
                        TELEGRAM_ALLOWED_USER_ID,
                    )
                )


                rows = cur.fetchall()


        if not rows:

            set_state(
                "market_weekly_summary",
                (
                    "هذا الأسبوع لم تتجمع فرص "
                    "تجارية قوية كفاية."
                )
            )


            set_state(
                "market_last_weekly",
                utc_now().isoformat()
            )


            return


        prompt = f"""
هذه نتائج Kemo Market Hunter خلال آخر أسبوع:

{json.dumps(
    rows,
    ensure_ascii=False,
    default=str,
    indent=2
)}

اكتب ملخصاً داخلياً فقط، لا رسالة للمستخدم.

حدد:

1. القطاعات التي تتكرر فيها المشكلة.
2. أين يبدو استعداد الدفع أعلى.
3. الفرص التي تحتاج مراقبة إضافية.
4. الفرص التي فقدت قوتها ولماذا.
5. إشارات مهمة عن طرق تحقيق الدخل أونلاين.
6. ما الذي يجب أن تركز عليه عمليات البحث الأسبوع القادم.

لا تختلق معلومة جديدة.
استخدم فقط البيانات أعلاه.

أخرج JSON:

{{
  "summary": "..."
}}
"""


        result = call_gemini_json(
            prompt
        )


        summary = str(
            result.get(
                "summary",
                ""
            )
        ).strip()


        if summary:

            set_state(
                "market_weekly_summary",
                summary[
                    :12000
                ]
            )


        set_state(
            "market_last_weekly",
            utc_now().isoformat()
        )


        print(
            "✅ Weekly market intelligence updated"
        )


    except Exception as error:

        print(
            (
                "⚠️ Weekly market summary: "
                f"{error}"
            )
        )


# =========================================================
# MARKET TIMING
# =========================================================

def is_due(
    state_key,
    hours
):

    previous = parse_state_datetime(
        get_state(
            state_key
        )
    )


    if previous is None:

        return True


    age = (
        utc_now()
        -
        previous.astimezone(
            ZoneInfo(
                "UTC"
            )
        )
    )


    return (
        age.total_seconds()
        >=
        hours * 3600
    )


def maybe_run_market_research():

    # ================================================
    # Deep أولاً.
    # إذا deep مستحق ما بنعمل quick بنفس اللحظة.
    # ================================================

    if is_due(
        "market_last_deep",
        MARKET_DEEP_HOURS
    ):

        run_market_scan(
            "deep"
        )


    elif is_due(
        "market_last_quick",
        MARKET_QUICK_HOURS
    ):

        run_market_scan(
            "quick"
        )


    if is_due(
        "market_last_weekly",
        MARKET_WEEKLY_HOURS
    ):

        build_weekly_market_summary()


# =========================================================
# MARKET THREAD
# =========================================================

def market_watch_loop():

    # نعطي السيرفر وقت يقوم
    time.sleep(
        20
    )


    while True:

        try:

            maybe_run_market_research()


        except Exception as error:

            print(
                (
                    "❌ Market watch loop: "
                    f"{error}"
                )
            )


        # نفحص هل حان موعد scan مرة بالدقيقة.
        # هذا لا يعني بحث كل دقيقة.
        time.sleep(
            60
        )


# =========================================================
# RECOVER STUCK REMINDER JOBS
# =========================================================

def recover_stuck_jobs():

    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE scheduled_jobs

                SET
                    status =
                        'pending',

                    locked_at =
                        NULL,

                    updated_at =
                        NOW(),

                    last_error =
                        COALESCE(
                            last_error,
                            ''
                        )
                        ||
                        CASE
                            WHEN last_error IS NULL
                            OR last_error = ''
                            THEN ''
                            ELSE E'\\n'
                        END
                        ||
                        'Recovered after scheduler restart'

                WHERE
                    status =
                        'processing'

                    AND locked_at
                    <
                    NOW()
                    -
                    (
                        %s
                        *
                        INTERVAL '1 minute'
                    );
                """,
                (
                    STUCK_JOB_MINUTES,
                )
            )


            recovered = (
                cur.rowcount
            )


    if recovered:

        print(
            (
                "♻️ Recovered "
                f"{recovered} "
                "stuck reminder job(s)"
            )
        )


# =========================================================
# CLAIM NEXT REMINDER JOB
# =========================================================

def claim_next_job():

    with db_connect() as conn:

        with conn.cursor() as cur:

            if TELEGRAM_ALLOWED_USER_ID:

                cur.execute(
                    """
                    SELECT
                        id,
                        user_id,
                        chat_id,
                        job_type,
                        title,
                        message,
                        run_at,
                        timezone,
                        status,
                        metadata,
                        attempts,
                        max_attempts

                    FROM scheduled_jobs

                    WHERE
                        status =
                            'pending'

                        AND user_id =
                            %s

                        AND run_at
                            <= NOW()

                        AND (
                            next_attempt_at
                            IS NULL

                            OR

                            next_attempt_at
                            <= NOW()
                        )

                    ORDER BY
                        run_at ASC,
                        id ASC

                    FOR UPDATE
                    SKIP LOCKED

                    LIMIT 1;
                    """,
                    (
                        TELEGRAM_ALLOWED_USER_ID,
                    )
                )


            else:

                cur.execute(
                    """
                    SELECT
                        id,
                        user_id,
                        chat_id,
                        job_type,
                        title,
                        message,
                        run_at,
                        timezone,
                        status,
                        metadata,
                        attempts,
                        max_attempts

                    FROM scheduled_jobs

                    WHERE
                        status =
                            'pending'

                        AND run_at
                            <= NOW()

                        AND (
                            next_attempt_at
                            IS NULL

                            OR

                            next_attempt_at
                            <= NOW()
                        )

                    ORDER BY
                        run_at ASC,
                        id ASC

                    FOR UPDATE
                    SKIP LOCKED

                    LIMIT 1;
                    """
                )


            job = cur.fetchone()


            if not job:

                return None


            cur.execute(
                """
                UPDATE scheduled_jobs

                SET
                    status =
                        'processing',

                    locked_at =
                        NOW(),

                    attempts =
                        attempts + 1,

                    updated_at =
                        NOW()

                WHERE id = %s;
                """,
                (
                    job[
                        "id"
                    ],
                )
            )


            job[
                "attempts"
            ] += 1


            return job


# =========================================================
# MARK JOB SENT
# =========================================================

def mark_job_sent(
    job_id
):

    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE scheduled_jobs

                SET
                    status =
                        'sent',

                    sent_at =
                        NOW(),

                    locked_at =
                        NULL,

                    next_attempt_at =
                        NULL,

                    last_error =
                        NULL,

                    updated_at =
                        NOW()

                WHERE id = %s;
                """,
                (
                    job_id,
                )
            )


# =========================================================
# JOB ERROR / RETRY
# =========================================================

def mark_job_error(
    job,
    error,
    retry_after=None
):

    attempts = int(
        job.get(
            "attempts",
            1
        )
    )


    max_attempts = int(
        job.get(
            "max_attempts",
            5
        )
    )


    error_text = str(
        error
    )[
        :3000
    ]


    if attempts >= max_attempts:

        with db_connect() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    UPDATE scheduled_jobs

                    SET
                        status =
                            'failed',

                        locked_at =
                            NULL,

                        last_error =
                            %s,

                        updated_at =
                            NOW()

                    WHERE id = %s;
                    """,
                    (
                        error_text,
                        job[
                            "id"
                        ]
                    )
                )


        print(
            (
                "❌ Job "
                f"#{job['id']} "
                "failed permanently"
            )
        )


        return


    if retry_after is not None:

        try:

            delay_seconds = max(
                1,
                int(
                    retry_after
                )
            )


        except Exception:

            delay_seconds = 10


    else:

        delay_seconds = min(
            300,
            5
            *
            (
                2
                **
                max(
                    0,
                    attempts - 1
                )
            )
        )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE scheduled_jobs

                SET
                    status =
                        'pending',

                    locked_at =
                        NULL,

                    next_attempt_at =
                        NOW()
                        +
                        (
                            %s
                            *
                            INTERVAL '1 second'
                        ),

                    last_error =
                        %s,

                    updated_at =
                        NOW()

                WHERE id = %s;
                """,
                (
                    delay_seconds,
                    error_text,
                    job[
                        "id"
                    ]
                )
            )


    print(
        (
            "🔁 Job "
            f"#{job['id']} "
            "will retry in "
            f"{delay_seconds}s"
        )
    )


# =========================================================
# EXECUTE REMINDER JOB
# =========================================================

def execute_job(
    job
):

    job_id = job[
        "id"
    ]


    chat_id = job[
        "chat_id"
    ]


    message = job[
        "message"
    ]


    print(
        (
            "⏰ Executing job "
            f"#{job_id} | "
            f"{local_time_string()}"
        )
    )


    try:

        send_message(
            chat_id,
            message
        )


        mark_job_sent(
            job_id
        )


        print(
            (
                "✅ Job "
                f"#{job_id} sent"
            )
        )


    except TelegramSendError as error:

        print(
            (
                "⚠️ Telegram job "
                f"#{job_id}: "
                f"{error}"
            )
        )


        mark_job_error(
            job,
            error,
            retry_after=(
                error.retry_after
            )
        )


    except Exception as error:

        print(
            (
                "⚠️ Job "
                f"#{job_id}: "
                f"{error}"
            )
        )


        mark_job_error(
            job,
            error
        )


# =========================================================
# PROCESS DUE REMINDERS
# =========================================================

def process_due_jobs():

    processed = 0


    while True:

        job = claim_next_job()


        if not job:

            break


        execute_job(
            job
        )


        processed += 1


        if processed >= 50:

            break


    return processed


# =========================================================
# CLOCK
# =========================================================

def print_clock_status():

    print(
        (
            "🕒 Palestine time: "
            f"{local_time_string()}"
        )
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("")


    print(
        "======================================"
    )


    print(
        "       KEMO SCHEDULER V4"
    )


    print(
        "       + MARKET HUNTER"
    )


    print(
        "======================================"
    )


    # =====================================================
    # REQUIRED REMINDER ENV
    # =====================================================

    if not TELEGRAM_BOT_TOKEN:

        print(
            "❌ TELEGRAM_BOT_TOKEN missing"
        )

        return


    if not DATABASE_URL:

        print(
            "❌ DATABASE_URL missing"
        )

        return


    if (
        TELEGRAM_ALLOWED_USER_ID
        == 0
    ):

        print(
            "❌ TELEGRAM_ALLOWED_USER_ID missing"
        )

        return


    # =====================================================
    # DATABASE
    # =====================================================

    try:

        init_database()

        recover_stuck_jobs()


    except Exception as error:

        print(
            (
                "❌ Scheduler database: "
                f"{error}"
            )
        )


        return


    # =====================================================
    # STATUS
    # =====================================================

    print(
        (
            "✅ Timezone: "
            f"{KEMO_TIMEZONE}"
        )
    )


    print_clock_status()


    print(
        (
            "✅ Reminder poll every "
            f"{POLL_INTERVAL_SECONDS}s"
        )
    )


    print(
        "✅ Telegram sender ready"
    )


    print(
        "✅ Persistent reminders ready"
    )


    print(
        (
            "✅ Master Kemo system prompt: "
            "stored"
        )
    )


    # =====================================================
    # MARKET HUNTER
    # =====================================================

    market_ready = (

        MARKET_SCAN_ENABLED

        and

        bool(
            GEMINI_API_KEY
        )

        and

        bool(
            TAVILY_API_KEY
        )
    )


    if market_ready:

        print(
            "✅ Kemo Market Hunter: ACTIVE"
        )


        print(
            (
                "✅ Quick market scan: every "
                f"{MARKET_QUICK_HOURS:g}h"
            )
        )


        print(
            (
                "✅ Deep market scan: every "
                f"{MARKET_DEEP_HOURS:g}h"
            )
        )


        print(
            (
                "✅ Strong opportunity threshold: "
                f"{MARKET_ALERT_SCORE}/100"
            )
        )


        print(
            (
                "✅ Watch threshold: "
                f"{MARKET_WATCH_SCORE}/100"
            )
        )


        print(
            "✅ Two-source validation required"
        )


        print(
            "✅ Strong opportunity alerts: Telegram"
        )


        market_thread = threading.Thread(
            target=market_watch_loop,
            name="kemo-market-hunter",
            daemon=True
        )


        market_thread.start()


    else:

        print(
            "⚠️ Kemo Market Hunter: DISABLED"
        )


        if not MARKET_SCAN_ENABLED:

            print(
                "   reason: KEMO_MARKET_SCAN_ENABLED=0"
            )


        if not GEMINI_API_KEY:

            print(
                "   reason: GEMINI_API_KEY missing"
            )


        if not TAVILY_API_KEY:

            print(
                "   reason: TAVILY_API_KEY missing"
            )


    print(
        "✅ Scheduler online"
    )


    print("")


    last_heartbeat = 0

    last_recovery_check = 0


    # =====================================================
    # REMINDER LOOP
    # =====================================================

    while True:

        try:

            now_monotonic = (
                time.monotonic()
            )


            # =============================================
            # HEARTBEAT
            # =============================================

            if (
                now_monotonic
                -
                last_heartbeat
                >= 30
            ):

                update_scheduler_heartbeat()


                last_heartbeat = (
                    now_monotonic
                )


            # =============================================
            # RECOVERY
            # =============================================

            if (
                now_monotonic
                -
                last_recovery_check
                >= 60
            ):

                recover_stuck_jobs()


                last_recovery_check = (
                    now_monotonic
                )


            # =============================================
            # REMINDERS
            # =============================================

            process_due_jobs()


            time.sleep(
                POLL_INTERVAL_SECONDS
            )


        except KeyboardInterrupt:

            print(
                "🛑 Scheduler stopped"
            )


            break


        except Exception as error:

            print(
                (
                    "❌ Scheduler loop: "
                    f"{error}"
                )
            )


            time.sleep(
                3
            )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()


# =========================================================
# KEMO SCHEDULER V4
# PROACTIVE MARKET HUNTER
# =========================================================
