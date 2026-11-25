import html
import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

README_PATH = Path("README.md")
USERNAME = "CaioAPereira"
TARGET_YEAR = 2026

HOURLY_START = "<!-- HOURLY_STATUS_START -->"
HOURLY_END = "<!-- HOURLY_STATUS_END -->"

STATS_2026_START = "<!-- YEAR_2026_STATS_START -->"
STATS_2026_END = "<!-- YEAR_2026_STATS_END -->"


def get_hourly_message(now: datetime) -> str:
    hour = now.hour
    time_label = now.strftime("%H:%M")

    if 6 <= hour < 12:
        icon = "☀️"
        status = "Morning coffee &amp; systems check in progress"
    elif 12 <= hour < 18:
        icon = "💻"
        status = "Afternoon build mode — containers, infrastructure &amp; code"
    elif 18 <= hour < 23:
        icon = "🌙"
        status = "Evening lab &amp; problem-solving session"
    else:
        icon = "🦉"
        status = "Late-night tinkering &amp; async mode"

    safe_status = html.escape(status, quote=False)
    return (
        f'<p align="center">\n'
        f'  <sub>{icon} <b>{time_label} BRT</b> • {safe_status}</sub>\n'
        f'</p>'
    )


def fetch_2026_summary(username: str) -> str:
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{username}-readme-updater",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(url, headers=headers)
    with urlopen(req, timeout=15) as resp:
        repos = json.loads(resp.read().decode("utf-8"))

    repos_2026 = []
    for repo in repos:
        if repo.get("fork"):
            continue
        pushed_at = repo.get("pushed_at") or ""
        created_at = repo.get("created_at") or ""
        if pushed_at.startswith(f"{TARGET_YEAR}-") or created_at.startswith(f"{TARGET_YEAR}-"):
            repos_2026.append(repo)

    active_2026_count = len(repos_2026)
    latest_repo = repos_2026[0]["name"] if repos_2026 else "N/A"
    safe_latest = html.escape(latest_repo, quote=False)

    return (
        f'<p align="center">\n'
        f'  <sub>📅 <b>{TARGET_YEAR} Activity</b> • '
        f'<b>{active_2026_count}</b> active own repos in {TARGET_YEAR} • '
        f'Latest touched: <code>{safe_latest}</code></sub>\n'
        f'</p>'
    )


def replace_block(content: str, start_marker: str, end_marker: str, new_block: str) -> str:
    pattern = re.compile(
        rf"({re.escape(start_marker)}\n).*?(\n{re.escape(end_marker)})",
        flags=re.DOTALL,
    )
    if not pattern.search(content):
        raise ValueError(f"Markers not found: {start_marker} / {end_marker}")
    return pattern.sub(rf"\g<1>{new_block}\g<2>", content, count=1)


def main() -> None:
    now_brt = datetime.now(ZoneInfo("America/Sao_Paulo"))
    content = README_PATH.read_text(encoding="utf-8")

    hourly_block = get_hourly_message(now_brt)
    stats_2026_block = fetch_2026_summary(USERNAME)

    updated = replace_block(content, HOURLY_START, HOURLY_END, hourly_block)
    updated = replace_block(updated, STATS_2026_START, STATS_2026_END, stats_2026_block)

    if updated != content:
        README_PATH.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
