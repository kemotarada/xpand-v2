# =========================================================
# KEMO HUMAN CORE V7
#
# Telegram text + voice
# Shared Master System Prompt
# PERMANENT MEMORY V2
# Canonical facts + history
# Full conversation archive
# Background memory learning
# Smart memory retrieval
# Anti-hallucination personal memory
# Exact Palestine time
# Persistent reminders
# =========================================================

import os
import re
import json
import time
import base64
import uuid
import hashlib
import threading
import subprocess
import urllib.request
import urllib.error

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg
import imageio_ffmpeg


# =========================================================
# ENV
# =========================================================

TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
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

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    ""
).strip()

KEMO_CALL_URL = os.environ.get(
    "KEMO_CALL_URL",
    ""
).strip().rstrip("/")

KEMO_TIMEZONE = os.environ.get(
    "KEMO_TIMEZONE",
    "Asia/Hebron"
).strip()

KEMO_VOICE = (
    os.environ.get(
        "KEMO_VOICE",
        ""
    ).strip()
    or
    os.environ.get(
        "KEMO_TTS_VOICE",
        ""
    ).strip()
    or
    "Iapetus"
)

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
# TIMEZONE
# =========================================================

try:
    LOCAL_TZ = ZoneInfo(
        KEMO_TIMEZONE
    )
except Exception:
    LOCAL_TZ = ZoneInfo(
        "Asia/Hebron"
    )


# =========================================================
# MODELS
# =========================================================

def env_model_list(
    env_name,
    defaults
):
    raw = os.environ.get(
        env_name,
        ""
    ).strip()

    if not raw:
        return defaults

    values = [
        item.strip()
        for item in raw.split(",")
        if item.strip()
    ]

    return values or defaults


# السرعة أولاً بالمحادثة العادية.
# التحليل الثقيل يروح تلقائياً لـ 3.7.
GEMINI_MODELS = env_model_list(
    "KEMO_CHAT_MODELS",
    [
        "gemini-3.5-flash-lite",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
    ]
)

DEEP_CHAT_MODELS = env_model_list(
    "KEMO_DEEP_CHAT_MODELS",
    [
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
    ]
)

MEMORY_EXTRACT_MODELS = env_model_list(
    "KEMO_MEMORY_EXTRACT_MODELS",
    [
        "gemini-3.5-flash-lite",
        "gemini-3.7-flash",
    ]
)

TRANSCRIBE_MODEL = os.environ.get(
    "KEMO_TRANSCRIBE_MODEL",
    "gemini-3.5-transcribe"
).strip()

TRANSCRIBE_FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]

TTS_MODELS = env_model_list(
    "KEMO_TTS_MODELS",
    [
        "gemini-3.1-flash-tts-preview",
        "gemini-2.5-flash-preview-tts",
    ]
)


# =========================================================
# LIMITS
# =========================================================

RECENT_MESSAGES_LIMIT = 14

MAX_PROFILE_FACTS = 25
MAX_LESSONS = 30

MAX_GENERAL_MEMORIES = 14
MAX_CANONICAL_FACTS = 18
MAX_ARCHIVE_MATCHES = 10
MAX_CALL_ARTIFACTS = 8
MAX_MARKET_OPPORTUNITIES = 5

MAX_TELEGRAM_VOICE_BYTES = (
    19 * 1024 * 1024
)

TTS_MIN_INTERVAL_SECONDS = 6.5
TTS_MAX_WAIT_SECONDS = 65

TTS_LAST_REQUEST_TIME = {}


# =========================================================
# MASTER SYSTEM PROMPT VERSION
# =========================================================

MASTER_PROMPT_VERSION = (
    "2026-09-02-xpand-master-v1"
)


# =========================================================
# MASTER SYSTEM PROMPT
# =========================================================

MASTER_SYSTEM_PROMPT = r"""
# XPAND — SYSTEM PROMPT

## 1. الهوية الأساسية

أنت **XPAND – إكسباند**، وكيل ذكاء اصطناعي شخصي وتجاري تعمل مع **كريم** كشريك تفكير وموظف ذكي ومستشار مقرّب، وليس كمساعد آلي تقليدي.

مهمتك الأساسية:

- مساعدة كريم في أعماله ومشاريعه وقراراته.
- التفكير معه بطريقة ذكية، واقعية، عملية وتجارية.
- اكتشاف الفرص القوية في السوق قبل أن تصبح مزدحمة.
- اقتراح أفكار يمكن تحويلها إلى خدمات أو منتجات أو مصادر دخل حقيقية.
- متابعة المشاريع والمهام والتقدم فيها.
- تنبيه كريم للمخاطر والثغرات والفرص التي تستحق الانتباه.
- التعلم المستمر من أسلوب كريم وكلماته وتفضيلاته وقراراته السابقة.

اسم المستخدم هو: **كريم**.

تحدث معه كشخص يعرفه جيداً، وليس كعميل جديد في كل محادثة.

---

## 2. شخصية إكسباند

إكسباند يتمتع بالشخصيات التالية في الوقت نفسه:

- ذكي جداً وسريع البديهة.
- عملي ويعرف كيف يحول الكلام إلى خطوات قابلة للتنفيذ.
- حيوي وممتع وغير ممل.
- يمتلك حساً فكاهياً طبيعياً.
- يمزح مع كريم باللهجة الفلسطينية عندما يكون الوقت والموقف مناسبين.
- يعرف متى يمزح ومتى يتحدث بجدية.
- صريح ولا يجامل كريم على حساب الحقيقة.
- يحترم كريم دائماً حتى أثناء المزاح.
- يتحدث بثقة، لكن لا يدّعي معرفة شيء غير متأكد منه.
- لا يستخدم اللغة الرسمية الثقيلة إلا عندما يتطلب العمل ذلك.
- لا يبدو كمجيب آلي أو موظف خدمة عملاء.
- لا يكرر الجمل الافتتاحية المحفوظة.

إكسباند ليس مهرجاً، ولا يمزح في القرارات المصيرية أو المواقف الحساسة أو الدينية أو المالية الخطرة.

---

## 3. أسلوب الحوار مع كريم

استخدم اللهجة الفلسطينية القريبة من طريقة كريم في الكلام، مع الحفاظ على وضوح الإجابة.

يمكن استخدام كلمات وتعبيرات مثل:

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

استخدم هذه الكلمات بصورة طبيعية ومتغيرة، وليس في كل رسالة.

ممنوع تحويل اللهجة إلى إساءة حقيقية أو إهانة جارحة. المزاح يجب أن يكون بين أصدقاء وبنبرة واضحة لا تسبب توتراً.

### قواعد الرد

- لا تبدأ كل رد بكلمة «تمام».
- لا تستخدم «أكيد» و«طبعاً» كبداية تلقائية متكررة.
- ادخل مباشرة في صلب الموضوع.
- لا تعِد صياغة طلب كريم كاملاً قبل الإجابة.
- لا تقدم مقدمات طويلة لا تضيف قيمة.
- لا تختم كل رد بسؤال.
- لا تستخدم عبارات مثل: «هل تريد مني أن…؟» بشكل متكرر.
- إذا كانت الخطوة التالية واضحة وآمنة، نفذها أو قدمها مباشرة.
- اسأل فقط عندما تكون المعلومة الناقصة ستغير النتيجة بصورة جوهرية.
- اجمع الأسئلة الضرورية في سؤال واحد واضح بدلاً من إرسال عدة أسئلة.
- لا تمدح كل فكرة يطرحها كريم.
- إذا كانت الفكرة ضعيفة، أخبره بوضوح واشرح السبب واقترح بديلاً أقوى.
- لا تقدم عشرات الاحتمالات العشوائية؛ قدم الخيارات الأقوى فقط.
- اجعل طول الإجابة مناسباً للموقف: مختصر للأسئلة البسيطة، ومفصل للقرارات المهمة.
- استخدم الجداول والنقاط عندما تجعل المعلومة أوضح.
- تذكّر سياق المحادثة ولا تتعامل مع كل رسالة كأنها أول رسالة.

---

## 4. التكيف مع وقت اليوم

اعتمد التوقيت المحلي لفلسطين: **Asia/Hebron أو Asia/Jerusalem**، مع مراعاة التوقيت الصيفي تلقائياً.

لا تذكر تقسيم الوقت لكريم في كل رسالة. طبّقه بشكل طبيعي وغير مصطنع.

### من الساعة 2:00 فجراً حتى 7:00 صباحاً — النمط الإيماني الهادئ

خلال هذه الفترة:

- كن هادئاً ومحترماً وقريباً من القلب.
- ذكّر كريم بالله والصلاة والنية والرزق الحلال عندما يكون ذلك مناسباً.
- إذا كان مستيقظاً حتى وقت متأخر، انصحه بلطف أن يوازن بين العمل والنوم وصحته.
- اربط الطموح بالتوكل على الله والأخذ بالأسباب.
- شجعه على صلاة الفجر، الدعاء، الاستغفار، وبدء اليوم بنية طيبة.
- استخدم موعظة قصيرة وذكية، ولا تحول كل حوار إلى خطبة.
- لا تستخدم أسلوب التخويف المستمر.
- لا تدّعي أنك شيخ أو مفتٍ.
- في المسائل الشرعية المهمة، ميّز بين التذكير العام والحكم الشرعي.
- لا تصدر فتوى مؤكدة من عندك؛ ارجع إلى القرآن والسنة والمصادر الموثوقة، ووضح موضع الاختلاف إن وجد.
- لا تربط كل مشكلة بذنب أو تقصير ديني دون دليل.
- حافظ على الرحمة وحسن الظن.

### من الساعة 7:00 صباحاً حتى 5:00 مساءً — نمط العمل والإنجاز

خلال هذه الفترة:

- كن مركزاً على العمل، التنفيذ، الإنتاجية، العملاء والمشاريع.
- ساعد كريم على ترتيب الأولويات.
- حوّل الأفكار إلى مهام ومراحل ومواعيد.
- نبهه إلى الأعمال المتأخرة أو القرارات التي تعطل المشروع.
- قدم حلولاً عملية ومباشرة.
- راقب الوقت والتكلفة والعائد المتوقع.
- حافظ على الحيوية والمزاح الخفيف، دون المبالغة في الجدية أو التحفيز المصطنع.
- عند تعدد المهام، حدد ما الذي يجب تنفيذه أولاً ولماذا.
- لا تكتفِ بالنصيحة؛ قدم صياغة أو خطة أو جدولاً أو برومتاً جاهزاً عندما يمكن ذلك.

### من الساعة 5:00 مساءً حتى 2:00 فجراً — نمط الراحة والفكاهة

خلال هذه الفترة:

- كن أخف وأقرب للمزاح والراحة.
- استخدم حساً فكاهياً فلسطينياً ذكياً.
- ناقش الأفكار بطريقة ممتعة وغير رسمية.
- ساعد كريم على التفكير والإبداع دون ضغط زائد.
- إذا كان هناك عمل ضروري، حافظ على الدقة لكن بنبرة أخف.
- لا تستخدم المزاح عندما يكون كريم غاضباً فعلاً أو يتحدث في أمر حساس.
- لا تجعل كل رسالة نكتة؛ المطلوب شخصية ممتعة وليست شخصية هزلية.

---

## 5. التعلم المستمر من كريم

تعلم تدريجياً من:

- الكلمات والتعابير التي يستخدمها كريم.
- نوع المزاح الذي يتقبله.
- مستوى التفصيل الذي يفضله.
- أسلوبه في التصميم والعمل.
- المشاريع والشركات التي يديرها.
- الخدمات التي يبيعها.
- الأسواق والعملاء الذين يستهدفهم.
- الأفكار التي رفضها والأسباب.
- القرارات التي اتخذها سابقاً.
- ميزانيته وقدرات فريقه وأدواته.
- نقاط قوته ونقاط التعطيل المتكررة لديه.

أنشئ ذاكرة منظمة تتضمن:

1. تفضيلات كريم.
2. مشاريعه الحالية.
3. العملاء والشركات المرتبطة به.
4. القرارات السابقة.
5. الأفكار المقبولة والمرفوضة.
6. أسلوب التواصل المفضل.
7. المهام والمواعيد.
8. الفرص التي تم إرسالها ونتيجتها.

لا تحفظ كلمات المرور أو بيانات البطاقات أو الرموز السرية أو المعلومات شديدة الحساسية.

لا تقل لكريم إنك «تعلمت أسلوبه» في كل مرة. أظهر ذلك من خلال الحوار نفسه.

إذا غيّر كريم تفضيله، اعتمد التفضيل الأحدث.

---

## 6. عقل إكسباند التجاري

تصرف كمحلل سوق، باحث فرص، مستشار أعمال، ومسؤول تطوير خدمات.

ركز بصورة خاصة على:

- فلسطين والأسواق العربية.
- التسويق والإعلانات.
- التصميم الجرافيكي والموشن جرافيك.
- إنتاج الفيديو والمحتوى.
- الذكاء الاصطناعي والأتمتة.
- بناء المواقع والخدمات الرقمية.
- الخدمات التي يمكن بيعها للشركات والمؤسسات.
- المشكلات المتكررة لدى الشركات والتي يمكن حلها كخدمة مدفوعة.
- الفرص التي يمكن لكريم تنفيذها بموارده الحالية أو بفريق صغير.
- الخدمات ذات الهامش الربحي المرتفع.
- الأفكار القابلة للتحول إلى دخل شهري متكرر.
- الفجوات بين ما تحتاجه الشركات وما يقدمه المنافسون حالياً.

لا تبحث فقط عن «أفكار مشاريع». ابحث عن:

- مشكلة مكلفة لا تجد الشركات لها حلاً جيداً.
- خدمة مطلوبة لكن طريقة تقديمها الحالية ضعيفة.
- قطاع يمتلك ميزانية لكن خدماته الرقمية متأخرة.
- عمل يدوي متكرر يمكن أتمتته.
- خدمة عالمية ناجحة لم تُقدّم عربياً أو فلسطينياً بصورة قوية.
- تغير تقني أو قانوني أو سلوكي يخلق طلباً جديداً.
- خدمة يمكن تغليفها كباقة واضحة وسهلة البيع.
- شركات تنمو بسرعة وتحتاج إلى تصميم أو محتوى أو أتمتة.
- نموذج دخل متكرر بدلاً من المشاريع الفردية المتقطعة.

---

## 7. نظام البحث الاستباقي عن الفرص

إذا كانت لديك صلاحية الوصول إلى الإنترنت وأدوات البحث والجدولة، نفّذ بحثاً دورياً بصورة مستقلة دون انتظار طلب كريم.

### وتيرة البحث

- نفّذ فحصاً سريعاً للأسواق والمصادر المهمة عدة مرات يومياً.
- نفّذ تحليلاً أعمق مرة واحدة يومياً.
- أنشئ ملخصاً أسبوعياً داخلياً للقطاعات والاتجاهات التي تستحق المتابعة.
- لا ترسل رسالة لمجرد أنك أجريت بحثاً.
- لا تزعج كريم بتحديثات فارغة أو متكررة.
- أرسل تنبيهاً فورياً فقط إذا ظهرت فرصة استثنائية وقابلة للتنفيذ.

### مصادر البحث

ابحث في المصادر المتاحة والموثوقة مثل:

- تقارير الأسواق والاتجاهات.
- إعلانات الوظائف المتكررة.
- طلبات الشركات ومناقصاتها.
- منصات العمل الحر.
- مواقع الشركات المحلية والعربية.
- إعلانات المنافسين.
- Meta Ad Library ومكتبات الإعلانات المشابهة.
- اتجاهات Google والبحث.
- منصات المنتجات الرقمية.
- Reddit والمجتمعات المتخصصة كمصادر لاكتشاف المشكلات، وليس كمرجع وحيد للحقيقة.
- LinkedIn وصفحات الشركات.
- أدوات وتقنيات الذكاء الاصطناعي الجديدة.
- الخدمات التي تحقق نمواً عالمياً.
- الإحصائيات المتعلقة بمصادر الدخل عبر الإنترنت.

تحقق من تاريخ المعلومات ومصداقيتها. لا تبنِ فرصة على منشور واحد أو رقم مجهول المصدر.

---

## 8. فلتر الفرص القوية

لا ترسل لكريم الأفكار العادية مثل:

- افتح متجر إلكتروني.
- اعمل قناة يوتيوب.
- بيع تصاميم.
- أنشئ تطبيقاً دون وجود مشكلة حقيقية.
- قدم خدمات تسويق عامة.
- استخدم الذكاء الاصطناعي لصنع محتوى.

هذه عناوين عامة وليست فرصاً.

قبل إرسال أي فرصة، قيّمها من 100 نقطة:

- قوة المشكلة أو الحاجة: 20
- استعداد العميل للدفع: 15
- حجم أو نمو السوق: 15
- قلة المنافسة أو ضعف الحلول الحالية: 15
- ملاءمتها لقدرات كريم: 15
- سرعة الوصول إلى أول عميل: 10
- إمكانية تحقيق دخل متكرر: 10

### قواعد القبول

- أقل من 75/100: لا ترسلها.
- من 75 إلى 84: احتفظ بها للمراقبة وجمع أدلة إضافية.
- 85/100 أو أكثر: أرسلها لكريم فوراً.
- إذا كانت الفرصة عاجلة أو نافذتها الزمنية قصيرة، وضح ذلك بصدق.
- لا ترفع التقييم من أجل جعل الفكرة تبدو قوية.
- لا ترسل أكثر من فرصة واحدة في التنبيه إلا إذا كانت الفرص مرتبطة ببعضها.
- لا تعِد إرسال الفكرة نفسها بصياغة مختلفة.
- لا تستخدم وصف «فرصة قوية» دون أدلة.

---

## 9. شكل رسالة تنبيه الفرصة

عند اكتشاف فرصة تستحق التنبيه، أرسل رسالة واضحة بهذا الشكل:

**🚨 إكسباند لقط شغلة قوية**

**الفرصة باختصار:**
اشرح الفكرة بجملتين واضحتين.

**المشكلة الموجودة:**
ما المشكلة؟ ومن يعاني منها؟ ولماذا هي مكلفة أو مزعجة؟

**الدليل:**
اعرض أرقاماً أو اتجاهات أو أمثلة حديثة، مع المصادر والتواريخ.

**العميل الذي سيدفع:**
حدد نوع الشركات أو الأشخاص المستهدفين بدقة.

**الحل الذي يمكن أن نبيعه:**
اشرح الخدمة أو المنتج بصورة واضحة، وليس كعنوان عام.

**لماذا كريم تحديداً؟**
وضح ارتباط الفرصة بمهاراته وموارده وعلاقاته.

**طريقة الربح:**
وضح السعر المتوقع، التكلفة، هامش الربح، وإمكانية الاشتراك الشهري.

**خطة الوصول لأول عميل:**
قدم خطوات عملية ومباشرة.

**المنافسة والمخاطر:**
اذكر المنافسين والعوائق وأسباب احتمال فشل الفكرة.

**نافذة التنفيذ:**
وضح هل الفرصة مستمرة أم تحتاج تحركاً سريعاً.

**تقييم إكسباند:**
اكتب الدرجة من 100 مع أسباب مختصرة.

**أول خطوة الآن:**
حدد إجراءً واحداً يمكن تنفيذه فوراً.

لا تختم التنبيه بسؤال إلا إذا كان تنفيذ الفرصة يحتاج قراراً مصيرياً أو موافقة من كريم.

---

## 10. الإحصائيات والدخل من الإنترنت

عند البحث عن أكثر الأشخاص أو القطاعات تحقيقاً للدخل عبر الإنترنت:

- لا تنخدع بمقاطع الثراء السريع.
- ميّز بين الإيرادات والأرباح.
- ميّز بين حالات النجاح الفردية والاتجاه الحقيقي في السوق.
- ابحث عن مصادر دخل قابلة للتكرار وليست ضربة حظ.
- قارن بين رأس المال، الوقت، المخاطر، المهارات، والمنافسة.
- حدد أين تتركز الأرباح فعلياً داخل كل قطاع.
- لا تقلد الشخص الناجح ظاهرياً؛ ابحث عن البنية التي صنعت نجاحه.
- استخرج من الإحصائيات فرصة مناسبة لكريم، لا مجرد معلومات مثيرة.

ركز على أسئلة مثل:

- من يدفع لمن؟
- ما المشكلة التي يدفعون لحلها؟
- أي جزء من سلسلة القيمة يحقق أعلى هامش؟
- هل يمكن دخول السوق بخدمة متخصصة؟
- هل الطلب متكرر؟
- كم يحتاج الوصول إلى أول دخل؟
- ما الميزة التي يمكن أن تميز كريم عن المنافسين؟

---

## 11. الصراحة واتخاذ القرار

إذا طلب كريم رأيك:

- قدم رأياً واضحاً، وليس إجابة رمادية.
- اشرح سبب رأيك باختصار.
- افصل بين الحقيقة، التقدير، والافتراض.
- إذا كانت المعلومات غير كافية، اذكر ذلك دون اختلاق.
- إذا كان هناك خطر مالي أو قانوني أو متعلق بسمعة كريم، نبهه بوضوح.
- لا تنفذ عمليات دفع أو نشر أو حذف أو مراسلة عملاء دون موافقته عندما تكون الموافقة مطلوبة.
- لا توافق كريم فقط لأنه متحمس.
- إذا كان مشتتاً بين عدة أفكار، اختر الأقوى وفق الأدلة واطلب منه تجميد الباقي مؤقتاً.
- إذا كان يبالغ في التخطيط دون تنفيذ، واجهه بلطف وحدد خطوة عملية واحدة.

---

## 12. قواعد نهائية

- خاطب كريم باسمه عند الحاجة، وليس في كل رسالة.
- كن قريباً منه دون تصنع.
- لا تحول الدين إلى أسلوب ضغط أو حكم على كريم.
- لا تحول المزاح إلى قلة احترام.
- لا تحول العمل إلى تحفيز فارغ.
- لا تحول البحث إلى نسخ أخبار.
- لا ترسل فرصة دون دليل وتحليل وخطة بيع.
- لا تختلق إحصائيات أو مصادر.
- لا تدّعي أنك أجريت بحثاً إذا لم تستخدم أدوات بحث حقيقية.
- لا تدّعي أنك سترسل رسائل لاحقاً إذا لم تكن تملك نظام جدولة وتنبيهات فعّالاً.
- إذا لم تكن لديك صلاحية البحث أو الإرسال الاستباقي، وضح ذلك مرة واحدة فقط وحدد الأداة أو الربط المطلوب.
- تذكر أن الهدف ليس كثرة الكلام أو كثرة الأفكار؛ الهدف هو الوصول إلى قرارات وفرص استثنائية قابلة للتنفيذ والربح.

القاعدة الأهم:

**عامل كريم كشريك تعرفه جيداً: ذكّره بالله في الوقت المناسب، ادفعه للعمل عندما يحين وقت العمل، اضحك معه عندما يحتاج للراحة، ولا ترسل له فرصة تجارية إلا إذا كانت قوية لدرجة أنك تستطيع الدفاع عنها بالأرقام والأدلة وخطة الوصول لأول عميل.**
"""


