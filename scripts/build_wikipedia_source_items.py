#!/usr/bin/env python3
"""Create editorial source items for the 200-character batch from Wikipedia lead sections.

Each new character gets the Wikipedia article linked to its Wikidata item (pt first, then en),
with the lead paragraph as the excerpt. Items are appended to docs/content/character-sources.json
unless they already exist there, so the validator sees one source per expansion character.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).parents[1]
BATCH = ROOT / "scripts/character-batch-200.json"
SOURCES = ROOT / "docs/content/character-sources.json"
SOURCES_200 = ROOT / "docs/content/character-sources-200.json"
USER_AGENT = "quem-sou-eu-catalog/1.0 (https://github.com/socialbot114-cell/quem-sou-eu-adivinha)"
LICENSE = "CC BY-SA 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
EXCERPT_LIMIT = 700


def get_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urlopen(request, timeout=30) as response:
                time.sleep(0.3)
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            if attempt == 4:
                raise
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("unreachable")


def sitelinks(qids: list[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for start in range(0, len(qids), 50):
        chunk = qids[start:start + 50]
        url = "https://www.wikidata.org/w/api.php?" + urlencode({
            "action": "wbgetentities", "ids": "|".join(chunk), "props": "sitelinks", "format": "json",
        })
        for qid, entity in get_json(url)["entities"].items():
            links = entity.get("sitelinks", {})
            result[qid] = {site: links[site]["title"] for site in ("ptwiki", "enwiki") if site in links}
    return result


def summary(language: str, title: str) -> dict:
    url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}"
    return get_json(url)


def main() -> None:
    batch = json.loads(BATCH.read_text(encoding="utf-8"))["people"]
    people = [person for category in batch.values() for person in category]
    qid_by_id = {item["id"]: item for item in json.loads(SOURCES_200.read_text(encoding="utf-8"))["characters"]}
    links = sitelinks([qid_by_id[person["id"]]["qid"] for person in people])

    document = json.loads(SOURCES.read_text(encoding="utf-8"))
    current_ids = {person["id"] for person in people}
    # Drop sources generated for characters that left the batch; the original items are untouched.
    generated = {item["id"] for item in json.loads(SOURCES_200.read_text(encoding="utf-8"))["characters"]}
    document["items"] = [item for item in document["items"] if item["id"] not in generated or item["id"] in current_ids]
    existing = {item["id"] for item in document["items"]}
    today = date.today().isoformat()
    added, missing = [], []
    for person in people:
        if person["id"] in existing:
            continue
        titles = links.get(qid_by_id[person["id"]]["qid"], {})
        page = None
        for site, language in (("ptwiki", "pt"), ("enwiki", "en")):
            if site in titles:
                try:
                    page = (language, titles[site], summary(language, titles[site]))
                    break
                except Exception:
                    page = None
        if page is None:
            missing.append(person["name"])
            continue
        language, title, data = page
        excerpt = (data.get("extract") or "").strip()
        if not excerpt:
            missing.append(person["name"])
            continue
        if len(excerpt) > EXCERPT_LIMIT:
            excerpt = excerpt[:EXCERPT_LIMIT].rsplit(" ", 1)[0] + "…"
        url = data.get("content_urls", {}).get("desktop", {}).get("page") or f"https://{language}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
        document["items"].append({
            "id": person["id"],
            "name": person["name"],
            "profession": person["profession"],
            "sourceTitle": data.get("title", title),
            "sourceURL": url,
            "sourceExcerpt": excerpt,
            "lastVerified": today,
            "sourceLicense": LICENSE,
            "sourceLicenseURL": LICENSE_URL,
        })
        added.append(person["id"])
    document["generatedAt"] = today
    SOURCES.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"adicionadas: {len(added)}  sem artigo/resumo: {len(missing)}")
    if missing:
        print("sem fonte:", missing)


if __name__ == "__main__":
    main()
