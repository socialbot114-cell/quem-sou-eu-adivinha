#!/usr/bin/env python3
"""Fetch dated encyclopedic source excerpts for the expansion's identity facts."""
from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).parents[1]
EXPANSION_PATH = ROOT / "iosApp/Resources/KnowledgeBase/character-expansion.json"
OUTPUT_PATH = ROOT / "docs/content/character-sources.json"
TITLE_OVERRIDES = {
    "beyonce": "Beyoncé",
    "v-kim-taehyung": "V (singer)",
    "jin-bts": "Jin (singer)",
    "rm-bts": "RM (rapper)",
    "rose-blackpink": "Rosé (singer)",
    "lisa-blackpink": "Lisa (rapper)",
    "jennie-blackpink": "Jennie (singer)",
    "iu": "IU (singer)",
    "drake": "Drake (musician)",
    "djavan": "Djavan",
    "the-weeknd": "The Weeknd",
    "lebron-james": "LeBron James",
    "stephen-curry": "Stephen Curry",
    "timothee-chalamet": "Timothée Chalamet",
    "gisele-bundchen": "Gisele Bündchen",
}
USER_AGENT = "QuemSouEuContentReview/1.0 (https://github.com/socialbot114-cell/quem-sou-eu-adivinha)"
WIKIPEDIA_TEXT_LICENSE = "CC BY-SA 4.0"
WIKIPEDIA_TEXT_LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"


def fetch_summary(title: str) -> dict:
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(title.replace(" ", "_"), safe="()')")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=45) as response:
        data = json.load(response)
    if data.get("type") != "standard" or not data.get("extract"):
        raise ValueError(f"no article summary for {title!r}")
    return {
        "sourceTitle": data.get("title", title),
        "sourceURL": data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"),
        "sourceExcerpt": data["extract"],
        "sourceRevision": data.get("revision"),
        "sourceLicense": WIKIPEDIA_TEXT_LICENSE,
        "sourceLicenseURL": WIKIPEDIA_TEXT_LICENSE_URL,
    }


def main() -> None:
    people = json.loads(EXPANSION_PATH.read_text(encoding="utf-8"))["people"]
    cached_items = {}
    if OUTPUT_PATH.is_file():
        try:
            current = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
            cached_items = {item["id"]: item for item in current.get("items", []) if item.get("sourceExcerpt")}
        except (OSError, json.JSONDecodeError, TypeError, KeyError):
            cached_items = {}
    items = []
    failures = []
    for person in people:
        cached = cached_items.get(person["id"])
        if cached and cached.get("name") == person["name"]:
            items.append({
                **cached,
                "profession": person["profession"],
                "sourceLicense": cached.get("sourceLicense", WIKIPEDIA_TEXT_LICENSE),
                "sourceLicenseURL": cached.get("sourceLicenseURL", WIKIPEDIA_TEXT_LICENSE_URL),
            })
            continue
        title = TITLE_OVERRIDES.get(person["id"], person["name"])
        try:
            source = fetch_summary(title)
            items.append({
                "id": person["id"],
                "name": person["name"],
                "profession": person["profession"],
                **source,
                "lastVerified": date.today().isoformat(),
            })
        except (HTTPError, OSError, ValueError) as error:
            failures.append({"id": person["id"], "name": person["name"], "title": title, "error": str(error)})
        time.sleep(0.5)

    if failures:
        print(f"Source refresh incomplete ({len(failures)} unresolved); existing complete manifest was preserved.")
        for item in failures:
            print(f"- {item['id']} ({item['title']}): {item['error']}")
        raise SystemExit(1)
    report = {"schemaVersion": 1, "generatedAt": date.today().isoformat(), "items": items}
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(items)} source excerpts; unresolved: {len(failures)}")


if __name__ == "__main__":
    main()
