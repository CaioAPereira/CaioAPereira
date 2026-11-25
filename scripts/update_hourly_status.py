import html
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

README_PATH = Path("README.md")
START_MARKER = "<!-- HOURLY_STATUS_START -->"
END_MARKER = "<!-- HOURLY_STATUS_END -->"


def get_hourly_message(now: datetime) -> str:
    hour = now.hour
    time_label = now.strftime("%H:%M")

    if 6 <= hour < 12:
        status = "Morning coffee &amp; systems check in progress"
        icon = "☀️"
    elif 12 <= hour < 18:
        status = "Afternoon build mode — containers, infrastructure &amp; code"
        icon = "💻"
    elif 18 <= hour < 23:
        status = "Evening lab &amp; problem-solving session"
        icon = "🌙"
    else:
        status = "Late-night tinkering &amp; async mode"
        icon = "🦉"

    safe_status = html.escape(status, quote=False)
    return (
        f'<p align="center">\n'
        f'  <sub>{icon} <b>{time_label} BRT</b> — {safe_status}</sub>\n'
        f'</p>'
    )


def main() -> None:
    now_brt = datetime.now(ZoneInfo("America/Sao_Paulo"))
    content = README_PATH.read_text(encoding="utf-8")

    pattern = re.compile(
        rf"({re.escape(START_MARKER)}\n).*?(\n{re.escape(END_MARKER)})",
        flags=re.DOTALL,
    )

    if not pattern.search(content):
        raise ValueError("Start/end markers not found in README.md")

    new_block = get_hourly_message(now_brt)
    updated_content = pattern.sub(rf"\g<1>{new_block}\g<2>", content, count=1)

    if updated_content != content:
        README_PATH.write_text(updated_content, encoding="utf-8")


if __name__ == "__main__":
    main()