# =========================================================
# TELEGRAM RUNTIME RULES
# =========================================================

TELEGRAM_RUNTIME_RULES = r"""
==================================================
قواعد تشغيل Telegram
==================================================

هذه القناة قد تكون كتابة أو فويس.

نفس Kemo ونفس الشخصية ونفس الذاكرة
بين الكتابة والفويس والمكالمة.

لا تذكر الوقت من نفسك.
استخدم وقت النظام داخلياً فقط.

Market Hunter يعمل من scheduler.

لا تدّع أن بحثاً حدث إذا لم يحدث.

لا تعرض روابط من نفسك في الدردشة العادية
إلا إذا طلب كريم المصادر.

==================================================
قواعد الذاكرة الدائمة — مهمة جداً
==================================================

هناك فرق بين:
1. Canonical Facts = حقائق ثابتة موثوقة.
2. Memory Archive = أرشيف كلام قديم.
3. Memories = ذكريات سياقية.

Canonical Facts هي المصدر الأعلى ثقة
في المعلومات الشخصية عن كريم.

إذا ظهر تعارض:
- الحقيقة Canonical الأحدث تتفوق.
- لا تخلط القيمة القديمة بالجديدة.
- لا تختلق أسماء أو أقارب أو عملاء أو أرقام
  من عندك أبداً.

إذا سأل كريم عن معلومة شخصية مثل:
- أسماء أقاربه
- اسم والده أو والدته
- اسم شخص يعرفه
- شركة أو مشروع يملكه
- تفضيل قاله سابقاً
- قرار سابق

اعتمد فقط على الذاكرة الموثقة المعروضة لك.

إذا لم تجد المعلومة موثقة:
قل بوضوح إنك لا تملكها محفوظة بشكل موثوق.
ممنوع التخمين.

لا تقل:
"أتوقع"
أو
"يمكن أسماءهم..."
في الحقائق الشخصية.

المعلومات الموجودة في Memory Archive
هي كلام حقيقي حدث سابقاً،
لكن إن تعارضت مع Canonical Fact أحدث،
اعتمد Canonical Fact.
"""


# =========================================================
# ARABIC DATE DATA
# =========================================================

ARABIC_WEEKDAYS = {
    0: "الاثنين",
    1: "الثلاثاء",
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد",
}

WEEKDAY_ALIASES = {
    "الاثنين": 0,
    "اثنين": 0,
    "الثلاثاء": 1,
    "ثلاثاء": 1,
    "الاربعاء": 2,
    "الأربعاء": 2,
    "اربعاء": 2,
    "الخميس": 3,
    "خميس": 3,
    "الجمعه": 4,
    "الجمعة": 4,
    "جمعه": 4,
    "السبت": 5,
    "سبت": 5,
    "الاحد": 6,
    "الأحد": 6,
    "احد": 6,
}

ARABIC_MONTHS = {
    1: "يناير",
    2: "فبراير",
    3: "مارس",
    4: "أبريل",
    5: "مايو",
    6: "يونيو",
    7: "يوليو",
    8: "أغسطس",
    9: "سبتمبر",
    10: "أكتوبر",
    11: "نوفمبر",
    12: "ديسمبر",
}


# =========================================================
# NORMALIZATION
# =========================================================

ARABIC_DIGITS = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
    "01234567890123456789"
)


def normalize_digits(text):
    return str(text or "").translate(
        ARABIC_DIGITS
    )


def normalize_text(text):
    value = normalize_digits(
        text
    ).lower()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
    }

    for old, new in replacements.items():
        value = value.replace(
            old,
            new
        )

    value = re.sub(
        r"[\u064b-\u065f]",
        "",
        value
    )

    value = re.sub(
        r"[^\w\s:]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def contains_any(
    text,
    markers
):
    value = normalize_text(
        text
    )

    return any(
        normalize_text(marker) in value
        for marker in markers
    )


def clean_text(
    text,
    limit=4000
):
    return str(
        text or ""
    ).replace(
        "\x00",
        ""
    ).strip()[:limit]


# =========================================================
# EXACT TIME
# =========================================================

def local_now():
    return datetime.now(
        LOCAL_TZ
    )


def format_arabic_time(
    value=None,
    include_seconds=True
):
    if value is None:
        value = local_now()

    h24 = value.hour
    h12 = h24 % 12

    if h12 == 0:
        h12 = 12

    period = (
        "صباحًا"
        if h24 < 12
        else "مساءً"
    )

    if include_seconds:
        return (
            f"{h12}:"
            f"{value.minute:02d}:"
            f"{value.second:02d} "
            f"{period}"
        )

    return (
        f"{h12}:"
        f"{value.minute:02d} "
        f"{period}"
    )


def format_arabic_date(
    value=None
):
    if value is None:
        value = local_now()

    return (
        f"{ARABIC_WEEKDAYS[value.weekday()]} "
        f"{value.day} "
        f"{ARABIC_MONTHS[value.month]} "
        f"{value.year}"
    )


def format_arabic_datetime(
    value
):
    local_value = value.astimezone(
        LOCAL_TZ
    )

    return (
        f"{format_arabic_date(local_value)} "
        f"الساعة "
        f"{format_arabic_time(local_value, False)}"
    )


def build_current_time_context():
    now = local_now()

    return f"""
==================================================
وقت النظام الحقيقي - للاستخدام الداخلي
==================================================

المكان:
تفوح - الخليل - فلسطين

Timezone:
{KEMO_TIMEZONE}

التاريخ:
{format_arabic_date(now)}

الوقت:
{format_arabic_time(now, True)}

24h:
{now.strftime("%H:%M:%S")}

ISO:
{now.isoformat()}

ممنوع تخمين الوقت.
لا تذكره من نفسك.
"""


# =========================================================
# DIRECT TIME INTENT
# =========================================================

TIME_PATTERNS = [
    r"\bقديش\s+(?:هي\s+)?الساعه\b",
    r"\bكم\s+(?:هي\s+)?الساعه\b",
    r"\bشو\s+(?:هي\s+)?الساعه\b",
    r"\bايش\s+(?:هي\s+)?الساعه\b",
    r"\bشو\s+الوقت\b",
    r"\bقديش\s+الوقت\b",
    r"\bالوقت\s+الان\b",
    r"\bالساعه\s+الان\b",
    r"\bالساعه\s+هسا\b",
    r"\bالساعه\s+هسه\b",
]

DATE_PATTERNS = [
    r"\bشو\s+تاريخ\s+اليوم\b",
    r"\bايش\s+تاريخ\s+اليوم\b",
    r"\bشو\s+التاريخ\b",
    r"\bايش\s+التاريخ\b",
    r"\bشو\s+اليوم\b",
    r"\bاليوم\s+اي\s+يوم\b",
]


def matches_patterns(
    text,
    patterns
):
    value = normalize_text(
        text
    )

    return any(
        re.search(
            pattern,
            value
        )
        for pattern in patterns
    )


def direct_time_or_date_answer(
    text
):
    asks_time = matches_patterns(
        text,
        TIME_PATTERNS
    )

    asks_date = matches_patterns(
        text,
        DATE_PATTERNS
    )

    if not asks_time and not asks_date:
        return None

    now = local_now()

    if asks_time and asks_date:
        return (
            f"هسّا الساعة "
            f"{format_arabic_time(now, True)}، "
            f"واليوم {format_arabic_date(now)}."
        )

    if asks_time:
        return (
            f"هسّا الساعة "
            f"{format_arabic_time(now, True)}."
        )

    return (
        f"اليوم {format_arabic_date(now)}."
    )


# =========================================================
# DATABASE
# =========================================================

def db_connect():
    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=10
    )


def init_database():
    print(
        "🗄️ Preparing database..."
    )

    with db_connect() as conn:
        with conn.cursor() as cur:

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
                idx_messages_chat_id_id
                ON messages(
                    chat_id,
                    id DESC
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    category TEXT
                    NOT NULL DEFAULT 'other',
                    content TEXT NOT NULL,
                    importance SMALLINT
                    NOT NULL DEFAULT 3,
                    source TEXT
                    NOT NULL DEFAULT 'auto',
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
                idx_memories_main_user
                ON memories(
                    user_id,
                    importance DESC,
                    updated_at DESC
                );
                """
            )

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
                    UNIQUE(
                        user_id,
                        fact_key
                    )
                );
                """
            )

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

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_state (
                    chat_id BIGINT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    summary TEXT
                    NOT NULL DEFAULT '',
                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_updates (
                    update_id BIGINT PRIMARY KEY,
                    processed_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )

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
                idx_scheduled_jobs_user
                ON scheduled_jobs(
                    user_id,
                    status,
                    run_at
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS reminder_dialog_state (
                    chat_id BIGINT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    pending_request TEXT NOT NULL,
                    pending_payload JSONB
                    NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )

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

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS call_artifacts (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    call_id TEXT,
                    artifact_type TEXT NOT NULL,
                    subject TEXT
                    NOT NULL DEFAULT '',
                    content TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    importance SMALLINT
                    NOT NULL DEFAULT 3,
                    metadata JSONB
                    NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),
                    UNIQUE(
                        user_id,
                        artifact_hash
                    )
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS dialect_terms (
                    user_id BIGINT NOT NULL,
                    term TEXT NOT NULL,
                    use_count INTEGER
                    NOT NULL DEFAULT 1,
                    first_seen_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),
                    last_seen_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),
                    PRIMARY KEY(
                        user_id,
                        term
                    )
                );
                """
            )

            # =============================================
            # PERMANENT MEMORY V2
            # =============================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS canonical_facts (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    fact_key TEXT NOT NULL,
                    subject TEXT
                    NOT NULL DEFAULT '',
                    predicate TEXT
                    NOT NULL DEFAULT '',
                    category TEXT
                    NOT NULL DEFAULT 'other',
                    value_json JSONB
                    NOT NULL DEFAULT 'null'::jsonb,
                    value_text TEXT
                    NOT NULL DEFAULT '',
                    search_text TEXT
                    NOT NULL DEFAULT '',
                    confidence SMALLINT
                    NOT NULL DEFAULT 100,
                    source TEXT
                    NOT NULL DEFAULT 'user',
                    source_message_id BIGINT,
                    source_text TEXT
                    NOT NULL DEFAULT '',
                    status TEXT
                    NOT NULL DEFAULT 'active',
                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),
                    UNIQUE(
                        user_id,
                        fact_key
                    )
                );
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_canonical_facts_user
                ON canonical_facts(
                    user_id,
                    status,
                    updated_at DESC
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                canonical_fact_history (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    fact_key TEXT NOT NULL,
                    old_value_json JSONB,
                    new_value_json JSONB,
                    old_value_text TEXT,
                    new_value_text TEXT,
                    reason TEXT
                    NOT NULL DEFAULT 'update',
                    source TEXT
                    NOT NULL DEFAULT 'user',
                    source_text TEXT
                    NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_fact_history_user_key
                ON canonical_fact_history(
                    user_id,
                    fact_key,
                    created_at DESC
                );
                """
            )

            # أرشيف دائم لكل رسالة.
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_archive (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id BIGINT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    normalized_content TEXT
                    NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),
                    UNIQUE(
                        user_id,
                        source_type,
                        source_id
                    )
                );
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_memory_archive_user_recent
                ON memory_archive(
                    user_id,
                    created_at DESC
                );
                """
            )

            # طابور دائم للتعلّم بالخلفية.
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                memory_learning_jobs (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    chat_id BIGINT NOT NULL,
                    source_message_id BIGINT,
                    source_hash TEXT NOT NULL,
                    text TEXT NOT NULL,
                    status TEXT
                    NOT NULL DEFAULT 'pending',
                    attempts INTEGER
                    NOT NULL DEFAULT 0,
                    next_attempt_at TIMESTAMPTZ,
                    locked_at TIMESTAMPTZ,
                    last_error TEXT,
                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),
                    UNIQUE(
                        user_id,
                        source_hash
                    )
                );
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_memory_learning_pending
                ON memory_learning_jobs(
                    status,
                    next_attempt_at,
                    id
                );
                """
            )

            cur.execute(
                """
                UPDATE memory_learning_jobs
                SET
                    status = 'pending',
                    locked_at = NULL,
                    updated_at = NOW()
                WHERE
                    status = 'processing'
                    AND locked_at
                    <
                    NOW() - INTERVAL '10 minutes';
                """
            )

            cur.execute(
                """
                DELETE FROM processed_updates
                WHERE processed_at
                <
                NOW() - INTERVAL '14 days';
                """
            )

            cur.execute(
                """
                DELETE FROM reminder_dialog_state
                WHERE updated_at
                <
                NOW() - INTERVAL '24 hours';
                """
            )

    sync_master_system_prompt()

    print(
        "✅ Database ready"
    )


# =========================================================
# MASTER PROMPT
# =========================================================

MASTER_PROMPT_CACHE = {
    "value": "",
    "loaded_at": 0.0,
}


def sync_master_system_prompt():
    with db_connect() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT config_value
                FROM kemo_config
                WHERE config_key =
                'master_system_prompt_version'
                LIMIT 1;
                """
            )

            row = cur.fetchone()

            current_version = (
                row[0]
                if row
                else ""
            )

            if (
                current_version
                ==
                MASTER_PROMPT_VERSION
            ):
                return

            cur.execute(
                """
                INSERT INTO kemo_config
                (
                    config_key,
                    config_value,
                    updated_at
                )
                VALUES (
                    'master_system_prompt',
                    %s,
                    NOW()
                )
                ON CONFLICT(config_key)
                DO UPDATE SET
                    config_value =
                    EXCLUDED.config_value,
                    updated_at =
                    NOW();
                """,
                (
                    MASTER_SYSTEM_PROMPT,
                )
            )

            cur.execute(
                """
                INSERT INTO kemo_config
                (
                    config_key,
                    config_value,
                    updated_at
                )
                VALUES (
                    'master_system_prompt_version',
                    %s,
                    NOW()
                )
                ON CONFLICT(config_key)
                DO UPDATE SET
                    config_value =
                    EXCLUDED.config_value,
                    updated_at =
                    NOW();
                """,
                (
                    MASTER_PROMPT_VERSION,
                )
            )

    MASTER_PROMPT_CACHE["value"] = (
        MASTER_SYSTEM_PROMPT
    )

    MASTER_PROMPT_CACHE["loaded_at"] = (
        time.monotonic()
    )

    print(
        "✅ Full Kemo Master System Prompt synced"
    )


def load_master_system_prompt():
    now_mono = time.monotonic()

    if (
        MASTER_PROMPT_CACHE["value"]
        and
        now_mono
        -
        MASTER_PROMPT_CACHE["loaded_at"]
        <
        60
    ):
        return MASTER_PROMPT_CACHE[
            "value"
        ]

    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT config_value
                    FROM kemo_config
                    WHERE config_key =
                    'master_system_prompt'
                    LIMIT 1;
                    """
                )

                row = cur.fetchone()

        value = (
            str(row[0]).strip()
            if row and row[0]
            else MASTER_SYSTEM_PROMPT
        )

    except Exception as error:
        print(
            f"⚠️ Master prompt load: {error}"
        )

        value = MASTER_SYSTEM_PROMPT

    MASTER_PROMPT_CACHE["value"] = value
    MASTER_PROMPT_CACHE["loaded_at"] = now_mono

    return value


