#!/usr/bin/env python3
"""Fetch recent entries from an RSS or Atom feed."""

import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse


def fetch_feed(url: str, hours: int = 24) -> list[dict]:
    """Fetch entries from the last N hours from an RSS/Atom feed."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        print(f"Error: only HTTP(S) URLs allowed, got {parsed.scheme}://", file=sys.stderr)
        return []

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"Warning: could not fetch {url}: {e}", file=sys.stderr)
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    results = []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"Warning: invalid XML from {url}: {e}", file=sys.stderr)
        return []

    # RSS 2.0
    for item in root.iter("item"):
        title = item.findtext("title", "")
        desc = item.findtext("description", "")
        link = item.findtext("link", "")
        pub = item.findtext("pubDate", "")
        try:
            dt = parsedate_to_datetime(pub)
            if dt >= cutoff:
                desc = re.sub(r"<[^>]+>", " ", desc).strip()[:300]
                results.append(
                    {
                        "title": title,
                        "description": desc,
                        "link": link,
                        "date": pub,
                        "source": url,
                    }
                )
        except Exception:
            pass

    # Atom
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        title = entry.findtext("atom:title", "", ns)
        summary = (
            entry.findtext("atom:summary", "", ns)
            or entry.findtext("atom:content", "", ns)
            or ""
        )
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "") if link_el is not None else ""
        updated = entry.findtext("atom:updated", "", ns) or entry.findtext(
            "atom:published", "", ns
        )
        try:
            dt = datetime.fromisoformat(updated)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt >= cutoff:
                summary = re.sub(r"<[^>]+>", " ", summary).strip()[:300]
                results.append(
                    {
                        "title": title,
                        "description": summary,
                        "link": link,
                        "date": updated,
                        "source": url,
                    }
                )
        except Exception:
            pass

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: fetch_rss.py <feed_url> [hours]", file=sys.stderr)
        sys.exit(1)

    feed_url = sys.argv[1]
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    entries = fetch_feed(feed_url, hours)
    print(json.dumps(entries, ensure_ascii=False, indent=2))
