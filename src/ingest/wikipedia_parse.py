import argparse
import csv
import re
from datetime import datetime
from pathlib import Path

from src.ingest.wikipedia_fetch import fetch_wikitext

CSV_COLUMNS = [
    "date", "season", "competition", "stage",
    "home_team", "away_team", "home_score", "away_score",
    "neutral", "source",
]

FIELD_RE = re.compile(r"^\|\s*(\w+)\s*=\s*(.*)$")
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
SCORE_RE = re.compile(r"(\d+)\s*[–—−-]\s*(\d+)")


def extract_blocks(text: str) -> list[str]:
    """Return every {{rugbybox ...}} block, matching braces so nested
    templates like {{flagicon|ENG}} don't end the block early."""
    blocks = []
    start_re = re.compile(r"\{\{\s*rugbybox\b", re.IGNORECASE)
    pos = 0
    while True:
        m = start_re.search(text, pos)
        if not m:
            break
        depth = 0
        i = m.start()
        while i < len(text):
            if text.startswith("{{", i):
                depth += 1
                i += 2
            elif text.startswith("}}", i):
                depth -= 1
                i += 2
                if depth == 0:
                    break
            else:
                i += 1
        blocks.append(text[m.start():i])
        pos = i
    return blocks


def block_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.splitlines():
        m = FIELD_RE.match(line.strip())
        if m:
            fields.setdefault(m.group(1).lower(), m.group(2).strip())
    return fields


def clean_team(raw: str) -> str:
    raw = re.sub(r"\{\{[^{}]*\}\}", "", raw)          # flag templates
    raw = re.sub(r"\(\s*\d+\s*BP\s*\)", "", raw)      # bonus point markers
    m = LINK_RE.search(raw)
    if m:
        name = m.group(2) or m.group(1)
    else:
        name = re.sub(r"<[^>]+>", "", raw)
    return name.strip()


def parse_score(raw: str):
    m = SCORE_RE.search(raw or "")
    if not m:
        return None, None  # unplayed fixture ("v", blank, etc.)
    return int(m.group(1)), int(m.group(2))


def parse_date(raw: str) -> str:
    cleaned = re.sub(r"<[^>]+>|\[\[|\]\]", "", raw).strip()
    try:
        return datetime.strptime(cleaned, "%d %B %Y").date().isoformat()
    except ValueError:
        raise ValueError(f"Could not parse date {raw!r} (expected e.g. '6 December 2025')")


def parse_matches(text: str, season: str, competition: str,
                  stage: str = "Pool", neutral: bool = False,
                  source: str = "wikipedia") -> list[dict]:
    rows = []
    for block in extract_blocks(text):
        f = block_fields(block)
        missing = [k for k in ("date", "home", "away") if k not in f]
        if missing:
            raise ValueError(f"rugbybox block missing {missing}: {block[:150]!r}")
        home, away = clean_team(f["home"]), clean_team(f["away"])
        if not home or not away:
            raise ValueError(f"Could not read team names from: {block[:150]!r}")
        home_score, away_score = parse_score(f.get("score", ""))
        rows.append({
            "date": parse_date(f["date"]),
            "season": season,
            "competition": competition,
            "stage": stage,
            "home_team": home,
            "away_team": away,
            "home_score": "" if home_score is None else home_score,
            "away_score": "" if away_score is None else away_score,
            "neutral": 1 if neutral else 0,
            "source": source,
        })
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(description="Convert a Wikipedia results page to importer CSV")
    p.add_argument("title", help="Wikipedia page title")
    p.add_argument("--season", required=True, help='e.g. "2025-26"')
    p.add_argument("--competition", required=True, help='e.g. "Champions Cup"')
    p.add_argument("--stage", default="Pool")
    p.add_argument("--neutral", action="store_true", help="matches are at neutral venues")
    p.add_argument("--refresh", action="store_true", help="re-download the page")
    args = p.parse_args()

    wikitext_path = fetch_wikitext(args.title, refresh=args.refresh)
    rows = parse_matches(
        wikitext_path.read_text(encoding="utf-8"),
        season=args.season, competition=args.competition,
        stage=args.stage, neutral=args.neutral,
    )
    out = wikitext_path.with_suffix(".csv")
    write_csv(rows, out)
    played = sum(1 for r in rows if r["home_score"] != "")
    print(f"Parsed {len(rows)} matches ({played} played, {len(rows) - played} upcoming) -> {out}")


if __name__ == "__main__":
    main()