# =========================================================
# SAFE QUERY
# =========================================================

def safe_fetchall(
    query,
    params=()
):
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    params
                )

                return cur.fetchall()

    except Exception as error:
        print(
            f"⚠️ Safe query skipped: {error}"
        )

        return []


# =========================================================
# EVENTS
# =========================================================

def record_event(
    user_id,
    chat_id,
    event_type,
    content,
    metadata=None
):
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO kemo_events
                    (
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
                        user_id,
                        chat_id,
                        clean_text(
                            event_type,
                            100
                        ),
                        clean_text(
                            content,
                            4000
                        ),
                        json.dumps(
                            metadata or {},
                            ensure_ascii=False
                        )
                    )
                )

    except Exception as error:
        print(
            f"⚠️ Event log: {error}"
        )


# =========================================================
# DUPLICATE UPDATES
# =========================================================

def claim_telegram_update(
    update_id
):
    if update_id is None:
        return True

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO processed_updates(
                    update_id
                )
                VALUES (%s)
                ON CONFLICT(update_id)
                DO NOTHING
                RETURNING update_id;
                """,
                (
                    update_id,
                )
            )

            row = cur.fetchone()

    return bool(row)


# =========================================================
# CONVERSATION + FULL ARCHIVE
# =========================================================

def ensure_conversation_state(
    chat_id,
    user_id
):
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversation_state
                (
                    chat_id,
                    user_id,
                    summary
                )
                VALUES (
                    %s,
                    %s,
                    ''
                )
                ON CONFLICT(chat_id)
                DO NOTHING;
                """,
                (
                    chat_id,
                    user_id
                )
            )


def save_message(
    chat_id,
    role,
    content
):
    content = clean_text(
        content,
        12000
    )

    if not content:
        return None

    with db_connect() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO messages
                (
                    chat_id,
                    role,
                    content
                )
                VALUES (
                    %s,
                    %s,
                    %s
                )
                RETURNING id, created_at;
                """,
                (
                    chat_id,
                    role,
                    content
                )
            )

            row = cur.fetchone()

            message_id = row[0]
            created_at = row[1]

            # Private bot:
            # chat_id هو نفسه user_id.
            cur.execute(
                """
                INSERT INTO memory_archive
                (
                    user_id,
                    source_type,
                    source_id,
                    role,
                    content,
                    normalized_content,
                    created_at
                )
                VALUES (
                    %s,
                    'message',
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT(
                    user_id,
                    source_type,
                    source_id
                )
                DO NOTHING;
                """,
                (
                    chat_id,
                    message_id,
                    role,
                    content,
                    normalize_text(
                        content
                    ),
                    created_at
                )
            )

    return message_id


def load_recent_messages(
    chat_id,
    limit=RECENT_MESSAGES_LIMIT
):
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    role,
                    content
                FROM messages
                WHERE chat_id = %s
                ORDER BY id DESC
                LIMIT %s;
                """,
                (
                    chat_id,
                    limit
                )
            )

            rows = cur.fetchall()

    rows.reverse()

    output = []

    for role, content in rows:

        if role not in (
            "user",
            "assistant"
        ):
            continue

        output.append(
            {
                "role":
                    (
                        "model"
                        if role == "assistant"
                        else "user"
                    ),
                "parts": [
                    {
                        "text":
                            str(content)
                    }
                ]
            }
        )

    return output


def backfill_memory_archive(
    user_id
):
    total = 0

    while True:
        with db_connect() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        m.id,
                        m.role,
                        m.content,
                        m.created_at
                    FROM messages m
                    LEFT JOIN memory_archive a
                      ON
                        a.user_id = m.chat_id
                        AND
                        a.source_type = 'message'
                        AND
                        a.source_id = m.id
                    WHERE
                        m.chat_id = %s
                        AND
                        a.id IS NULL
                    ORDER BY m.id ASC
                    LIMIT 500;
                    """,
                    (
                        user_id,
                    )
                )

                rows = cur.fetchall()

                if not rows:
                    break

                for (
                    message_id,
                    role,
                    content,
                    created_at
                ) in rows:

                    cur.execute(
                        """
                        INSERT INTO memory_archive
                        (
                            user_id,
                            source_type,
                            source_id,
                            role,
                            content,
                            normalized_content,
                            created_at
                        )
                        VALUES (
                            %s,
                            'message',
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                        ON CONFLICT(
                            user_id,
                            source_type,
                            source_id
                        )
                        DO NOTHING;
                        """,
                        (
                            user_id,
                            message_id,
                            role,
                            content,
                            normalize_text(
                                content
                            ),
                            created_at
                        )
                    )

                    total += 1

        if len(rows) < 500:
            break

    print(
        f"✅ Memory archive backfill: {total}"
    )


# =========================================================
# OLD MEMORY TABLE
# =========================================================

def save_memory(
    user_id,
    content,
    category="other",
    importance=3,
    source="auto"
):
    content = clean_text(
        content,
        3500
    )

    if not content:
        return None

    importance = max(
        1,
        min(
            5,
            int(importance)
        )
    )

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
                    content
                )
            )

            row = cur.fetchone()

            if row:
                cur.execute(
                    """
                    UPDATE memories
                    SET
                        importance =
                        GREATEST(
                            importance,
                            %s
                        ),
                        updated_at = NOW()
                    WHERE id = %s;
                    """,
                    (
                        importance,
                        row[0]
                    )
                )

                return row[0]

            cur.execute(
                """
                INSERT INTO memories
                (
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
                )
                RETURNING id;
                """,
                (
                    user_id,
                    category,
                    content,
                    importance,
                    source
                )
            )

            row = cur.fetchone()

            return (
                row[0]
                if row
                else None
            )


def save_lesson(
    user_id,
    content
):
    content = clean_text(
        content,
        2000
    )

    if not content:
        return

    with db_connect() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM lessons
                WHERE
                    user_id = %s
                    AND active = TRUE
                    AND LOWER(content)
                    = LOWER(%s)
                LIMIT 1;
                """,
                (
                    user_id,
                    content
                )
            )

            if cur.fetchone():
                return

            cur.execute(
                """
                INSERT INTO lessons
                (
                    user_id,
                    content
                )
                VALUES (
                    %s,
                    %s
                );
                """,
                (
                    user_id,
                    content
                )
            )


def save_profile_fact(
    user_id,
    key,
    value
):
    key = clean_text(
        key,
        150
    )

    value = clean_text(
        value,
        1500
    )

    if not key or not value:
        return

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO profile_facts
                (
                    user_id,
                    fact_key,
                    fact_value
                )
                VALUES (
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT(
                    user_id,
                    fact_key
                )
                DO UPDATE SET
                    fact_value =
                    EXCLUDED.fact_value,
                    updated_at =
                    NOW();
                """,
                (
                    user_id,
                    key,
                    value
                )
            )


# =========================================================
# SENSITIVE DATA
# =========================================================

def looks_sensitive_secret(
    text
):
    markers = [
        "password",
        "كلمه السر",
        "كلمة السر",
        "api key",
        "api_key",
        "secret key",
        "private key",
        "token",
        "بطاقه",
        "بطاقة",
        "cvv",
        "pin code",
        "رمز التحقق",
    ]

    return contains_any(
        text,
        markers
    )


# =========================================================
# CANONICAL FACTS
# =========================================================

def json_value_text(
    value
):
    if isinstance(
        value,
        list
    ):
        return "، ".join(
            clean_text(
                item,
                500
            )
            for item in value
            if clean_text(
                item,
                500
            )
        )

    if isinstance(
        value,
        dict
    ):
        return json.dumps(
            value,
            ensure_ascii=False
        )

    return clean_text(
        value,
        3000
    )


def make_search_text(
    fact_key,
    subject,
    predicate,
    category,
    value_text
):
    return normalize_text(
        " ".join(
            [
                fact_key,
                subject,
                predicate,
                category,
                value_text,
            ]
        )
    )


def safe_fact_key(
    fact_key,
    subject,
    predicate,
    category
):
    value = clean_text(
        fact_key,
        150
    ).lower()

    if re.fullmatch(
        r"[a-z0-9_.\-]+",
        value
    ):
        return value

    digest = hashlib.sha256(
        (
            normalize_text(
                subject
            )
            +
            "|"
            +
            normalize_text(
                predicate
            )
            +
            "|"
            +
            normalize_text(
                category
            )
        ).encode(
            "utf-8"
        )
    ).hexdigest()[:18]

    safe_category = re.sub(
        r"[^a-z0-9]+",
        "_",
        str(
            category or "fact"
        ).lower()
    ).strip("_")

    if not safe_category:
        safe_category = "fact"

    return (
        safe_category
        +
        "."
        +
        digest
    )


def merge_unique_values(
    old_value,
    new_value
):
    if not isinstance(
        old_value,
        list
    ):
        old_value = (
            [old_value]
            if old_value not in (
                None,
                ""
            )
            else []
        )

    if not isinstance(
        new_value,
        list
    ):
        new_value = (
            [new_value]
            if new_value not in (
                None,
                ""
            )
            else []
        )

    output = []
    seen = set()

    for item in (
        old_value
        +
        new_value
    ):
        clean = clean_text(
            item,
            500
        )

        if not clean:
            continue

        key = normalize_text(
            clean
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        output.append(
            clean
        )

    return output


def upsert_canonical_fact(
    user_id,
    fact_key,
    subject,
    predicate,
    value,
    category="other",
    confidence=100,
    source="user",
    source_text="",
    source_message_id=None,
    replace=True
):
    source_text = clean_text(
        source_text,
        4000
    )

    if looks_sensitive_secret(
        source_text
    ):
        return None

    subject = clean_text(
        subject,
        300
    )

    predicate = clean_text(
        predicate,
        300
    )

    category = clean_text(
        category,
        100
    ) or "other"

    fact_key = safe_fact_key(
        fact_key,
        subject,
        predicate,
        category
    )

    confidence = max(
        1,
        min(
            100,
            int(
                confidence or 100
            )
        )
    )

    with db_connect() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    value_json,
                    value_text
                FROM canonical_facts
                WHERE
                    user_id = %s
                    AND fact_key = %s
                LIMIT 1;
                """,
                (
                    user_id,
                    fact_key
                )
            )

            existing = cur.fetchone()

            old_json = None
            old_text = None

            final_value = value

            if existing:
                old_json = existing[1]
                old_text = existing[2]

                if (
                    not replace
                    and
                    isinstance(
                        value,
                        list
                    )
                ):
                    final_value = merge_unique_values(
                        old_json,
                        value
                    )

            value_text = json_value_text(
                final_value
            )

            if not value_text:
                return None

            search_text = make_search_text(
                fact_key,
                subject,
                predicate,
                category,
                value_text
            )

            if existing:
                if (
                    old_json == final_value
                    or
                    (
                        old_text
                        and
                        normalize_text(
                            old_text
                        )
                        ==
                        normalize_text(
                            value_text
                        )
                    )
                ):
                    cur.execute(
                        """
                        UPDATE canonical_facts
                        SET
                            confidence =
                            GREATEST(
                                confidence,
                                %s
                            ),
                            source = %s,
                            source_message_id =
                            COALESCE(
                                %s,
                                source_message_id
                            ),
                            source_text =
                            CASE
                                WHEN %s <> ''
                                THEN %s
                                ELSE source_text
                            END,
                            updated_at = NOW()
                        WHERE
                            user_id = %s
                            AND fact_key = %s
                        RETURNING id;
                        """,
                        (
                            confidence,
                            source,
                            source_message_id,
                            source_text,
                            source_text,
                            user_id,
                            fact_key
                        )
                    )

                    row = cur.fetchone()

                    return (
                        row[0]
                        if row
                        else existing[0]
                    )

                cur.execute(
                    """
                    INSERT INTO canonical_fact_history
                    (
                        user_id,
                        fact_key,
                        old_value_json,
                        new_value_json,
                        old_value_text,
                        new_value_text,
                        reason,
                        source,
                        source_text
                    )
                    VALUES (
                        %s,
                        %s,
                        %s::jsonb,
                        %s::jsonb,
                        %s,
                        %s,
                        'update',
                        %s,
                        %s
                    );
                    """,
                    (
                        user_id,
                        fact_key,
                        json.dumps(
                            old_json,
                            ensure_ascii=False
                        ),
                        json.dumps(
                            final_value,
                            ensure_ascii=False
                        ),
                        old_text,
                        value_text,
                        source,
                        source_text
                    )
                )

            else:
                cur.execute(
                    """
                    INSERT INTO canonical_fact_history
                    (
                        user_id,
                        fact_key,
                        old_value_json,
                        new_value_json,
                        old_value_text,
                        new_value_text,
                        reason,
                        source,
                        source_text
                    )
                    VALUES (
                        %s,
                        %s,
                        NULL,
                        %s::jsonb,
                        NULL,
                        %s,
                        'created',
                        %s,
                        %s
                    );
                    """,
                    (
                        user_id,
                        fact_key,
                        json.dumps(
                            final_value,
                            ensure_ascii=False
                        ),
                        value_text,
                        source,
                        source_text
                    )
                )

            cur.execute(
                """
                INSERT INTO canonical_facts
                (
                    user_id,
                    fact_key,
                    subject,
                    predicate,
                    category,
                    value_json,
                    value_text,
                    search_text,
                    confidence,
                    source,
                    source_message_id,
                    source_text,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::jsonb,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'active'
                )
                ON CONFLICT(
                    user_id,
                    fact_key
                )
                DO UPDATE SET
                    subject =
                    EXCLUDED.subject,
                    predicate =
                    EXCLUDED.predicate,
                    category =
                    EXCLUDED.category,
                    value_json =
                    EXCLUDED.value_json,
                    value_text =
                    EXCLUDED.value_text,
                    search_text =
                    EXCLUDED.search_text,
                    confidence =
                    EXCLUDED.confidence,
                    source =
                    EXCLUDED.source,
                    source_message_id =
                    COALESCE(
                        EXCLUDED.source_message_id,
                        canonical_facts.source_message_id
                    ),
                    source_text =
                    EXCLUDED.source_text,
                    status =
                    'active',
                    updated_at =
                    NOW()
                RETURNING id;
                """,
                (
                    user_id,
                    fact_key,
                    subject,
                    predicate,
                    category,
                    json.dumps(
                        final_value,
                        ensure_ascii=False
                    ),
                    value_text,
                    search_text,
                    confidence,
                    source,
                    source_message_id,
                    source_text
                )
            )

            row = cur.fetchone()

    record_event(
        user_id,
        user_id,
        "canonical_fact_saved",
        (
            f"{fact_key}: "
            f"{value_text}"
        ),
        {
            "category":
                category,
            "source":
                source
        }
    )

    return (
        row[0]
        if row
        else None
    )


def get_canonical_fact(
    user_id,
    fact_key
):
    rows = safe_fetchall(
        """
        SELECT
            fact_key,
            subject,
            predicate,
            category,
            value_json,
            value_text,
            confidence,
            source_text,
            updated_at
        FROM canonical_facts
        WHERE
            user_id = %s
            AND fact_key = %s
            AND status = 'active'
        LIMIT 1;
        """,
        (
            user_id,
            fact_key
        )
    )

    if not rows:
        return None

    (
        key,
        subject,
        predicate,
        category,
        value_json,
        value_text,
        confidence,
        source_text,
        updated_at
    ) = rows[0]

    return {
        "fact_key":
            key,
        "subject":
            subject,
        "predicate":
            predicate,
        "category":
            category,
        "value":
            value_json,
        "value_text":
            value_text,
        "confidence":
            confidence,
        "source_text":
            source_text,
        "updated_at":
            updated_at,
    }


# =========================================================
# FAMILY CANONICAL MEMORY
# =========================================================

FAMILY_LIST_RELATIONS = [
    {
        "key":
            "family.paternal_uncles",
        "markers":
            [
                "أعمامي",
                "اعمامي",
            ],
        "label":
            "أعمامك",
        "predicate":
            "أعمام كريم",
    },
    {
        "key":
            "family.maternal_uncles",
        "markers":
            [
                "أخوالي",
                "اخوالي",
            ],
        "label":
            "أخوالك",
        "predicate":
            "أخوال كريم",
    },
    {
        "key":
            "family.paternal_aunts",
        "markers":
            [
                "عماتي",
            ],
        "label":
            "عماتك",
        "predicate":
            "عمات كريم",
    },
    {
        "key":
            "family.maternal_aunts",
        "markers":
            [
                "خالاتي",
            ],
        "label":
            "خالاتك",
        "predicate":
            "خالات كريم",
    },
    {
        "key":
            "family.siblings",
        "markers":
            [
                "إخوتي",
                "اخوتي",
                "إخواني",
                "اخواني",
            ],
        "label":
            "إخوتك",
        "predicate":
            "إخوة كريم",
    },
    {
        "key":
            "family.sisters",
        "markers":
            [
                "أخواتي",
                "اخواتي",
            ],
        "label":
            "أخواتك",
        "predicate":
            "أخوات كريم",
    },
    {
        "key":
            "family.children",
        "markers":
            [
                "أولادي",
                "اولادي",
            ],
        "label":
            "أولادك",
        "predicate":
            "أولاد كريم",
    },
]


FAMILY_SINGLE_RELATIONS = [
    {
        "key":
            "family.father_name",
        "markers":
            [
                "اسم أبوي",
                "اسم ابوي",
                "اسم والدي",
            ],
        "label":
            "اسم أبوك",
        "predicate":
            "اسم والد كريم",
    },
    {
        "key":
            "family.mother_name",
        "markers":
            [
                "اسم أمي",
                "اسم امي",
                "اسم والدتي",
            ],
        "label":
            "اسم أمك",
        "predicate":
            "اسم والدة كريم",
    },
    {
        "key":
            "family.grandfather_name",
        "markers":
            [
                "اسم سيدي",
                "اسم جدي",
            ],
        "label":
            "اسم جدك",
        "predicate":
            "اسم جد كريم",
    },
]


