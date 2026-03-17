#!/usr/bin/env python3
"""Fetch recent posts from a public Telegram channel via t.me/s/ page."""

import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone


def fetch_channel(channel_name: str, hours: int = 24) -> list[dict]:
    """Fetch posts from the last N hours from a public Telegram channel."""
    url = f"https://t.me/s/{channel_name}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"Warning: could not fetch @{channel_name}: {e}", file=sys.stderr)
        return []

    dates = re.findall(r'<time[^>]*datetime="([^"]+)"', html)
    texts = re.findall(
        r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL
    )
    links = re.findall(
        r'<a class="tgme_widget_message_date"[^>]*href="([^"]+)"', html
    )

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    results = []

    for i, date_str in enumerate(dates):
        try:
            dt = datetime.fromisoformat(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt >= cutoff:
                text = texts[i] if i < len(texts) else ""
                text = re.sub(r"<[^>]+>", " ", text).strip()
                text = re.sub(r"\s+", " ", text)
                link = links[i] if i < len(links) else ""
                results.append(
                    {
                        "text": text[:500],
                        "date": date_str,
                        "link": link,
                        "channel": channel_name,
                    }
                )
        except Exception:
            pass

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: fetch_telegram.py <channel_name> [hours]", file=sys.stderr)
        sys.exit(1)

    channel = sys.argv[1].lstrip("@")
    if not re.match(r'^[a-zA-Z0-9_]{3,32}$', channel):
        print(f"Error: invalid channel name '{channel}'", file=sys.stderr)
        sys.exit(1)
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    posts = fetch_channel(channel, hours)
    print(json.dumps(posts, ensure_ascii=False, indent=2))
