import re
import sys
import time
from pathlib import Path

import requests

API_URL = "https://en.wikipedia.org/w/api.php"
RAW_DIR = Path("data/raw/wikipedia")
USER_AGENT = (
    "rugby-predictor/0.1 "
    "(personal portfolio project; https://github.com/aidancorless-boop/rugby--predictor)"
)


def safe_filename(title: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", title).strip("_") + ".wikitext"


def fetch_wikitext(title: str, refresh: bool = False) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / safe_filename(title)
    if out.exists() and not refresh:
        print(f"Using cached {out}")
        return out
    resp = requests.get(
        API_URL,
        params={
            "action": "parse",
            "page": title,
            "prop": "wikitext",
            "format": "json",
            "formatversion": 2,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Wikipedia error for {title!r}: {data['error']}")
    out.write_text(data["parse"]["wikitext"], encoding="utf-8")
    print(f"Saved {out} ({out.stat().st_size} bytes)")
    time.sleep(2)  # be polite if this is called in a loop
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python -m src.ingest.wikipedia_fetch "Page title" [--refresh]')
        sys.exit(1)
    fetch_wikitext(sys.argv[1], refresh="--refresh" in sys.argv)