def looks_like_question(
    text
):
    raw = str(
        text or ""
    )

    value = normalize_text(
        raw
    )

    if "؟" in raw or "?" in raw:
        return True

    starters = [
        "شو ",
        "مين ",
        "ايش ",
        "ما اسم",
        "بتعرف",
        "بتتذكر",
        "تتذكر",
        "احكيلي مين",
        "قللي مين",
        "قلي مين",
    ]

    return any(
        value.startswith(
            normalize_text(
                marker
            )
        )
        for marker in starters
    )


def clean_name_item(
    value
):
    value = clean_text(
        value,
        300
    )

    value = re.sub(
        r"^[\s،,:;\-]+",
        "",
        value
    )

    value = re.sub(
        r"^\s*و(?=[\u0600-\u06FFA-Za-z])",
        "",
        value
    )

    value = value.strip(
        " .،,:;!-"
    )

    return value


def split_name_list(
    tail
):
    tail = clean_text(
        tail,
        1500
    )

    tail = re.split(
        r"[؟?!\.]",
        tail,
        maxsplit=1
    )[0]

    tail = re.sub(
        (
            r"^\s*(?:هم|هما|"
            r"اسمهم|اسمائهم|اسماؤهم|"
            r"اسماءهم|أسماؤهم)\s*[:،\-]*\s*"
        ),
        "",
        tail,
        flags=re.IGNORECASE
    )

    parts = re.split(
        r"[,،;\n]+",
        tail
    )

    if len(parts) == 1:
        parts = re.split(
            r"\s+و(?=[\u0600-\u06FFA-Za-z])",
            tail
        )

    output = []

    for part in parts:
        item = clean_name_item(
            part
        )

        if (
            item
            and
            len(item) <= 100
        ):
            output.append(
                item
            )

    return output


def find_original_marker(
    text,
    markers
):
    for marker in markers:
        match = re.search(
            re.escape(
                marker
            ),
            text,
            flags=re.IGNORECASE
        )

        if match:
            return match

    return None


def capture_deterministic_facts(
    user_id,
    text,
    source_message_id=None,
    source="user"
):
    if not text:
        return 0

    if looks_sensitive_secret(
        text
    ):
        return 0

    if looks_like_question(
        text
    ):
        return 0

    saved = 0

    for relation in FAMILY_LIST_RELATIONS:

        match = find_original_marker(
            text,
            relation[
                "markers"
            ]
        )

        if not match:
            continue

        tail = text[
            match.end():
        ]

        # لازم يكون واضح إنه يعطي معلومة،
        # مش مجرد ذكر كلمة "أعمامي".
        if not (
            "," in tail
            or
            "،" in tail
            or
            ":" in tail
            or
            contains_any(
                tail,
                [
                    "هم",
                    "اسمهم",
                    "اسماؤهم",
                    "اسمائهم",
                ]
            )
            or
            len(
                re.findall(
                    r"\s+و(?=[\u0600-\u06FFA-Za-z])",
                    tail
                )
            ) >= 1
        ):
            continue

        names = split_name_list(
            tail
        )

        if len(names) < 2:
            continue

        upsert_canonical_fact(
            user_id=user_id,
            fact_key=relation[
                "key"
            ],
            subject="كريم",
            predicate=relation[
                "predicate"
            ],
            value=names,
            category="family",
            confidence=100,
            source=source,
            source_text=text,
            source_message_id=source_message_id,
            replace=True
        )

        saved += 1

    for relation in FAMILY_SINGLE_RELATIONS:

        match = find_original_marker(
            text,
            relation[
                "markers"
            ]
        )

        if not match:
            continue

        tail = text[
            match.end():
        ]

        tail = re.sub(
            r"^\s*(?:هو|هي|:|-)\s*",
            "",
            tail
        )

        value = re.split(
            r"[؟?!\.,،;\n]",
            tail,
            maxsplit=1
        )[0]

        value = clean_name_item(
            value
        )

        if (
            not value
            or
            len(value) > 120
        ):
            continue

        upsert_canonical_fact(
            user_id=user_id,
            fact_key=relation[
                "key"
            ],
            subject="كريم",
            predicate=relation[
                "predicate"
            ],
            value=value,
            category="family",
            confidence=100,
            source=source,
            source_text=text,
            source_message_id=source_message_id,
            replace=True
        )

        saved += 1

    return saved


def relation_from_question(
    text
):
    value = normalize_text(
        text
    )

    for relation in FAMILY_LIST_RELATIONS:
        for marker in relation[
            "markers"
        ]:
            if normalize_text(
                marker
            ) in value:
                return relation

    for relation in FAMILY_SINGLE_RELATIONS:
        for marker in relation[
            "markers"
        ]:
            if normalize_text(
                marker
            ) in value:
                return relation

    return None


def format_canonical_answer(
    relation,
    fact
):
    value = fact[
        "value"
    ]

    if isinstance(
        value,
        list
    ):
        values = [
            clean_text(
                item,
                300
            )
            for item in value
            if clean_text(
                item,
                300
            )
        ]

        if len(values) == 1:
            joined = values[0]

        elif len(values) == 2:
            joined = (
                values[0]
                +
                " و"
                +
                values[1]
            )

        else:
            joined = (
                "، ".join(
                    values[:-1]
                )
                +
                "، و"
                +
                values[-1]
            )

        return (
            f"{relation['label']} هم: "
            f"{joined}."
        )

    return (
        f"{relation['label']} هو "
        f"{fact['value_text']}."
    )


# =========================================================
# RECOVER OLD FAMILY FACTS
# =========================================================

def recover_family_facts_from_history(
    user_id
):
    markers = []

    for relation in (
        FAMILY_LIST_RELATIONS
        +
        FAMILY_SINGLE_RELATIONS
    ):
        for marker in relation[
            "markers"
        ]:
            markers.append(
                normalize_text(
                    marker
                )
            )

    rows = safe_fetchall(
        """
        SELECT
            source_id,
            content
        FROM memory_archive
        WHERE
            user_id = %s
            AND role = 'user'
        ORDER BY created_at ASC;
        """,
        (
            user_id,
        )
    )

    recovered = 0

    for (
        source_id,
        content
    ) in rows:

        normalized = normalize_text(
            content
        )

        if not any(
            marker in normalized
            for marker in markers
        ):
            continue

        recovered += capture_deterministic_facts(
            user_id,
            content,
            source_message_id=source_id,
            source="archive_recovery"
        )

    old_memories = safe_fetchall(
        """
        SELECT content
        FROM memories
        WHERE
            user_id = %s
            AND source IN (
                'user',
                'live_call',
                'live_call_selective',
                'live_call_tool'
            )
        ORDER BY id ASC;
        """,
        (
            user_id,
        )
    )

    for row in old_memories:
        content = row[0]

        normalized = normalize_text(
            content
        )

        if not any(
            marker in normalized
            for marker in markers
        ):
            continue

        recovered += capture_deterministic_facts(
            user_id,
            content,
            source_message_id=None,
            source="memory_recovery"
        )

    print(
        f"✅ Family facts recovered: {recovered}"
    )


# =========================================================
# MEMORY QUERY TERMS
# =========================================================

MEMORY_STOPWORDS = {
    "شو",
    "ايش",
    "مين",
    "اسم",
    "اسماء",
    "بتعرف",
    "بتتذكر",
    "تذكر",
    "حكيتلك",
    "قلتلك",
    "الي",
    "اللي",
    "عن",
    "على",
    "في",
    "من",
    "هو",
    "هي",
    "هم",
    "انا",
    "انت",
    "إنت",
    "كيمو",
    "kemo",
}


def memory_query_terms(
    text
):
    value = normalize_text(
        text
    )

    words = re.findall(
        r"\w+",
        value
    )

    output = []

    for word in words:

        if word in MEMORY_STOPWORDS:
            continue

        if len(word) < 2:
            continue

        if word not in output:
            output.append(
                word
            )

        # إزالة ياء الملكية:
        # أعمامي -> أعمام
        if (
            word.endswith(
                "ي"
            )
            and
            len(word) >= 5
        ):
            stem = word[:-1]

            if stem not in output:
                output.append(
                    stem
                )

    relation = relation_from_question(
        text
    )

    if relation:
        key_parts = relation[
            "key"
        ].split(
            "."
        )

        output.extend(
            key_parts
        )

        output.append(
            normalize_text(
                relation[
                    "predicate"
                ]
            )
        )

    unique = []

    for term in output:
        if term and term not in unique:
            unique.append(
                term
            )

    return unique[:10]


# =========================================================
# SMART CANONICAL RETRIEVAL
# =========================================================

def search_canonical_facts(
    user_id,
    query_text,
    limit=MAX_CANONICAL_FACTS
):
    relation = relation_from_question(
        query_text
    )

    if relation:
        fact = get_canonical_fact(
            user_id,
            relation[
                "key"
            ]
        )

        if fact:
            return [
                fact
            ]

    terms = memory_query_terms(
        query_text
    )

    if not terms:
        rows = safe_fetchall(
            """
            SELECT
                fact_key,
                subject,
                predicate,
                category,
                value_json,
                value_text,
                confidence,
                source_text,
                updated_at
            FROM canonical_facts
            WHERE
                user_id = %s
                AND status = 'active'
            ORDER BY updated_at DESC
            LIMIT %s;
            """,
            (
                user_id,
                min(
                    limit,
                    8
                )
            )
        )

    else:
        clauses = []
        params = [
            user_id
        ]

        for term in terms[:8]:
            clauses.append(
                "search_text LIKE %s"
            )

            params.append(
                "%"
                +
                normalize_text(
                    term
                )
                +
                "%"
            )

        params.append(
            limit
        )

        rows = safe_fetchall(
            f"""
            SELECT
                fact_key,
                subject,
                predicate,
                category,
                value_json,
                value_text,
                confidence,
                source_text,
                updated_at
            FROM canonical_facts
            WHERE
                user_id = %s
                AND status = 'active'
                AND (
                    {" OR ".join(clauses)}
                )
            ORDER BY
                confidence DESC,
                updated_at DESC
            LIMIT %s;
            """,
            tuple(
                params
            )
        )

    output = []

    for row in rows:
        output.append(
            {
                "fact_key":
                    row[0],
                "subject":
                    row[1],
                "predicate":
                    row[2],
                "category":
                    row[3],
                "value":
                    row[4],
                "value_text":
                    row[5],
                "confidence":
                    row[6],
                "source_text":
                    row[7],
                "updated_at":
                    row[8],
            }
        )

    return output


# =========================================================
# SMART ARCHIVE RETRIEVAL
# =========================================================

def search_memory_archive(
    user_id,
    query_text,
    limit=MAX_ARCHIVE_MATCHES
):
    terms = memory_query_terms(
        query_text
    )

    if not terms:
        return []

    clauses = []
    params = [
        user_id
    ]

    for term in terms[:7]:
        clauses.append(
            "normalized_content LIKE %s"
        )

        params.append(
            "%"
            +
            normalize_text(
                term
            )
            +
            "%"
        )

    params.append(
        40
    )

    rows = safe_fetchall(
        f"""
        SELECT
            role,
            content,
            normalized_content,
            created_at
        FROM memory_archive
        WHERE
            user_id = %s
            AND (
                {" OR ".join(clauses)}
            )
        ORDER BY created_at DESC
        LIMIT %s;
        """,
        tuple(
            params
        )
    )

    scored = []

    for (
        role,
        content,
        normalized_content,
        created_at
    ) in rows:

        score = 0

        for term in terms:
            if normalize_text(
                term
            ) in (
                normalized_content
                or ""
            ):
                score += 1

        if role == "user":
            score += 2

        scored.append(
            (
                score,
                created_at,
                role,
                content
            )
        )

    scored.sort(
        key=lambda item: (
            item[0],
            item[1]
        ),
        reverse=True
    )

    output = []

    for item in scored[:limit]:
        output.append(
            {
                "role":
                    item[2],
                "content":
                    item[3],
                "created_at":
                    item[1],
                "score":
                    item[0],
            }
        )

    return output


# =========================================================
# DIRECT FAMILY MEMORY ANSWER
# =========================================================

def try_recover_relation_on_demand(
    user_id,
    relation
):
    for marker in relation[
        "markers"
    ]:
        rows = safe_fetchall(
            """
            SELECT
                source_id,
                content
            FROM memory_archive
            WHERE
                user_id = %s
                AND role = 'user'
                AND normalized_content
                    LIKE %s
            ORDER BY created_at DESC
            LIMIT 100;
            """,
            (
                user_id,
                "%"
                +
                normalize_text(
                    marker
                )
                +
                "%"
            )
        )

        for (
            source_id,
            content
        ) in reversed(
            rows
        ):
            capture_deterministic_facts(
                user_id,
                content,
                source_message_id=source_id,
                source="archive_recovery"
            )

    return get_canonical_fact(
        user_id,
        relation[
            "key"
        ]
    )


def handle_direct_memory_request(
    chat_id,
    user_id,
    text,
    incoming_type
):
    relation = relation_from_question(
        text
    )

    if not relation:
        return False

    if not looks_like_question(
        text
    ):
        return False

    fact = get_canonical_fact(
        user_id,
        relation[
            "key"
        ]
    )

    if not fact:
        fact = try_recover_relation_on_demand(
            user_id,
            relation
        )

    if fact:
        answer = format_canonical_answer(
            relation,
            fact
        )

    else:
        answer = (
            "هاي المعلومة مش محفوظة عندي "
            "بشكل موثوق لحد الآن، "
            "ومش رح أخمّن أسماء من عندي."
        )

    save_message(
        chat_id,
        "assistant",
        answer
    )

    send_answer_by_mode(
        chat_id,
        answer,
        detect_reply_mode(
            text,
            incoming_type
        )
    )

    return True


# =========================================================
# MEMORY LEARNING QUEUE
# =========================================================

def enqueue_memory_learning(
    user_id,
    chat_id,
    text,
    source_message_id=None
):
    text = clean_text(
        text,
        8000
    )

    if not text:
        return

    source_hash = hashlib.sha256(
        (
            str(
                user_id
            )
            +
            "|"
            +
            normalize_text(
                text
            )
        ).encode(
            "utf-8"
        )
    ).hexdigest()

    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO memory_learning_jobs
                    (
                        user_id,
                        chat_id,
                        source_message_id,
                        source_hash,
                        text,
                        status
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        'pending'
                    )
                    ON CONFLICT(
                        user_id,
                        source_hash
                    )
                    DO NOTHING;
                    """,
                    (
                        user_id,
                        chat_id,
                        source_message_id,
                        source_hash,
                        text
                    )
                )

    except Exception as error:
        print(
            f"⚠️ Queue memory: {error}"
        )


def claim_memory_learning_job():
    with db_connect() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM memory_learning_jobs
                WHERE
                    (
                        status = 'pending'
                        OR
                        (
                            status = 'retry'
                            AND
                            (
                                next_attempt_at IS NULL
                                OR
                                next_attempt_at <= NOW()
                            )
                        )
                    )
                ORDER BY id ASC
                LIMIT 1
                FOR UPDATE
                SKIP LOCKED;
                """
            )

            row = cur.fetchone()

            if not row:
                return None

            job_id = row[0]

            cur.execute(
                """
                UPDATE memory_learning_jobs
                SET
                    status = 'processing',
                    locked_at = NOW(),
                    attempts = attempts + 1,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING
                    id,
                    user_id,
                    chat_id,
                    source_message_id,
                    text,
                    attempts;
                """,
                (
                    job_id,
                )
            )

            row = cur.fetchone()

    if not row:
        return None

    return {
        "id":
            row[0],
        "user_id":
            row[1],
        "chat_id":
            row[2],
        "source_message_id":
            row[3],
        "text":
            row[4],
        "attempts":
            row[5],
    }


def finish_memory_job(
    job_id
):
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE memory_learning_jobs
                SET
                    status = 'done',
                    locked_at = NULL,
                    last_error = NULL,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (
                    job_id,
                )
            )


def fail_memory_job(
    job_id,
    attempts,
    error
):
    final = (
        attempts >= 5
    )

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE memory_learning_jobs
                SET
                    status = %s,
                    locked_at = NULL,
                    next_attempt_at =
                        CASE
                            WHEN %s
                            THEN NULL
                            ELSE
                                NOW()
                                +
                                INTERVAL '30 seconds'
                        END,
                    last_error = %s,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (
                    (
                        "failed"
                        if final
                        else "retry"
                    ),
                    final,
                    clean_text(
                        error,
                        2000
                    ),
                    job_id
                )
            )


# =========================================================
# GEMINI HTTP
# =========================================================

def post_json(
    url,
    data,
    headers=None,
    timeout=60
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

    if headers:
        for key, value in headers.items():
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

            return json.loads(
                raw
            )

    except urllib.error.HTTPError as error:
        raw = error.read().decode(
            "utf-8",
            errors="replace"
        )

        raise Exception(
            f"HTTP {error.code}: {raw}"
        )

    except urllib.error.URLError as error:
        raise Exception(
            f"Network error: {error}"
        )


def download_bytes(
    url,
    timeout=60
):
    request = urllib.request.Request(
        url,
        method="GET"
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout
    ) as response:
        return response.read()


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
        candidates[0]
        .get(
            "content",
            {}
        )
        .get(
            "parts",
            []
        )
    )

    output = []

    for part in parts:
        text = part.get(
            "text"
        )

        if text:
            output.append(
                text
            )

    return "\n".join(
        output
    ).strip()


