"""
Fetch URL content as plain text for Discovery Chat context.
Uses stdlib only (urllib). HTML is stripped to approximate text.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from typing import Tuple

# Timeout and size limits
_TIMEOUT_SEC = 15
_MAX_BYTES = 600_000
_MAX_TEXT_CHARS = 20_000


def fetch_url_text(url: str) -> Tuple[str, str | None]:
    """
    Fetch URL and return (text, None) on success or ("", error_message) on failure.
    Text is truncated to _MAX_TEXT_CHARS. HTML tags are stripped.
    """
    if not url or not url.strip().lower().startswith(("http://", "https://")):
        return "", "Ungültige URL."
    url = url.strip()
    # Browser-like headers to reduce 403 from sites that block simple bots
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SEC) as resp:
            if resp.length and resp.length > _MAX_BYTES:
                body = resp.read(_MAX_BYTES)
            else:
                body = resp.read(_MAX_BYTES)
            content_type = (resp.headers.get_content_type() or "").lower()
    except urllib.error.HTTPError as e:
        return "", f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return "", str(e.reason) if e.reason else str(e)
    except TimeoutError:
        return "", "Zeitüberschreitung"
    except Exception as e:
        return "", str(e)

    try:
        raw = body.decode("utf-8", errors="replace")
    except Exception:
        return "", "Seite konnte nicht als Text gelesen werden."

    if "html" in content_type or "<" in raw[:2000]:
        text = _strip_html(raw)
    else:
        text = raw

    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > _MAX_TEXT_CHARS:
        text = text[:_MAX_TEXT_CHARS] + "\n… (gekürzt)"
    return text, None


def _strip_html(html: str) -> str:
    """Remove script/style, then tags; collapse whitespace."""
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"&amp;", "&", html, flags=re.IGNORECASE)
    html = re.sub(r"&lt;", "<", html, flags=re.IGNORECASE)
    html = re.sub(r"&gt;", ">", html, flags=re.IGNORECASE)
    html = re.sub(r"&quot;", '"', html, flags=re.IGNORECASE)
    html = re.sub(r"\s+", " ", html)
    return html.strip()
