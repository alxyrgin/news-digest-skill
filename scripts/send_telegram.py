#!/usr/bin/env python3
"""Send a message to Telegram via Bot API, splitting if needed."""

import json
import sys
import urllib.parse
import urllib.request


def send_message(token: str, chat_id: str, text: str) -> None:
    """Send text to Telegram, splitting into chunks if over 4000 chars."""
    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > 4000:
            chunks.append(current)
            current = line
        else:
            current += ("\n" if current else "") + line
    if current:
        chunks.append(current)

    for i, chunk in enumerate(chunks):
        data = urllib.parse.urlencode(
            {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": "true",
            }
        ).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data
        )
        try:
            # SSL verification is intentionally enabled (default context)
            resp = urllib.request.urlopen(req)
            result = json.loads(resp.read())
            if not result.get("ok"):
                print(f"Telegram API error: {result}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Failed to send chunk {i + 1}: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Sent {len(chunks)} message(s) to Telegram.")


if __name__ == "__main__":
    import os

    config_path = os.path.expanduser("~/.config/news-digest/config.json")

    # Try env vars first, then config file
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        try:
            with open(config_path) as f:
                config = json.load(f)
            token = token or config.get("telegram_bot_token", "")
            chat_id = chat_id or config.get("telegram_chat_id", "")
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    if not token or not chat_id:
        print("Error: telegram_bot_token and telegram_chat_id required", file=sys.stderr)
        print("Run /digest setup or set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars", file=sys.stderr)
        sys.exit(1)

    message_file = sys.argv[1] if len(sys.argv) > 1 else "/dev/stdin"
    with open(message_file) as f:
        message = f.read()
    send_message(token, chat_id, message)