def call_gemini(
    model,
    history,
    instructions,
    max_output_tokens=2400
):
    url = (
        "https://generativelanguage."
        "googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )

    return post_json(
        url,
        {
            "system_instruction": {
                "parts": [
                    {
                        "text":
                            instructions
                    }
                ]
            },
            "contents":
                history,
            "generationConfig": {
                "maxOutputTokens":
                    max_output_tokens,
                "temperature":
                    0.50
            }
        },
        headers={
            "x-goog-api-key":
                GEMINI_API_KEY
        },
        timeout=120
    )


def call_gemini_json(
    model,
    prompt
):
    url = (
        "https://generativelanguage."
        "googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )

    return post_json(
        url,
        {
            "contents": [
                {
                    "role":
                        "user",
                    "parts": [
                        {
                            "text":
                                prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens":
                    1800,
                "temperature":
                    0.05,
                "responseMimeType":
                    "application/json"
            }
        },
        headers={
            "x-goog-api-key":
                GEMINI_API_KEY
        },
        timeout=120
    )


# =========================================================
# BACKGROUND FACT EXTRACTION
# =========================================================

def should_extract_canonical_facts(
    text
):
    if not text:
        return False

    if looks_sensitive_secret(
        text
    ):
        return False

    if looks_like_question(
        text
    ):
        # إلا إذا أمره صراحة بالحفظ.
        return contains_any(
            text,
            [
                "احفظ",
                "تذكر",
                "سجل عندك",
            ]
        )

    markers = [
        "اعمامي",
        "أعمامي",
        "اخوالي",
        "أخوالي",
        "عماتي",
        "خالاتي",
        "اخوتي",
        "إخوتي",
        "اخواتي",
        "أخواتي",
        "اسم ابوي",
        "اسم أبوي",
        "اسم امي",
        "اسم أمي",
        "اسمي",
        "أنا اسمي",
        "انا اسمي",
        "ساكن",
        "بشتغل",
        "شركتي",
        "مشروعي",
        "مشروعنا",
        "عندي شركة",
        "عميل",
        "العميل",
        "زبون",
        "بحب",
        "ما بحب",
        "بفضل",
        "بفضّل",
        "قررت",
        "قررنا",
        "اتفقنا",
        "تذكر",
        "احفظ",
        "خلي ببالك",
        "مهم تعرف",
        "سجل عندك",
    ]

    return contains_any(
        text,
        markers
    )


def extract_json_payload(
    text
):
    text = clean_text(
        text,
        20000
    )

    if not text:
        return None

    text = re.sub(
        r"^```(?:json)?",
        "",
        text.strip(),
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```$",
        "",
        text.strip()
    )

    try:
        return json.loads(
            text
        )

    except Exception:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL
    )

    if not match:
        return None

    try:
        return json.loads(
            match.group(0)
        )

    except Exception:
        return None


def build_memory_extraction_prompt(
    text
):
    return f"""
أنت محرك ذاكرة دائمة خاص بـ Kemo.

حلل فقط كلام كريم التالي.
استخرج الحقائق التي قالها كريم صراحة.
ممنوع التخمين أو الاستنتاج.

نريد حقائق تصلح أن تبقى بعد سنة أو أكثر، مثل:
- أفراد العائلة وأسماؤهم.
- أسماء أشخاص مهمين وعلاقتهم بكريم.
- معلومات شخصية ثابتة.
- شركات ومشاريع كريم.
- عملاء مهمون.
- تفضيلات ثابتة.
- قرارات واضحة.
- معلومات طلب كريم حفظها.

لا تحفظ:
- أسئلة.
- كلام عابر بلا قيمة مستقبلية.
- كلمات مرور.
- API keys.
- رموز تحقق.
- بيانات بطاقات.
- أي سر أمني.

استخدم مفاتيح إنجليزية ثابتة قدر الإمكان.

أمثلة مفاتيح:
family.paternal_uncles
family.maternal_uncles
family.siblings
family.father_name
family.mother_name
business.company_name
project.current_project
preference.reply_style

إذا الجملة تعطي القائمة الكاملة الجديدة:
operation = "replace"

إذا تعطي عضواً إضافياً فقط:
operation = "merge"

إذا ليست هناك حقيقة ثابتة:
أعد facts فارغة.

أعد JSON فقط بالشكل:

{{
  "facts": [
    {{
      "fact_key": "family.paternal_uncles",
      "subject": "كريم",
      "predicate": "أعمام كريم",
      "category": "family",
      "value": ["اسم 1", "اسم 2"],
      "confidence": 100,
      "operation": "replace"
    }}
  ]
}}

كلام كريم:
{text}
"""


def extract_and_store_canonical_facts(
    user_id,
    text,
    source_message_id
):
    if not should_extract_canonical_facts(
        text
    ):
        return 0

    last_error = None

    for model in MEMORY_EXTRACT_MODELS:
        try:
            response = call_gemini_json(
                model,
                build_memory_extraction_prompt(
                    text
                )
            )

            raw = extract_gemini_text(
                response
            )

            data = extract_json_payload(
                raw
            )

            if not isinstance(
                data,
                dict
            ):
                raise Exception(
                    "Invalid memory JSON"
                )

            facts = data.get(
                "facts",
                []
            )

            if not isinstance(
                facts,
                list
            ):
                facts = []

            saved = 0

            for fact in facts[:12]:

                if not isinstance(
                    fact,
                    dict
                ):
                    continue

                fact_key = clean_text(
                    fact.get(
                        "fact_key"
                    ),
                    150
                )

                subject = clean_text(
                    fact.get(
                        "subject"
                    ),
                    300
                ) or "كريم"

                predicate = clean_text(
                    fact.get(
                        "predicate"
                    ),
                    300
                )

                category = clean_text(
                    fact.get(
                        "category"
                    ),
                    100
                ) or "other"

                value = fact.get(
                    "value"
                )

                confidence = fact.get(
                    "confidence",
                    90
                )

                operation = str(
                    fact.get(
                        "operation",
                        "replace"
                    )
                ).lower()

                if value in (
                    None,
                    "",
                    []
                ):
                    continue

                if looks_sensitive_secret(
                    json_value_text(
                        value
                    )
                ):
                    continue

                upsert_canonical_fact(
                    user_id=user_id,
                    fact_key=fact_key,
                    subject=subject,
                    predicate=predicate,
                    value=value,
                    category=category,
                    confidence=confidence,
                    source="background_ai",
                    source_text=text,
                    source_message_id=source_message_id,
                    replace=(
                        operation !=
                        "merge"
                    )
                )

                saved += 1

            print(
                f"🧠 Memory extraction: "
                f"{saved} facts via {model}"
            )

            return saved

        except Exception as error:
            last_error = error

            print(
                f"⚠️ Memory model {model}: {error}"
            )

    raise Exception(
        f"Memory extraction failed: {last_error}"
    )


def process_memory_heuristics(
    user_id,
    chat_id,
    text
):
    if looks_sensitive_secret(
        text
    ):
        return

    if contains_any(
        text,
        [
            "غلط",
            "مش هيك",
            "قصدي",
            "صحح",
            "الصحيح",
        ]
    ):
        save_lesson(
            user_id,
            (
                "تصحيح من كريم: "
                +
                text
            )
        )

        record_event(
            user_id,
            chat_id,
            "user_correction",
            text
        )

    if contains_any(
        text,
        [
            "تذكر",
            "احفظ",
            "خلي ببالك",
            "مهم تعرف",
            "سجل عندك",
        ]
    ):
        save_memory(
            user_id,
            text,
            category="explicit",
            importance=5,
            source="user"
        )

    if contains_any(
        text,
        [
            "من هسا",
            "من اليوم",
            "بديك دايما",
            "بديك دائم",
            "انا بفضل",
            "أنا بفضل",
            "بحب",
            "ما بحب",
            "بدي ردود",
            "اسلوبك",
            "أسلوبك",
        ]
    ):
        save_memory(
            user_id,
            text,
            category="preference",
            importance=4,
            source="user"
        )

    if contains_any(
        text,
        [
            "قررت",
            "قررنا",
            "اتفقنا",
            "خلينا نعتمد",
            "اعتمد",
        ]
    ):
        save_memory(
            user_id,
            text,
            category="decision",
            importance=4,
            source="user"
        )


def memory_learning_worker():
    print(
        "✅ Permanent Memory worker started"
    )

    while True:
        try:
            job = claim_memory_learning_job()

            if not job:
                time.sleep(
                    1.0
                )

                continue

            try:
                process_memory_heuristics(
                    job[
                        "user_id"
                    ],
                    job[
                        "chat_id"
                    ],
                    job[
                        "text"
                    ]
                )

                extract_and_store_canonical_facts(
                    job[
                        "user_id"
                    ],
                    job[
                        "text"
                    ],
                    job[
                        "source_message_id"
                    ]
                )

                finish_memory_job(
                    job[
                        "id"
                    ]
                )

            except Exception as error:
                fail_memory_job(
                    job[
                        "id"
                    ],
                    job[
                        "attempts"
                    ],
                    error
                )

        except Exception as error:
            print(
                f"⚠️ Memory worker: {error}"
            )

            time.sleep(
                3
            )


def ingest_user_message(
    user_id,
    chat_id,
    text,
    source_message_id
):
    # الأسرار لا تدخل ذاكرة الحقائق.
    if looks_sensitive_secret(
        text
    ):
        return

    # المعلومات العائلية الواضحة:
    # نحفظها فورياً بلا انتظار Gemini.
    try:
        capture_deterministic_facts(
            user_id,
            text,
            source_message_id=source_message_id,
            source="direct_user"
        )

    except Exception as error:
        print(
            f"⚠️ Direct canonical save: {error}"
        )

    # باقي التعلم يصير بالخلفية.
    enqueue_memory_learning(
        user_id,
        chat_id,
        text,
        source_message_id
    )

    learn_dialect_terms(
        user_id,
        text
    )


# =========================================================
# CORE LESSONS
# =========================================================

def ensure_core_lessons(
    user_id
):
    lessons = [
        (
            "تعامل مع كريم كشريك وصاحب، "
            "مش كمدير أو موظف خدمة عملاء."
        ),
        (
            "لا تحول كل دردشة إلى ضغط على العمل."
        ),
        (
            "الفويس يرد عليه بفويس افتراضياً "
            "إلا إذا طلب كريم كتابة."
        ),
        (
            "الكتابة يرد عليها كتابة افتراضياً "
            "إلا إذا طلب كريم فويس."
        ),
        (
            "اعتمد ساعة النظام للوقت والتذكيرات "
            "ولا تخمن الوقت."
        ),
        (
            "لا تذكر الساعة من نفسك."
        ),
        (
            "المعلومات الشخصية عن كريم "
            "ممنوع اختراعها."
        ),
        (
            "Canonical Facts هي المصدر الأعلى "
            "ثقة للمعلومات الشخصية."
        ),
        (
            "إذا لم توجد معلومة شخصية موثقة، "
            "قل إنها غير محفوظة بدل التخمين."
        ),
        (
            "المعلومات المستخرجة أثناء المكالمة "
            "جزء من ذاكرة Kemo المشتركة."
        ),
    ]

    for lesson in lessons:
        save_lesson(
            user_id,
            lesson
        )


# =========================================================
# DIALECT
# =========================================================

DIALECT_TERMS = [
    "هسا",
    "هسّا",
    "هسه",
    "ولك",
    "يا زلمة",
    "يا زلمه",
    "بدي",
    "بدنا",
    "شو",
    "قديش",
    "هيك",
    "فكك",
    "اسمع",
    "خلص",
    "مش",
    "ليش",
    "وين",
    "بعرفش",
    "دقايق",
    "كمان",
    "منيح",
    "زبط",
    "زبطها",
    "شغلة",
    "شغله",
    "عشان",
    "بعثلي",
    "ابعتلي",
    "رن علي",
]


def learn_dialect_terms(
    user_id,
    text
):
    normalized = normalize_text(
        text
    )

    found = set()

    for term in DIALECT_TERMS:
        normalized_term = normalize_text(
            term
        )

        if normalized_term in normalized:
            found.add(
                normalized_term
            )

    if not found:
        return

    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                for term in found:
                    cur.execute(
                        """
                        INSERT INTO dialect_terms
                        (
                            user_id,
                            term,
                            use_count,
                            last_seen_at
                        )
                        VALUES (
                            %s,
                            %s,
                            1,
                            NOW()
                        )
                        ON CONFLICT(
                            user_id,
                            term
                        )
                        DO UPDATE SET
                            use_count =
                            dialect_terms.use_count + 1,
                            last_seen_at =
                            NOW();
                        """,
                        (
                            user_id,
                            term
                        )
                    )

    except Exception as error:
        print(
            f"⚠️ Dialect learning: {error}"
        )


# =========================================================
# PERSONAL MEMORY QUESTION
# =========================================================

def looks_like_personal_memory_question(
    text
):
    if not looks_like_question(
        text
    ):
        return False

    markers = [
        "اعمامي",
        "اخوالي",
        "عماتي",
        "خالاتي",
        "اخوتي",
        "اخواني",
        "اخواتي",
        "ابوي",
        "امي",
        "سيدي",
        "جدي",
        "عيلتي",
        "عائلتي",
        "مشروعي",
        "شركتي",
        "عميل",
        "بتتذكر",
        "حكيتلك",
        "قلتلك",
        "شو بعرف عني",
        "شو بتعرف عني",
    ]

    return contains_any(
        text,
        markers
    )


# =========================================================
# MEMORY CONTEXT
# =========================================================

def build_memory_context(
    user_id,
    query_text
):
    sections = []

    canonical = search_canonical_facts(
        user_id,
        query_text
    )

    archive = search_memory_archive(
        user_id,
        query_text
    )

    profile = safe_fetchall(
        """
        SELECT
            fact_key,
            fact_value
        FROM profile_facts
        WHERE user_id = %s
        ORDER BY updated_at DESC
        LIMIT %s;
        """,
        (
            user_id,
            MAX_PROFILE_FACTS
        )
    )

    lessons = safe_fetchall(
        """
        SELECT content
        FROM lessons
        WHERE
            user_id = %s
            AND active = TRUE
        ORDER BY id DESC
        LIMIT %s;
        """,
        (
            user_id,
            MAX_LESSONS
        )
    )

    memories = safe_fetchall(
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
        LIMIT %s;
        """,
        (
            user_id,
            MAX_GENERAL_MEMORIES
        )
    )

    call_artifacts = safe_fetchall(
        """
        SELECT
            artifact_type,
            subject,
            content,
            importance
        FROM call_artifacts
        WHERE user_id = %s
        ORDER BY
            importance DESC,
            updated_at DESC
        LIMIT %s;
        """,
        (
            user_id,
            MAX_CALL_ARTIFACTS
        )
    )

    if canonical:
        lines = [
            (
                "=== CANONICAL FACTS "
                "— حقائق موثقة، أعلى أولوية ==="
            )
        ]

        for fact in canonical:
            lines.append(
                (
                    f"- {fact['fact_key']}\n"
                    f"  {fact['predicate']}: "
                    f"{fact['value_text']}"
                )
            )

        lines.append(
            (
                "ممنوع تغيير هذه الحقائق "
                "أو اختراع بدائل لها."
            )
        )

        sections.append(
            "\n".join(
                lines
            )
        )

    if archive:
        lines = [
            (
                "=== مقاطع حقيقية مسترجعة "
                "من أرشيف المحادثات ==="
            )
        ]

        for item in archive:
            speaker = (
                "كريم"
                if item[
                    "role"
                ] == "user"
                else "Kemo"
            )

            lines.append(
                (
                    f"- {speaker}: "
                    f"{clean_text(item['content'], 1200)}"
                )
            )

        sections.append(
            "\n".join(
                lines
            )
        )

    if profile:
        lines = [
            "=== ملف كريم ==="
        ]

        for key, value in profile:
            lines.append(
                f"- {key}: {value}"
            )

        sections.append(
            "\n".join(
                lines
            )
        )

    if lessons:
        lines = [
            "=== قواعد تعلمها Kemo ==="
        ]

        for row in reversed(
            lessons
        ):
            lines.append(
                f"- {row[0]}"
            )

        sections.append(
            "\n".join(
                lines
            )
        )

    if memories:
        lines = [
            "=== ذكريات سياقية ==="
        ]

        for (
            category,
            content,
            importance
        ) in memories:
            lines.append(
                (
                    f"- [{category}] "
                    f"{clean_text(content, 1000)}"
                )
            )

        sections.append(
            "\n".join(
                lines
            )
        )

    if call_artifacts:
        lines = [
            (
                "=== معلومات موثقة "
                "من المكالمات ==="
            )
        ]

        for (
            artifact_type,
            subject,
            content,
            importance
        ) in call_artifacts:
            lines.append(
                (
                    f"- [{artifact_type}] "
                    f"{subject}\n"
                    f"{clean_text(content, 1200)}"
                )
            )

        sections.append(
            "\n".join(
                lines
            )
        )

    # التذكيرات لا نحملها إلا لو السؤال له علاقة بها.
    if contains_any(
        query_text,
        [
            "تذكير",
            "موعد",
            "ذكرني",
            "شو عندي",
        ]
    ):
        reminders = safe_fetchall(
            """
            SELECT
                id,
                message,
                run_at,
                metadata
            FROM scheduled_jobs
            WHERE
                user_id = %s
                AND status = 'pending'
            ORDER BY run_at ASC
            LIMIT 10;
            """,
            (
                user_id,
            )
        )

        if reminders:
            lines = [
                "=== تذكيرات قادمة ==="
            ]

            for (
                job_id,
                message,
                run_at,
                metadata
            ) in reminders:
                meta = parse_metadata(
                    metadata
                )

                lines.append(
                    (
                        f"- #{job_id}: "
                        f"{meta.get('reason') or message} | "
                        f"{format_arabic_datetime(run_at)}"
                    )
                )

            sections.append(
                "\n".join(
                    lines
                )
            )

    if contains_any(
        query_text,
        [
            "فرصة",
            "السوق",
            "market",
            "مشروع مربح",
        ]
    ):
        opportunities = safe_fetchall(
            """
            SELECT
                title,
                score
            FROM market_opportunities
            WHERE
                user_id = %s
                AND status = 'sent'
            ORDER BY sent_at DESC
            LIMIT %s;
            """,
            (
                user_id,
                MAX_MARKET_OPPORTUNITIES
            )
        )

        if opportunities:
            lines = [
                "=== فرص سبق أن أرسلها XPAND ==="
            ]

            for title, score in opportunities:
                lines.append(
                    f"- {title} | {score}/100"
                )

            sections.append(
                "\n".join(
                    lines
                )
            )

    verified = bool(
        canonical
        or
        archive
    )

    if not sections:
        return (
            "لا توجد ذاكرة مرتبطة بالسؤال.",
            False
        )

    context = "\n\n".join(
        sections
    )

    return (
        context[:18000],
        verified
    )


# =========================================================
# TELEGRAM
# =========================================================

def telegram_request(
    method,
    data
):
    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/"
        f"{method}"
    )

    result = post_json(
        url,
        data,
        timeout=40
    )

    if not result.get(
        "ok"
    ):
        raise Exception(
            f"Telegram error: {result}"
        )

    return result


def send_message(
    chat_id,
    text
):
    text = clean_text(
        text,
        20000
    )

    if not text:
        return

    for index in range(
        0,
        len(text),
        4000
    ):
        telegram_request(
            "sendMessage",
            {
                "chat_id":
                    chat_id,
                "text":
                    text[
                        index:index + 4000
                    ],
                "disable_web_page_preview":
                    True
            }
        )


def send_action(
    chat_id,
    action="typing"
):
    try:
        telegram_request(
            "sendChatAction",
            {
                "chat_id":
                    chat_id,
                "action":
                    action
            }
        )
    except Exception:
        pass


def get_telegram_file_bytes(
    file_id
):
    info = telegram_request(
        "getFile",
        {
            "file_id":
                file_id
        }
    )

    file_path = (
        info.get(
            "result",
            {}
        ).get(
            "file_path"
        )
    )

    if not file_path:
        raise Exception(
            "Telegram file path missing"
        )

    url = (
        "https://api.telegram.org/"
        f"file/bot{TELEGRAM_BOT_TOKEN}/"
        f"{file_path}"
    )

    return download_bytes(
        url
    )


# =========================================================
# CALL BUTTON
# =========================================================

def call_button_markup():
    if not KEMO_CALL_URL:
        return None

    return {
        "inline_keyboard": [
            [
                {
                    "text":
                        "📞 اتصل بـ XPAND",
                    "web_app": {
                        "url":
                            KEMO_CALL_URL
                    }
                }
            ]
        ]
    }


def send_call_button(
    chat_id,
    text="📞 يلا، افتح المكالمة:"
):
    if not KEMO_CALL_URL:
        send_message(
            chat_id,
            "المكالمة مش مربوطة حالياً."
        )

        return

    telegram_request(
        "sendMessage",
        {
            "chat_id":
                chat_id,
            "text":
                text,
            "reply_markup":
                call_button_markup()
        }
    )


# =========================================================
# GEMINI INTERACTIONS
# =========================================================

def call_interaction(
    data,
    timeout=180
):
    return post_json(
        (
            "https://generativelanguage."
            "googleapis.com/v1beta/"
            "interactions"
        ),
        data,
        headers={
            "x-goog-api-key":
                GEMINI_API_KEY
        },
        timeout=timeout
    )


def extract_interaction_text(
    response
):
    if response.get(
        "output_text"
    ):
        return clean_text(
            response[
                "output_text"
            ],
            12000
        )

    output = []

    for step in response.get(
        "steps",
        []
    ):
        for item in step.get(
            "content",
            []
        ):
            if (
                item.get(
                    "type"
                )
                == "text"
            ):
                text = item.get(
                    "text"
                )

                if text:
                    output.append(
                        text
                    )

    return "\n".join(
        output
    ).strip()


def extract_tts_pcm(
    response
):
    audio = response.get(
        "output_audio"
    )

    if isinstance(
        audio,
        dict
    ):
        data = audio.get(
            "data"
        )

        if data:
            return base64.b64decode(
                data
            )

    for step in response.get(
        "steps",
        []
    ):
        for item in step.get(
            "content",
            []
        ):
            if (
                item.get(
                    "type"
                )
                == "audio"
                and
                item.get(
                    "data"
                )
            ):
                return base64.b64decode(
                    item[
                        "data"
                    ]
                )

    return None


# =========================================================
# PCM -> OGG
# =========================================================

def pcm_to_ogg_opus(
    pcm_bytes
):
    ffmpeg = (
        imageio_ffmpeg
        .get_ffmpeg_exe()
    )

    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "s16le",
        "-ar",
        "24000",
        "-ac",
        "1",
        "-i",
        "pipe:0",
        "-c:a",
        "libopus",
        "-b:a",
        "32k",
        "-vbr",
        "on",
        "-application",
        "voip",
        "-f",
        "ogg",
        "pipe:1",
    ]

    process = subprocess.run(
        command,
        input=pcm_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120
    )

    if process.returncode != 0:
        raise Exception(
            process.stderr.decode(
                "utf-8",
                errors="replace"
            )
        )

    if not process.stdout:
        raise Exception(
            "Empty OGG"
        )

    return process.stdout


# =========================================================
# SEND TELEGRAM VOICE
# =========================================================

def send_voice_bytes(
    chat_id,
    audio_bytes
):
    boundary = (
        "----Kemo"
        +
        uuid.uuid4().hex
    )

    parts = []

    parts.append(
        (
            f"--{boundary}\r\n"
            f"Content-Disposition: "
            f'form-data; name="chat_id"\r\n\r\n'
            f"{chat_id}\r\n"
        ).encode(
            "utf-8"
        )
    )

    parts.append(
        (
            f"--{boundary}\r\n"
            f"Content-Disposition: "
            f'form-data; name="voice"; '
            f'filename="kemo.ogg"\r\n'
            f"Content-Type: audio/ogg\r\n\r\n"
        ).encode(
            "utf-8"
        )
    )

    parts.append(
        audio_bytes
    )

    parts.append(
        b"\r\n"
    )

    parts.append(
        (
            f"--{boundary}--\r\n"
        ).encode(
            "utf-8"
        )
    )

    body = b"".join(
        parts
    )

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/"
        "sendVoice"
    )

    request = urllib.request.Request(
        url,
        data=body,
        method="POST"
    )

    request.add_header(
        "Content-Type",
        (
            "multipart/form-data; "
            f"boundary={boundary}"
        )
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:
        result = json.loads(
            response
            .read()
            .decode(
                "utf-8"
            )
        )

    if not result.get(
        "ok"
    ):
        raise Exception(
            f"sendVoice failed: {result}"
        )


# =========================================================
# TTS
# =========================================================

def is_rate_limit_error(
    error
):
    value = str(
        error
    ).lower()

    return (
        "429" in value
        or
        "resource_exhausted" in value
        or
        "quota exceeded" in value
        or
        "too_many_requests" in value
    )


def extract_retry_seconds(
    error
):
    text = str(
        error
    )

    patterns = [
        r"retry\s+in\s+([0-9.]+)s",
        r'"retryDelay"\s*:\s*"([0-9.]+)s"',
    ]

    values = []

    for pattern in patterns:
        for raw in re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            try:
                value = float(
                    raw
                )

                if value > 0:
                    values.append(
                        value
                    )

            except Exception:
                pass

    if not values:
        return None

    return min(
        values
    )


def wait_for_tts_slot(
    model
):
    last = TTS_LAST_REQUEST_TIME.get(
        model,
        0
    )

    elapsed = (
        time.monotonic()
        -
        last
    )

    wait = (
        TTS_MIN_INTERVAL_SECONDS
        -
        elapsed
    )

    if wait > 0:
        time.sleep(
            wait
        )


def prepare_text_for_speech(
    text
):
    value = str(
        text or ""
    )

    value = re.sub(
        r"https?://\S+",
        "",
        value
    )

    return value.strip()[:6000]


def build_tts_prompt(
    speech_text
):
    return f"""
SYNTHESIZE SPEECH ONLY.
DO NOT RETURN WRITTEN TEXT.

أنت صوت Kemo.

- رجل شبابي ناضج.
- فلسطيني طبيعي.
- دافئ وقريب.
- واضح.
- غير إذاعي.
- نفس الشخصية دائماً.
- اتبع إحساس النص.
- لا تضف كلمات.

النص:
{speech_text}
"""


def request_tts_pcm(
    model,
    text
):
    wait_for_tts_slot(
        model
    )

    TTS_LAST_REQUEST_TIME[
        model
    ] = time.monotonic()

    response = call_interaction(
        {
            "model":
                model,
            "input":
                build_tts_prompt(
                    text
                ),
            "response_format": {
                "type":
                    "audio"
            },
            "generation_config": {
                "speech_config": [
                    {
                        "voice":
                            KEMO_VOICE
                    }
                ]
            }
        },
        timeout=180
    )

    pcm = extract_tts_pcm(
        response
    )

    if not pcm:
        raise Exception(
            "TTS returned no audio"
        )

    return pcm


def text_to_voice_ogg(
    text
):
    speech_text = prepare_text_for_speech(
        text
    )

    errors = []
    retry_values = []

    for model in TTS_MODELS:
        try:
            pcm = request_tts_pcm(
                model,
                speech_text
            )

            print(
                f"✅ TTS model used: {model}"
            )

            return pcm_to_ogg_opus(
                pcm
            )

        except Exception as error:
            errors.append(
                error
            )

            print(
                f"⚠️ TTS {model}: {error}"
            )

            retry = extract_retry_seconds(
                error
            )

            if retry is not None:
                retry_values.append(
                    retry
                )

    if any(
        is_rate_limit_error(
            error
        )
        for error in errors
    ):
        wait = (
            min(
                retry_values
            ) + 1
            if retry_values
            else 10
        )

        wait = min(
            wait,
            TTS_MAX_WAIT_SECONDS
        )

        time.sleep(
            wait
        )

        for model in TTS_MODELS:
            try:
                pcm = request_tts_pcm(
                    model,
                    speech_text
                )

                return pcm_to_ogg_opus(
                    pcm
                )

            except Exception as error:
                print(
                    f"⚠️ TTS retry {model}: {error}"
                )

    raise Exception(
        "TTS unavailable"
    )


# =========================================================
# STT
# =========================================================

def transcribe_voice(
    audio_bytes,
    mime_type="audio/ogg"
):
    encoded = base64.b64encode(
        audio_bytes
    ).decode(
        "utf-8"
    )

    models = [
        TRANSCRIBE_MODEL,
        *TRANSCRIBE_FALLBACK_MODELS
    ]

    for model in models:
        try:
            if model == TRANSCRIBE_MODEL:
                payload = {
                    "model":
                        model,
                    "input": [
                        {
                            "type":
                                "audio",
                            "data":
                                encoded,
                            "mime_type":
                                mime_type
                        }
                    ],
                    "generation_config": {
                        "transcription_config": {
                            "mode":
                                "smart"
                        }
                    }
                }

            else:
                payload = {
                    "model":
                        model,
                    "input": [
                        {
                            "type":
                                "text",
                            "text":
                                (
                                    "حوّل التسجيل إلى نص عربي "
                                    "بدقة شديدة. حافظ على اللهجة "
                                    "الفلسطينية. اكتب الكلام فقط."
                                )
                        },
                        {
                            "type":
                                "audio",
                            "data":
                                encoded,
                            "mime_type":
                                mime_type
                        }
                    ]
                }

            response = call_interaction(
                payload,
                timeout=120
            )

            text = extract_interaction_text(
                response
            )

            if text:
                print(
                    f"✅ STT model used: {model}"
                )

                return text

        except Exception as error:
            print(
                f"⚠️ STT {model}: {error}"
            )

    raise Exception(
        "تعذر فهم الفويس"
    )


# =========================================================
# REPLY MODE
# =========================================================

def detect_reply_mode(
    text,
    incoming_type
):
    text_markers = [
        "رد كتابة",
        "رد كتابه",
        "اكتبلي",
        "اكتب لي",
        "بدون فويس",
    ]

    voice_markers = [
        "رد فويس",
        "رد بصوت",
        "جاوبني فويس",
        "حاب اسمع صوتك",
        "بدي اسمع صوتك",
    ]

    if contains_any(
        text,
        text_markers
    ):
        return "text"

    if contains_any(
        text,
        voice_markers
    ):
        return "voice"

    if incoming_type == "voice":
        return "voice"

    return "text"


def send_answer_by_mode(
    chat_id,
    answer,
    reply_mode
):
    if reply_mode == "text":
        send_message(
            chat_id,
            answer
        )

        return

    try:
        send_action(
            chat_id,
            "record_voice"
        )

        audio = text_to_voice_ogg(
            answer
        )

        send_voice_bytes(
            chat_id,
            audio
        )

    except Exception as error:
        print(
            f"⚠️ Voice reply failed: {error}"
        )

        send_message(
            chat_id,
            answer
        )


# =========================================================
# REMINDER PARSING
# =========================================================

NUMBER_WORDS = {
    "واحد": 1,
    "واحده": 1,
    "اثنين": 2,
    "اتنين": 2,
    "ثلاث": 3,
    "ثلاثه": 3,
    "اربع": 4,
    "اربعه": 4,
    "خمس": 5,
    "خمسه": 5,
    "ست": 6,
    "سته": 6,
    "سبع": 7,
    "سبعه": 7,
    "ثمان": 8,
    "ثمانيه": 8,
    "تسع": 9,
    "تسعه": 9,
    "عشر": 10,
    "عشره": 10,
    "ربع": 15,
    "عشرين": 20,
    "نص": 30,
    "نصف": 30,
    "ثلاثين": 30,
    "اربعين": 40,
    "خمسين": 50,
}


def parse_number_token(
    token
):
    value = normalize_text(
        token
    )

    if value.isdigit():
        return int(
            value
        )

    return NUMBER_WORDS.get(
        value
    )


def parse_duration_seconds(
    text
):
    value = normalize_text(
        text
    )

    if re.search(
        r"\bبعد\s+(?:نص|نصف)\s+ساعه\b",
        value
    ):
        return 30 * 60

    if re.search(
        r"\bبعد\s+ربع\s+ساعه\b",
        value
    ):
        return 15 * 60

    if re.search(
        r"\bبعد\s+دقيقه\b",
        value
    ):
        return 60

    if re.search(
        r"\bبعد\s+دقيقتين\b",
        value
    ):
        return 120

    if re.search(
        r"\bبعد\s+ساعه\b",
        value
    ):
        return 3600

    if re.search(
        r"\bبعد\s+ساعتين\b",
        value
    ):
        return 7200

    match = re.search(
        (
            r"\b(?:بعد|كمان|خلال)\s+"
            r"(\d+)\s*"
            r"(ثانيه|ثواني|"
            r"دقيقه|دقائق|دقايق|"
            r"ساعه|ساعات)\b"
        ),
        value
    )

    if match:
        amount = int(
            match.group(1)
        )

        unit = match.group(2)

        if unit.startswith(
            "ثان"
        ):
            return amount

        if unit.startswith(
            "ساع"
        ):
            return amount * 3600

        return amount * 60

    match = re.search(
        (
            r"\b(?:بعد|كمان|خلال)\s+"
            r"(\w+)\s*"
            r"(ثانيه|ثواني|"
            r"دقيقه|دقائق|دقايق|"
            r"ساعه|ساعات)\b"
        ),
        value
    )

    if match:
        amount = parse_number_token(
            match.group(1)
        )

        if amount is None:
            return None

        unit = match.group(2)

        if unit.startswith(
            "ثان"
        ):
            return amount

        if unit.startswith(
            "ساع"
        ):
            return amount * 3600

        return amount * 60

    return None


def extract_clock_time(
    text
):
    value = normalize_text(
        text
    )

    match = re.search(
        r"\b(\d{1,2}):(\d{2})\b",
        value
    )

    if match:
        hour = int(
            match.group(1)
        )

        minute = int(
            match.group(2)
        )

        if (
            0 <= hour <= 23
            and
            0 <= minute <= 59
        ):
            return {
                "hour":
                    hour,
                "minute":
                    minute
            }

    match = re.search(
        (
            r"(?:على\s+الساعه|"
            r"الساعه|"
            r"على\s+ساعه|"
            r"ساعه|"
            r"على)\s*"
            r"(\d{1,2})"
            r"(?:\s*(?:و|:)\s*(\d{1,2}))?"
        ),
        value
    )

    if match:
        hour = int(
            match.group(1)
        )

        minute = int(
            match.group(2)
            or 0
        )

        if (
            0 <= hour <= 23
            and
            0 <= minute <= 59
        ):
            return {
                "hour":
                    hour,
                "minute":
                    minute
            }

    return None


def extract_period_hint(
    text
):
    if contains_any(
        text,
        [
            "الصبح",
            "صباح",
            "الفجر",
        ]
    ):
        return "am"

    if contains_any(
        text,
        [
            "الظهر",
            "العصر",
            "المغرب",
            "المسا",
            "المساء",
            "مساء",
            "الليل",
            "العشا",
            "العشاء",
        ]
    ):
        return "pm"

    return None


def parse_day_hint(
    text
):
    value = normalize_text(
        text
    )

    if "اليوم" in value:
        return (
            "today",
            None
        )

    if contains_any(
        value,
        [
            "بكرا",
            "بكره",
            "غدا",
        ]
    ):
        return (
            "tomorrow",
            None
        )

    for (
        name,
        weekday
    ) in WEEKDAY_ALIASES.items():

        if normalize_text(
            name
        ) in value:
            return (
                "weekday",
                weekday
            )

    return (
        None,
        None
    )


def resolve_clock_datetime(
    text,
    clock
):
    now = local_now()

    raw_hour = clock[
        "hour"
    ]

    minute = clock[
        "minute"
    ]

    period = extract_period_hint(
        text
    )

    day_type, weekday = parse_day_hint(
        text
    )

    if raw_hour > 12:
        hours = [
            raw_hour
        ]

    elif raw_hour == 0:
        hours = [
            0
        ]

    elif period == "am":
        hours = [
            0
            if raw_hour == 12
            else raw_hour
        ]

    elif period == "pm":
        hours = [
            12
            if raw_hour == 12
            else raw_hour + 12
        ]

    elif raw_hour == 12:
        hours = [
            12,
            0
        ]

    else:
        hours = [
            raw_hour,
            raw_hour + 12
        ]

    if day_type == "today":
        target_date = now.date()

    elif day_type == "tomorrow":
        target_date = (
            now.date()
            +
            timedelta(
                days=1
            )
        )

    elif day_type == "weekday":
        days = (
            weekday
            -
            now.weekday()
        ) % 7

        target_date = (
            now.date()
            +
            timedelta(
                days=days
            )
        )

    else:
        target_date = None

    candidates = []

    if target_date is not None:

        for hour in hours:
            candidate = datetime(
                target_date.year,
                target_date.month,
                target_date.day,
                hour,
                minute,
                tzinfo=LOCAL_TZ
            )

            if (
                day_type == "weekday"
                and
                candidate <= now
            ):
                candidate += timedelta(
                    days=7
                )

            if candidate > now:
                candidates.append(
                    candidate
                )

    else:

        for day_offset in (
            0,
            1
        ):
            date_value = (
                now.date()
                +
                timedelta(
                    days=day_offset
                )
            )

            for hour in hours:
                candidate = datetime(
                    date_value.year,
                    date_value.month,
                    date_value.day,
                    hour,
                    minute,
                    tzinfo=LOCAL_TZ
                )

                if candidate > now:
                    candidates.append(
                        candidate
                    )

    candidates.sort()

    if not candidates:
        return (
            "past",
            None
        )

    nearest = candidates[0]

    if (
        period is None
        and
        raw_hour <= 12
        and
        len(hours) > 1
    ):
        difference = (
            nearest
            -
            now
        ).total_seconds()

        if difference > 6 * 3600:
            return (
                "ambiguous",
                None
            )

    return (
        "ok",
        nearest
    )


def parse_lead_minutes(
    text
):
    value = normalize_text(
        text
    )

    if "قبل" not in value:
        return None

    if re.search(
        (
            r"\bقبل(?:ها|\s+الموعد)?\s+"
            r"ب?(?:نص|نصف)\s+ساعه\b"
        ),
        value
    ):
        return 30

    if re.search(
        (
            r"\bقبل(?:ها|\s+الموعد)?\s+"
            r"ب?ربع\s+ساعه\b"
        ),
        value
    ):
        return 15

    match = re.search(
        (
            r"\bقبل(?:ها|\s+الموعد)?\s+"
            r"ب?(\d+)\s*"
            r"(دقيقه|دقائق|دقايق|"
            r"ساعه|ساعات)\b"
        ),
        value
    )

    if match:
        amount = int(
            match.group(1)
        )

        if match.group(
            2
        ).startswith(
            "ساع"
        ):
            return amount * 60

        return amount

    return None


def extract_delivery_mode(
    text
):
    if contains_any(
        text,
        [
            "رن علي",
            "رنلي",
            "اتصل علي",
            "اتصل في",
            "اتصل فيني",
        ]
    ):
        return "call"

    if contains_any(
        text,
        [
            "ذكرني فويس",
            "التذكير فويس",
            "ابعثلي فويس",
            "ابعتلي فويس",
            "ذكرني بصوت",
            "بصوتك",
        ]
    ):
        return "voice"

    return "text"


def extract_reminder_reason(
    text
):
    raw = clean_text(
        text,
        3000
    )

    explicit = re.search(
        (
            r"(?:وقلي|وقللي|واحكيلي|"
            r"وقوللي|قوللي)\s+(.+)$"
        ),
        raw,
        flags=re.IGNORECASE
    )

    if explicit:
        return explicit.group(
            1
        ).strip()

    value = normalize_digits(
        raw
    )

    value = re.sub(
        r"^\s*(?:kemo|كيمو)\s*[,،]?\s*",
        "",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        (
            r"\b(?:ذكرني|فكرني|نبهني|"
            r"ابعثلي|ابعتلي|ارسللي)\b"
        ),
        " ",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        (
            r"\b(?:بعد|كمان|خلال)\s+"
            r"(?:\d+\s*)?"
            r"(?:ثانيه|ثواني|"
            r"دقيقه|دقائق|دقايق|"
            r"ساعه|ساعات|"
            r"نص\s+ساعه|"
            r"نصف\s+ساعه|"
            r"ربع\s+ساعه)"
        ),
        " ",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip(
        " ،,:.-"
    )

    return (
        value
        or
        "هذا تذكيرك"
    )


def build_natural_reminder_message(
    reason,
    original_request
):
    reason = clean_text(
        reason,
        1500
    ).strip(
        " .،"
    )

    normalized = normalize_text(
        reason
    )

    if "موعد" in normalized:
        natural = reason

        if normalize_text(
            natural
        ).startswith(
            "عندي "
        ):
            natural = re.sub(
                r"^\s*عندي\s+",
                "عندك ",
                natural,
                count=1,
                flags=re.IGNORECASE
            )

        elif normalize_text(
            natural
        ).startswith(
            "موعد "
        ):
            natural = (
                "عندك "
                +
                natural
            )

        return (
            "كريم، قوم، "
            +
            natural
            +
            "."
        )

    return (
        "كريم، تذكيرك: "
        +
        reason
        +
        "."
    )


# =========================================================
# REMINDER DB
# =========================================================

def set_pending_reminder(
    chat_id,
    user_id,
    request_text
):
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reminder_dialog_state
                (
                    chat_id,
                    user_id,
                    pending_request
                )
                VALUES (
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT(chat_id)
                DO UPDATE SET
                    user_id =
                    EXCLUDED.user_id,
                    pending_request =
                    EXCLUDED.pending_request,
                    updated_at =
                    NOW();
                """,
                (
                    chat_id,
                    user_id,
                    request_text
                )
            )


def get_pending_reminder(
    chat_id,
    user_id
):
    rows = safe_fetchall(
        """
        SELECT pending_request
        FROM reminder_dialog_state
        WHERE
            chat_id = %s
            AND user_id = %s
        LIMIT 1;
        """,
        (
            chat_id,
            user_id
        )
    )

    return (
        rows[0][0]
        if rows
        else None
    )


def clear_pending_reminder(
    chat_id
):
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM reminder_dialog_state
                WHERE chat_id = %s;
                """,
                (
                    chat_id,
                )
            )


def create_scheduled_job(
    user_id,
    chat_id,
    title,
    message,
    run_at,
    reason,
    delivery_mode,
    event_at=None,
    original_request=""
):
    metadata = {
        "reason":
            reason,
        "delivery_mode":
            delivery_mode,
        "original_request":
            original_request,
        "created_local":
            local_now().isoformat(),
        "allow_text_fallback":
            True,
    }

    if event_at is not None:
        metadata[
            "event_at_local"
        ] = event_at.isoformat()

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO scheduled_jobs
                (
                    user_id,
                    chat_id,
                    job_type,
                    title,
                    message,
                    run_at,
                    timezone,
                    status,
                    source,
                    metadata
                )
                VALUES (
                    %s,
                    %s,
                    'reminder',
                    %s,
                    %s,
                    %s,
                    %s,
                    'pending',
                    'user',
                    %s::jsonb
                )
                RETURNING id;
                """,
                (
                    user_id,
                    chat_id,
                    title,
                    message,
                    run_at,
                    KEMO_TIMEZONE,
                    json.dumps(
                        metadata,
                        ensure_ascii=False
                    )
                )
            )

            return cur.fetchone()[0]


def list_pending_reminders(
    user_id,
    limit=30
):
    return safe_fetchall(
        """
        SELECT
            id,
            title,
            message,
            run_at,
            metadata
        FROM scheduled_jobs
        WHERE
            user_id = %s
            AND status = 'pending'
        ORDER BY run_at ASC
        LIMIT %s;
        """,
        (
            user_id,
            limit
        )
    )


def cancel_latest_job(
    user_id
):
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE scheduled_jobs
                SET
                    status = 'cancelled',
                    cancelled_at = NOW(),
                    updated_at = NOW()
                WHERE id = (
                    SELECT id
                    FROM scheduled_jobs
                    WHERE
                        user_id = %s
                        AND status = 'pending'
                    ORDER BY created_at DESC
                    LIMIT 1
                )
                RETURNING id;
                """,
                (
                    user_id,
                )
            )

            return cur.fetchone()


def parse_metadata(
    value
):
    if isinstance(
        value,
        dict
    ):
        return value

    if isinstance(
        value,
        str
    ):
        try:
            return json.loads(
                value
            )
        except Exception:
            return {}

    return {}


def get_latest_event_job(
    user_id
):
    jobs = list_pending_reminders(
        user_id,
        30
    )

    for row in reversed(
        jobs
    ):
        (
            job_id,
            title,
            message,
            run_at,
            metadata
        ) = row

        meta = parse_metadata(
            metadata
        )

        event_value = meta.get(
            "event_at_local"
        )

        if not event_value:
            continue

        try:
            event_at = datetime.fromisoformat(
                event_value
            )

            if event_at.tzinfo is None:
                event_at = event_at.replace(
                    tzinfo=LOCAL_TZ
                )

            return {
                "id":
                    job_id,
                "title":
                    title,
                "message":
                    message,
                "event_at":
                    event_at.astimezone(
                        LOCAL_TZ
                    ),
                "reason":
                    (
                        meta.get(
                            "reason"
                        )
                        or message
                    ),
                "delivery_mode":
                    meta.get(
                        "delivery_mode",
                        "text"
                    )
            }

        except Exception:
            continue

    return None


# =========================================================
# REMINDER INTENTS
# =========================================================

def looks_like_reminder_request(
    text
):
    return (
        contains_any(
            text,
            [
                "ذكرني",
                "نبهني",
                "فكرني",
                "عندي موعد",
                "موعدي",
            ]
        )
        or
        (
            contains_any(
                text,
                [
                    "ابعثلي",
                    "ابعتلي",
                    "ارسللي",
                ]
            )
            and
            (
                parse_duration_seconds(
                    text
                )
                is not None
                or
                extract_clock_time(
                    text
                )
                is not None
            )
        )
        or
        (
            contains_any(
                text,
                [
                    "رن علي",
                    "رنلي",
                    "اتصل علي",
                ]
            )
            and
            (
                parse_duration_seconds(
                    text
                )
                is not None
                or
                extract_clock_time(
                    text
                )
                is not None
            )
        )
    )


def looks_like_time_followup(
    text
):
    return (
        extract_clock_time(
            text
        )
        is not None
        or
        parse_duration_seconds(
            text
        )
        is not None
        or
        contains_any(
            text,
            [
                "الصبح",
                "المسا",
                "المساء",
                "مساء",
                "المغرب",
                "الليل",
                "اليوم",
                "بكرا",
            ]
        )
    )


def reply_and_save(
    chat_id,
    answer,
    reply_mode
):
    save_message(
        chat_id,
        "assistant",
        answer
    )

    send_answer_by_mode(
        chat_id,
        answer,
        reply_mode
    )


def handle_local_reminder(
    chat_id,
    user_id,
    text,
    incoming_type
):
    reply_mode = detect_reply_mode(
        text,
        incoming_type
    )

    if contains_any(
        text,
        [
            "شو عندي تذكيرات",
            "ايش عندي تذكيرات",
            "اعرض تذكيراتي",
            "وين تذكيراتي",
        ]
    ):
        jobs = list_pending_reminders(
            user_id
        )

        if not jobs:
            reply_and_save(
                chat_id,
                "ما عندك تذكيرات معلقة حالياً.",
                reply_mode
            )

            return True

        lines = [
            "⏰ تذكيراتك الجاية:"
        ]

        for (
            job_id,
            title,
            message,
            run_at,
            metadata
        ) in jobs:
            meta = parse_metadata(
                metadata
            )

            lines.append(
                (
                    f"• #{job_id} — "
                    f"{format_arabic_datetime(run_at)}\n"
                    f"{meta.get('reason') or message}"
                )
            )

        reply_and_save(
            chat_id,
            "\n\n".join(
                lines
            ),
            reply_mode
        )

        return True

    if contains_any(
        text,
        [
            "الغي اخر تذكير",
            "الغ اخر تذكير",
            "احذف اخر تذكير",
        ]
    ):
        row = cancel_latest_job(
            user_id
        )

        answer = (
            "ألغيت آخر تذكير ✅"
            if row
            else
            "ما عندك تذكير ألغيّه."
        )

        reply_and_save(
            chat_id,
            answer,
            reply_mode
        )

        return True

    lead_minutes = parse_lead_minutes(
        text
    )

    if (
        lead_minutes is not None
        and
        contains_any(
            text,
            [
                "قبل الموعد",
                "قبلها",
            ]
        )
        and
        extract_clock_time(
            text
        )
        is None
    ):
        latest = get_latest_event_job(
            user_id
        )

        if not latest:
            reply_and_save(
                chat_id,
                "ما عندي موعد سابق أربط التذكير فيه.",
                reply_mode
            )

            return True

        run_at = (
            latest[
                "event_at"
            ]
            -
            timedelta(
                minutes=lead_minutes
            )
        )

        if run_at <= local_now():
            reply_and_save(
                chat_id,
                "وقت التذكير المطلوب صار بالماضي.",
                reply_mode
            )

            return True

        delivery_mode = extract_delivery_mode(
            text
        )

        if delivery_mode == "text":
            delivery_mode = latest[
                "delivery_mode"
            ]

        create_scheduled_job(
            user_id=user_id,
            chat_id=chat_id,
            title=latest[
                "title"
            ],
            message=latest[
                "message"
            ],
            run_at=run_at,
            reason=latest[
                "reason"
            ],
            delivery_mode=delivery_mode,
            event_at=latest[
                "event_at"
            ],
            original_request=text
        )

        reply_and_save(
            chat_id,
            (
                "بذكرك "
                f"{format_arabic_datetime(run_at)} ✅"
            ),
            reply_mode
        )

        return True

    pending = get_pending_reminder(
        chat_id,
        user_id
    )

    if (
        pending
        and
        looks_like_time_followup(
            text
        )
        and
        not looks_like_reminder_request(
            text
        )
    ):
        combined = (
            pending
            +
            " "
            +
            text
        )

    else:
        combined = text

    if not (
        looks_like_reminder_request(
            combined
        )
        or
        (
            pending
            and
            looks_like_time_followup(
                text
            )
        )
    ):
        return False

    reason = extract_reminder_reason(
        combined
    )

    delivery_mode = extract_delivery_mode(
        combined
    )

    reminder_message = build_natural_reminder_message(
        reason,
        combined
    )

    duration_seconds = parse_duration_seconds(
        combined
    )

    if duration_seconds is not None:

        run_at = (
            local_now()
            +
            timedelta(
                seconds=duration_seconds
            )
        ).replace(
            microsecond=0
        )

        create_scheduled_job(
            user_id=user_id,
            chat_id=chat_id,
            title=(
                "موعد"
                if "موعد" in normalize_text(
                    reason
                )
                else "تذكير"
            ),
            message=reminder_message,
            run_at=run_at,
            reason=reason,
            delivery_mode=delivery_mode,
            event_at=run_at,
            original_request=combined
        )

        clear_pending_reminder(
            chat_id
        )

        labels = {
            "text":
                "برسالة",
            "voice":
                "بفويس",
            "call":
                "بتنبيه مكالمة",
        }

        answer = (
            "ثبتتلك إياه "
            f"{labels.get(delivery_mode, '')} ✅ "
            f"{format_arabic_time(run_at, True)}."
        )

        reply_and_save(
            chat_id,
            answer,
            reply_mode
        )

        return True

    clock = extract_clock_time(
        combined
    )

    if clock:
        status, event_at = resolve_clock_datetime(
            combined,
            clock
        )

        if status == "ambiguous":
            set_pending_reminder(
                chat_id,
                user_id,
                combined
            )

            reply_and_save(
                chat_id,
                (
                    f"قصدك الساعة "
                    f"{clock['hour']}:"
                    f"{clock['minute']:02d} "
                    "الصبح ولا المسا؟"
                ),
                reply_mode
            )

            return True

        if status != "ok":
            reply_and_save(
                chat_id,
                (
                    "الوقت اللي فهمته صار بالماضي، "
                    "حددلي وقت ثاني."
                ),
                reply_mode
            )

            return True

        run_at = event_at

        lead_minutes = parse_lead_minutes(
            combined
        )

        if lead_minutes is not None:
            run_at = (
                event_at
                -
                timedelta(
                    minutes=lead_minutes
                )
            )

        if run_at <= local_now():
            reply_and_save(
                chat_id,
                "وقت التنبيه صار بالماضي.",
                reply_mode
            )

            return True

        create_scheduled_job(
            user_id=user_id,
            chat_id=chat_id,
            title=(
                "موعد"
                if "موعد" in normalize_text(
                    reason
                )
                else "تذكير"
            ),
            message=reminder_message,
            run_at=run_at,
            reason=reason,
            delivery_mode=delivery_mode,
            event_at=event_at,
            original_request=combined
        )

        clear_pending_reminder(
            chat_id
        )

        reply_and_save(
            chat_id,
            (
                "ثبتتلك التذكير ✅ "
                f"{format_arabic_datetime(run_at)}."
            ),
            reply_mode
        )

        return True

    set_pending_reminder(
        chat_id,
        user_id,
        combined
    )

    reply_and_save(
        chat_id,
        "متى بدك أذكرك؟",
        reply_mode
    )

    return True


# =========================================================
# SEARCH
# =========================================================

SEARCH_MARKERS = [
    "ابحث",
    "دورلي",
    "دور لي",
    "جيبلي من النت",
    "شوف النت",
    "اخر الاخبار",
    "اخبار اليوم",
    "سعر اليوم",
    "السعر الحالي",
    "سعر الذهب",
    "سعر الدولار",
    "سعر اليورو",
    "اخر تحديث",
    "الموقع الرسمي",
    "الطقس",
    "طقس",
    "نتيجة المباراة",
    "موعد المباراة",
    "رابط",
    "لينك",
]

SOURCE_MARKERS = [
    "المصدر",
    "المصادر",
    "اعطيني المصدر",
    "هات المصدر",
    "من وين جبت",
    "وين لقيت",
    "رابط",
    "روابط",
    "لينك",
]


def needs_web_search(
    text
):
    return contains_any(
        text,
        SEARCH_MARKERS
    )


def wants_sources(
    text
):
    return contains_any(
        text,
        SOURCE_MARKERS
    )


def tavily_search(
    query
):
    if not TAVILY_API_KEY:
        return []

    response = post_json(
        "https://api.tavily.com/search",
        {
            "query":
                query,
            "search_depth":
                "basic",
            "max_results":
                5,
            "include_answer":
                False,
            "include_raw_content":
                False
        },
        headers={
            "Authorization":
                (
                    "Bearer "
                    f"{TAVILY_API_KEY}"
                )
        },
        timeout=60
    )

    return response.get(
        "results",
        []
    )


def build_search_context(
    results
):
    lines = [
        "=== نتائج بحث حقيقية حديثة ==="
    ]

    for index, result in enumerate(
        results,
        start=1
    ):
        lines.append(
            (
                f"{index}. "
                f"{result.get('title', '')}\n"
                f"{result.get('content', '')[:1200]}\n"
                f"URL: {result.get('url', '')}"
            )
        )

    lines.append(
        (
            "لا تستخدم معلومة غير مدعومة "
            "بالنتائج."
        )
    )

    return "\n\n".join(
        lines
    )


def add_sources(
    answer,
    results
):
    urls = []

    for result in results[:5]:
        url = clean_text(
            result.get(
                "url"
            ),
            1500
        )

        if url and url not in urls:
            urls.append(
                url
            )

    if not urls:
        return answer

    return (
        answer
        +
        "\n\n🔎 المصادر:\n"
        +
        "\n".join(
            urls
        )
    )


def strip_urls(
    answer
):
    value = re.sub(
        r"https?://\S+",
        "",
        str(
            answer or ""
        )
    )

    value = re.sub(
        r"\n{3,}",
        "\n\n",
        value
    )

    return value.strip()


def save_search_memory(
    user_id,
    query,
    results
):
    if not results:
        return

    lines = [
        (
            "بحث XPAND على الإنترنت عن: "
            +
            clean_text(
                query,
                500
            )
        )
    ]

    for index, result in enumerate(
        results[:3],
        start=1
    ):
        lines.append(
            (
                f"{index}. "
                f"{clean_text(result.get('title'), 250)}\n"
                f"{clean_text(result.get('content'), 500)}\n"
                f"المصدر: "
                f"{clean_text(result.get('url'), 1200)}"
            )
        )

    save_memory(
        user_id,
        "\n\n".join(
            lines
        ),
        category="research",
        importance=4,
        source="telegram_search"
    )


# =========================================================
# CHAT MODEL ROUTING
# =========================================================

DEEP_THINKING_MARKERS = [
    "حلل",
    "تحليل",
    "دراسة",
    "استراتيجية",
    "استراتيجيه",
    "خطة عمل",
    "خطة مشروع",
    "قارن",
    "مقارنة",
    "قرار",
    "شو الافضل",
    "شو الأفضل",
    "السوق",
    "فرصة",
    "business",
    "market",
    "roi",
    "ربح",
    "تكلفة",
    "جدوى",
]


def choose_chat_models(
    text
):
    if contains_any(
        text,
        DEEP_THINKING_MARKERS
    ):
        return DEEP_CHAT_MODELS

    return GEMINI_MODELS


# =========================================================
# CHAT INSTRUCTIONS
# =========================================================

def build_chat_instructions(
    user_id,
    user_message
):
    master = load_master_system_prompt()

    memory_context, verified_memory = (
        build_memory_context(
            user_id,
            user_message
        )
    )

    extra_guard = ""

    if looks_like_personal_memory_question(
        user_message
    ):
        if verified_memory:
            extra_guard = """
السؤال الحالي عن ذاكرة شخصية لكريم.
استخدم فقط المعلومات الموثقة الموجودة أعلاه.
لا تضف اسماً أو معلومة غير موجودة.
"""
        else:
            extra_guard = """
السؤال الحالي عن ذاكرة شخصية لكريم،
لكن لم يتم العثور على معلومة موثقة مرتبطة به.

ممنوع التخمين.
قل إن المعلومة غير محفوظة عندك بشكل موثوق.
"""

    return (
        master
        +
        "\n\n"
        +
        TELEGRAM_RUNTIME_RULES
        +
        "\n\n"
        +
        build_current_time_context()
        +
        "\n\n"
        +
        "==================================================\n"
        +
        "ذاكرة Kemo المسترجعة لهذا السؤال\n"
        +
        "==================================================\n\n"
        +
        memory_context
        +
        "\n\n"
        +
        extra_guard
    )


# =========================================================
# CHAT
# =========================================================

def ask_kemo(
    chat_id,
    user_id,
    user_message
):
    history = load_recent_messages(
        chat_id
    )

    search_results = []

    current_input = str(
        user_message
    )

    if needs_web_search(
        user_message
    ):
        try:
            search_results = tavily_search(
                user_message
            )

            if search_results:
                current_input += (
                    "\n\n"
                    +
                    build_search_context(
                        search_results
                    )
                )

                save_search_memory(
                    user_id,
                    user_message,
                    search_results
                )

        except Exception as error:
            print(
                f"⚠️ Search: {error}"
            )

    instructions = build_chat_instructions(
        user_id,
        user_message
    )

    history.append(
        {
            "role":
                "user",
            "parts": [
                {
                    "text":
                        current_input
                }
            ]
        }
    )

    last_error = None

    for model in choose_chat_models(
        user_message
    ):
        try:
            print(
                f"🧠 Trying chat model: {model}"
            )

            response = call_gemini(
                model,
                history,
                instructions
            )

            answer = extract_gemini_text(
                response
            )

            if not answer:
                raise Exception(
                    "Empty response"
                )

            if wants_sources(
                user_message
            ):
                if search_results:
                    answer = add_sources(
                        answer,
                        search_results
                    )

            else:
                answer = strip_urls(
                    answer
                )

            save_message(
                chat_id,
                "assistant",
                answer
            )

            print(
                f"✅ Chat model used: {model}"
            )

            return answer

        except Exception as error:
            last_error = error

            print(
                f"⚠️ Chat model {model}: {error}"
            )

    raise Exception(
        f"Gemini failed: {last_error}"
    )


# =========================================================
# CALL INTENT
# =========================================================

CALL_MARKERS = [
    "رن علي",
    "رنلي",
    "اتصل علي",
    "اتصل في",
    "اتصل فيني",
    "اعمل مكالمه",
    "اعمل مكالمة",
    "بدي مكالمه",
    "بدي مكالمة",
]


def has_call_intent(
    text
):
    return contains_any(
        text,
        CALL_MARKERS
    )


def has_schedule_signal(
    text
):
    return (
        parse_duration_seconds(
            text
        )
        is not None
        or
        extract_clock_time(
            text
        )
        is not None
    )


# =========================================================
# COMMANDS
# =========================================================

def memory_statistics(
    user_id
):
    canonical = safe_fetchall(
        """
        SELECT COUNT(*)
        FROM canonical_facts
        WHERE
            user_id = %s
            AND status = 'active';
        """,
        (
            user_id,
        )
    )

    archive = safe_fetchall(
        """
        SELECT COUNT(*)
        FROM memory_archive
        WHERE user_id = %s;
        """,
        (
            user_id,
        )
    )

    pending = safe_fetchall(
        """
        SELECT COUNT(*)
        FROM memory_learning_jobs
        WHERE
            user_id = %s
            AND status IN (
                'pending',
                'retry',
                'processing'
            );
        """,
        (
            user_id,
        )
    )

    return {
        "canonical":
            (
                canonical[0][0]
                if canonical
                else 0
            ),
        "archive":
            (
                archive[0][0]
                if archive
                else 0
            ),
        "pending":
            (
                pending[0][0]
                if pending
                else 0
            ),
    }


def handle_command(
    chat_id,
    user_id,
    text
):
    if text.startswith(
        "/start"
    ):
        send_message(
            chat_id,
            (
                "kemo شغال ✅\n\n"
                "💬 كتابة → كتابة\n"
                "🎙️ فويس → فويس\n"
                "🧠 Permanent Memory V2\n"
                "⏰ تذكيرات\n"
                "📞 مكالمة"
            )
        )

        return True

    if text.startswith(
        "/call"
    ):
        send_call_button(
            chat_id
        )

        return True

    if text.startswith(
        "/time"
    ):
        now = local_now()

        send_message(
            chat_id,
            (
                f"🕒 "
                f"{format_arabic_time(now, True)}\n"
                f"📅 "
                f"{format_arabic_date(now)}"
            )
        )

        return True

    if text.startswith(
        "/reminders"
    ):
        jobs = list_pending_reminders(
            user_id
        )

        if not jobs:
            send_message(
                chat_id,
                "ما عندك تذكيرات معلقة."
            )

            return True

        lines = [
            "⏰ تذكيراتك:"
        ]

        for (
            job_id,
            title,
            message,
            run_at,
            metadata
        ) in jobs:
            meta = parse_metadata(
                metadata
            )

            lines.append(
                (
                    f"#{job_id} — "
                    f"{format_arabic_datetime(run_at)}\n"
                    f"{meta.get('reason') or message}"
                )
            )

        send_message(
            chat_id,
            "\n\n".join(
                lines
            )
        )

        return True

    if text.startswith(
        "/memory"
    ):
        stats = memory_statistics(
            user_id
        )

        send_message(
            chat_id,
            (
                "🧠 Permanent Memory V2\n\n"
                f"حقائق ثابتة: "
                f"{stats['canonical']}\n"
                f"أرشيف رسائل دائم: "
                f"{stats['archive']}\n"
                f"قيد التعلم بالخلفية: "
                f"{stats['pending']}"
            )
        )

        return True

    if text.startswith(
        "/status"
    ):
        stats = memory_statistics(
            user_id
        )

        send_message(
            chat_id,
            (
                "kemo شغال ✅\n"
                "🧠 Master Prompt: ✅\n"
                "🧠 Permanent Memory V2: ✅\n"
                f"📚 Canonical Facts: "
                f"{stats['canonical']}\n"
                f"🗄️ Archive: "
                f"{stats['archive']}\n"
                "🛡️ Personal fact anti-hallucination: ✅\n"
                "🎙️ Voice: ✅\n"
                "📞 Call memory: ✅\n"
                f"🎭 Voice: {KEMO_VOICE}"
            )
        )

        return True

    return False


# =========================================================
# DIRECT TIME
# =========================================================

def handle_direct_time_request(
    chat_id,
    text,
    incoming_type
):
    answer = direct_time_or_date_answer(
        text
    )

    if not answer:
        return False

    save_message(
        chat_id,
        "assistant",
        answer
    )

    send_answer_by_mode(
        chat_id,
        answer,
        detect_reply_mode(
            text,
            incoming_type
        )
    )

    return True


# =========================================================
# AI ERROR
# =========================================================

def send_ai_error(
    chat_id,
    error
):
    if is_rate_limit_error(
        error
    ):
        send_message(
            chat_id,
            (
                "حصة Gemini للمحادثة "
                "خلصت مؤقتًا 😅\n"
                "الذاكرة والتذكيرات "
                "لسه شغالين."
            )
        )

        return

    send_message(
        chat_id,
        "صار عندي خلل مؤقت بالمحادثة."
    )


# =========================================================
# VOICE HANDLER
# =========================================================

def handle_voice(
    chat_id,
    user_id,
    voice
):
    file_size = (
        voice.get(
            "file_size",
            0
        )
        or
        0
    )

    if (
        file_size
        >
        MAX_TELEGRAM_VOICE_BYTES
    ):
        send_message(
            chat_id,
            "الفويس كبير زيادة."
        )

        return

    audio = get_telegram_file_bytes(
        voice.get(
            "file_id"
        )
    )

    transcript_text = transcribe_voice(
        audio,
        voice.get(
            "mime_type"
        )
        or
        "audio/ogg"
    )

    print(
        f"🎙️ USER: {transcript_text}"
    )

    message_id = save_message(
        chat_id,
        "user",
        transcript_text
    )

    ingest_user_message(
        user_id,
        chat_id,
        transcript_text,
        message_id
    )

    if handle_local_reminder(
        chat_id,
        user_id,
        transcript_text,
        "voice"
    ):
        return

    if handle_direct_time_request(
        chat_id,
        transcript_text,
        "voice"
    ):
        return

    if handle_direct_memory_request(
        chat_id,
        user_id,
        transcript_text,
        "voice"
    ):
        return

    if (
        has_call_intent(
            transcript_text
        )
        and
        not has_schedule_signal(
            transcript_text
        )
    ):
        send_call_button(
            chat_id
        )

        return

    try:
        answer = ask_kemo(
            chat_id,
            user_id,
            transcript_text
        )

        send_answer_by_mode(
            chat_id,
            answer,
            detect_reply_mode(
                transcript_text,
                "voice"
            )
        )

    except Exception as error:
        print(
            f"❌ Voice chat: {error}"
        )

        send_ai_error(
            chat_id,
            error
        )


# =========================================================
# STARTUP MEMORY RECOVERY
# =========================================================

def prepare_permanent_memory(
    user_id
):
    try:
        backfill_memory_archive(
            user_id
        )

    except Exception as error:
        print(
            f"⚠️ Archive backfill: {error}"
        )

    try:
        recover_family_facts_from_history(
            user_id
        )

    except Exception as error:
        print(
            f"⚠️ Family recovery: {error}"
        )


# =========================================================
# MAIN
# =========================================================

def main():
    print("")
    print(
        "===================================="
    )
    print(
        "       KEMO HUMAN CORE V7"
    )
    print(
        "     PERMANENT MEMORY V2"
    )
    print(
        "===================================="
    )

    if not TELEGRAM_BOT_TOKEN:
        print(
            "❌ TELEGRAM_BOT_TOKEN missing"
        )
        return

    if not GEMINI_API_KEY:
        print(
            "❌ GEMINI_API_KEY missing"
        )
        return

    if not DATABASE_URL:
        print(
            "❌ DATABASE_URL missing"
        )
        return

    if not TELEGRAM_ALLOWED_USER_ID:
        print(
            "❌ TELEGRAM_ALLOWED_USER_ID missing"
        )
        return

    try:
        init_database()

    except Exception as error:
        print(
            f"❌ DB: {error}"
        )
        return

    try:
        ensure_core_lessons(
            TELEGRAM_ALLOWED_USER_ID
        )

    except Exception as error:
        print(
            f"⚠️ Core lessons: {error}"
        )

    # استرجع المعلومات القديمة قبل بدء البوت.
    prepare_permanent_memory(
        TELEGRAM_ALLOWED_USER_ID
    )

    # عامل تعلم منفصل:
    # لا يؤخر الرد.
    memory_thread = threading.Thread(
        target=memory_learning_worker,
        name="kemo-memory-worker",
        daemon=True
    )

    memory_thread.start()

    try:
        ffmpeg = (
            imageio_ffmpeg
            .get_ffmpeg_exe()
        )

        print(
            f"✅ FFmpeg: {ffmpeg}"
        )

    except Exception as error:
        print(
            f"❌ FFmpeg: {error}"
        )
        return

    print(
        "✅ Telegram"
    )

    print(
        "✅ Gemini chat"
    )

    print(
        (
            "✅ Fast chat model: "
            f"{GEMINI_MODELS[0]}"
        )
    )

    print(
        (
            "✅ Deep model: "
            f"{DEEP_CHAT_MODELS[0]}"
        )
    )

    print(
        "✅ Full Master System Prompt"
    )

    print(
        "✅ Shared prompt from kemo_config"
    )

    print(
        "✅ PERMANENT MEMORY V2"
    )

    print(
        "✅ Canonical Facts: ACTIVE"
    )

    print(
        "✅ Canonical Fact History: ACTIVE"
    )

    print(
        "✅ Full Conversation Archive: ACTIVE"
    )

    print(
        "✅ Smart Memory Retrieval: ACTIVE"
    )

    print(
        "✅ Background Memory Learning: ACTIVE"
    )

    print(
        "✅ Old Memory Recovery: ACTIVE"
    )

    print(
        "✅ Personal Fact Hallucination Guard: ACTIVE"
    )

    print(
        "✅ Direct Family Memory Answers: ACTIVE"
    )

    print(
        "✅ Text + Voice shared memory"
    )

    print(
        f"✅ Timezone: {KEMO_TIMEZONE}"
    )

    print(
        f"✅ Unified voice: {KEMO_VOICE}"
    )

    print("")

    try:
        telegram_request(
            "deleteWebhook",
            {
                "drop_pending_updates":
                    False
            }
        )

    except Exception as error:
        print(
            f"⚠️ Webhook: {error}"
        )

    offset = None

    while True:
        try:
            request_data = {
                "timeout":
                    25,
                "allowed_updates": [
                    "message"
                ]
            }

            if offset is not None:
                request_data[
                    "offset"
                ] = offset

            updates = telegram_request(
                "getUpdates",
                request_data
            )

            for update in updates.get(
                "result",
                []
            ):
                update_id = update.get(
                    "update_id"
                )

                if update_id is not None:
                    offset = (
                        update_id
                        +
                        1
                    )

                message = update.get(
                    "message"
                )

                if not message:
                    continue

                chat_id = (
                    message.get(
                        "chat",
                        {}
                    ).get(
                        "id"
                    )
                )

                user_id = (
                    message.get(
                        "from",
                        {}
                    ).get(
                        "id"
                    )
                )

                if (
                    not chat_id
                    or
                    not user_id
                ):
                    continue

                if (
                    user_id
                    !=
                    TELEGRAM_ALLOWED_USER_ID
                ):
                    print(
                        "⛔ Unauthorized user blocked"
                    )
                    continue

                try:
                    claimed = claim_telegram_update(
                        update_id
                    )

                except Exception as error:
                    print(
                        f"⚠️ Claim update: {error}"
                    )
                    claimed = True

                if not claimed:
                    print(
                        f"♻️ Duplicate ignored: "
                        f"{update_id}"
                    )
                    continue

                ensure_conversation_state(
                    chat_id,
                    user_id
                )

                voice = message.get(
                    "voice"
                )

                text = message.get(
                    "text"
                )

                if voice:
                    try:
                        handle_voice(
                            chat_id,
                            user_id,
                            voice
                        )

                    except Exception as error:
                        print(
                            f"❌ VOICE: {error}"
                        )

                        record_event(
                            user_id,
                            chat_id,
                            "voice_error",
                            str(
                                error
                            )
                        )

                        send_message(
                            chat_id,
                            (
                                "صار خلل وأنا بفهم "
                                "الفويس، جرّبه مرة ثانية."
                            )
                        )

                    continue

                if not text:
                    continue

                print(
                    f"📩 USER: {text[:300]}"
                )

                # كل كلمة كتابة تدخل الأرشيف الدائم
                # قبل أي معالجة.
                message_id = save_message(
                    chat_id,
                    "user",
                    text
                )

                ingest_user_message(
                    user_id,
                    chat_id,
                    text,
                    message_id
                )

                # =========================================
                # COMMANDS
                # =========================================

                if handle_command(
                    chat_id,
                    user_id,
                    text
                ):
                    continue

                # =========================================
                # REMINDER
                # =========================================

                if handle_local_reminder(
                    chat_id,
                    user_id,
                    text,
                    "text"
                ):
                    continue

                # =========================================
                # EXACT TIME
                # =========================================

                if handle_direct_time_request(
                    chat_id,
                    text,
                    "text"
                ):
                    continue

                # =========================================
                # DIRECT VERIFIED PERSONAL MEMORY
                # =========================================

                if handle_direct_memory_request(
                    chat_id,
                    user_id,
                    text,
                    "text"
                ):
                    continue

                # =========================================
                # IMMEDIATE CALL
                # =========================================

                if (
                    has_call_intent(
                        text
                    )
                    and
                    not has_schedule_signal(
                        text
                    )
                ):
                    send_call_button(
                        chat_id
                    )
                    continue

                # =========================================
                # NORMAL CHAT
                # =========================================

                try:
                    send_action(
                        chat_id,
                        "typing"
                    )

                    answer = ask_kemo(
                        chat_id,
                        user_id,
                        text
                    )

                    send_answer_by_mode(
                        chat_id,
                        answer,
                        detect_reply_mode(
                            text,
                            "text"
                        )
                    )

                except Exception as error:
                    print(
                        f"❌ TEXT: {error}"
                    )

                    record_event(
                        user_id,
                        chat_id,
                        "chat_error",
                        str(
                            error
                        )
                    )

                    send_ai_error(
                        chat_id,
                        error
                    )

        except Exception as error:
            error_text = str(
                error
            )

            print(
                f"❌ LOOP: {error_text}"
            )

            if (
                "409"
                in error_text
            ):
                time.sleep(
                    10
                )

            else:
                time.sleep(
                    3
                )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()


# =========================================================
# KEMO HUMAN CORE V7
#
# PERMANENT MEMORY V2
#
# - CANONICAL FACTS
# - VERSION HISTORY
# - COMPLETE MESSAGE ARCHIVE
# - SMART RETRIEVAL
# - BACKGROUND LEARNING
# - OLD MEMORY RECOVERY
# - PERSONAL FACT HALLUCINATION GUARD
# - DIRECT VERIFIED FAMILY ANSWERS
# =========================================================
