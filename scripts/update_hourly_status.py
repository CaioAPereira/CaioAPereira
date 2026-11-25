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

HOURLY_START = "<!-- HOURLY_STATUS_START -->"
HOURLY_END = "<!-- HOURLY_STATUS_END -->"

STATS_START = "<!-- YEAR_STATS_START -->"
STATS_END = "<!-- YEAR_STATS_END -->"


def get_hourly_message(now: datetime) -> str:
    hour = now.hour
    # Hour only: the README is rewritten once per hour, so minutes would always look stale.
    time_label = now.strftime("%Hh")

    if 6 <= hour < 12:
        icon = "☀️"
        status = "Morning coffee & systems check in progress"
    elif 12 <= hour < 18:
        icon = "💻"
        status = "Afternoon build mode — containers, infrastructure & code"
    elif 18 <= hour < 23:
        icon = "🌙"
        status = "Evening lab & problem-solving session"
    else:
        icon = "🦉"
        status = "Late-night tinkering & async mode"

    safe_status = html.escape(status, quote=False)
    return (
        f'<p align="center">\n'
        f'  <sub>{icon} <b>{time_label} BRT</b> • {safe_status}</sub>\n'
        f'</p>'
    )


def github_request(url: str, payload: dict | None = None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "readme-updater",
    }
    # Injected by the workflow from secrets.GITHUB_TOKEN (temporary, per-run token).
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    with urlopen(Request(url, data=data, headers=headers), timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_year_summary(username: str, now: datetime) -> str:
    year = now.year

    # Same number as the profile contribution graph (includes private ones if enabled in profile settings).
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar { totalContributions }
        }
      }
    }"""
    result = github_request(
        "https://api.github.com/graphql",
        {"query": query, "variables": {
            "login": username,
            "from": f"{year}-01-01T00:00:00Z",
            "to": now.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }},
    )
    if "errors" in result:
        raise RuntimeError(f"GraphQL error: {result['errors']}")
    contributions = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

    repos = github_request(f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed")
    repos_year = [
        r for r in repos
        if not r.get("fork")
        and ((r.get("pushed_at") or "").startswith(f"{year}-") or (r.get("created_at") or "").startswith(f"{year}-"))
    ]
    latest_repo = repos_year[0]["name"] if repos_year else "N/A"
    safe_latest = html.escape(latest_repo, quote=False)

    return (
        f'<p align="center">\n'
        f'  <sub>📅 <b>{year} Activity</b> • '
        f'<b>{contributions}</b> contributions • '
        f'<b>{len(repos_year)}</b> active own repos • '
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
    stats_block = fetch_year_summary(USERNAME, now_brt)

    updated = replace_block(content, HOURLY_START, HOURLY_END, hourly_block)
    updated = replace_block(updated, STATS_START, STATS_END, stats_block)

    if updated != content:
        README_PATH.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
