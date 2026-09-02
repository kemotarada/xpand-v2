from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent

MAIN_FILE = ROOT / "telegram-bot" / "main.py"
CALL_HTML = ROOT / "call" / "index.html"
CALL_APP = ROOT / "call" / "app.js"


def read(path: Path) -> str:
    if not path.exists():
        raise RuntimeError(f"Missing file: {path}")

    return path.read_text(
        encoding="utf-8"
    )


def write(path: Path, value: str):
    path.write_text(
        value,
        encoding="utf-8"
    )


def rebrand_master_prompt():
    text = read(
        MAIN_FILE
    )

    start_marker = (
        'MASTER_SYSTEM_PROMPT = r"""'
    )

    start = text.find(
        start_marker
    )

    if start < 0:
        raise RuntimeError(
            "MASTER_SYSTEM_PROMPT not found"
        )

    prompt_start = (
        start
        +
        len(
            start_marker
        )
    )

    prompt_end = text.find(
        '"""',
        prompt_start
    )

    if prompt_end < 0:
        raise RuntimeError(
            "MASTER_SYSTEM_PROMPT closing marker not found"
        )

    prompt = text[
        prompt_start:prompt_end
    ]

    prompt = (
        prompt
        .replace(
            "KEMO",
            "XPAND"
        )
        .replace(
            "Kemo",
            "XPAND"
        )
        .replace(
            "kemo",
            "XPAND"
        )
        .replace(
            "كيمو",
            "إكسباند"
        )
    )

    text = (
        text[:prompt_start]
        +
        prompt
        +
        text[prompt_end:]
    )

    text = re.sub(
        r'MASTER_PROMPT_VERSION\s*=\s*\(\s*"[^"]+"\s*\)',
        (
            'MASTER_PROMPT_VERSION = (\n'
            '    "2026-09-02-xpand-master-v1"\n'
            ')'
        ),
        text,
        count=1,
        flags=re.MULTILINE,
    )

    visible_replacements = {
        "📞 اتصل بـ kemo":
            "📞 اتصل بـ XPAND",

        "📞 اتصل بـ Kemo":
            "📞 اتصل بـ XPAND",

        "بحث Kemo على الإنترنت عن: ":
            "بحث XPAND على الإنترنت عن: ",

        "=== فرص سبق أن أرسلها Kemo ===":
            "=== فرص سبق أن أرسلها XPAND ===",
    }

    for old, new in visible_replacements.items():
        text = text.replace(
            old,
            new
        )

    write(
        MAIN_FILE,
        text
    )


def rebrand_call_html():
    text = read(
        CALL_HTML
    )

    text = (
        text
        .replace(
            "<title>Kemo Call</title>",
            "<title>XPAND Call</title>"
        )
        .replace(
            "<title>KEMO Call</title>",
            "<title>XPAND Call</title>"
        )
    )

    text = re.sub(
        r'(<div\s+class="brand"[^>]*>.*?<span>\s*)KEMO(\s*</span>)',
        r'\1XPAND\2',
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r'(<div\s+class="kemo-letter"[^>]*>\s*)K(\s*</div>)',
        r'\1X\2',
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r'(<h1>\s*)kemo(\s*</h1>)',
        r'\1XPAND\2',
        text,
        flags=re.IGNORECASE,
    )

    write(
        CALL_HTML,
        text
    )


def rebrand_call_app():
    text = read(
        CALL_APP
    )

    text = (
        text
        .replace(
            "KEMO",
            "XPAND"
        )
        .replace(
            "Kemo",
            "XPAND"
        )
        .replace(
            "kemo",
            "XPAND"
        )
        .replace(
            "كيمو",
            "إكسباند"
        )
    )

    write(
        CALL_APP,
        text
    )


def main():
    print(
        "XPAND rebrand starting..."
    )

    rebrand_master_prompt()

    print(
        "OK: Telegram/System Prompt"
    )

    rebrand_call_html()

    print(
        "OK: Call HTML"
    )

    rebrand_call_app()

    print(
        "OK: Call UI runtime"
    )

    print("")
    print(
        "XPAND USER-FACING REBRAND COMPLETE"
    )

    print(
        "Internal KEMO_* variables preserved."
    )

    print(
        "Internal database/table names preserved."
    )

    print(
        "Internal Python function/module names preserved."
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(
            f"ERROR: {error}"
        )

        sys.exit(
            1
        )
