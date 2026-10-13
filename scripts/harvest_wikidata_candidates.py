#!/usr/bin/env python3
"""Harvest objective facts for candidate characters from Wikidata.

Input: a JSON list of candidates:
  {"name": "...", "categories": [...], "search": "optional text",
   "qid": "optional", "expect": ["optional occupation keyword", ...],
   "requireBrazilian": false, "id": "existing character id", "allowExisting": false}

- "search" overrides the text used for the lookup (for ambiguous names).
- "qid" pins the item and skips the lookup.
- "expect" keeps only human hits whose occupations (pt labels) contain one of the keywords,
  so a footballer and a philosopher with the same name are told apart.
- "requireBrazilian" keeps only hits with Brazilian citizenship.

Output: one record per candidate with the matched item, its claims and the Wikidata
URL used as the source reference. Candidates that match an existing character, or
that cannot be matched, are reported and skipped.
"""

from __future__ import annotations

import argparse
import json
import time
import unicodedata
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).parents[1]
KNOWLEDGE_PATHS = (
    ROOT / "iosApp/Resources/KnowledgeBase/knowledge.json",
    ROOT / "iosApp/Resources/KnowledgeBase/character-expansion.json",
)
USER_AGENT = "quem-sou-eu-catalog/1.0 (https://github.com/socialbot114-cell/quem-sou-eu-adivinha)"
API = "https://www.wikidata.org/w/api.php"
HUMAN = "Q5"
BRAZIL = "Q155"

# Properties read from each item. Only these become evidence.
PROPERTIES = ("P21", "P27", "P569", "P570", "P106", "P54", "P413", "P136", "P463", "P166", "P1344", "P19")


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower().strip()


BATCH_200_PATH = ROOT / "scripts/character-batch-200.json"


def existing_names() -> set[str]:
    """Names already in the app. The 200-character batch is generated from these harvests,
    so its own names are not treated as existing when harvesting again."""
    generated: set[str] = set()
    if BATCH_200_PATH.is_file():
        for people in json.loads(BATCH_200_PATH.read_text(encoding="utf-8"))["people"].values():
            generated.update(normalize(person["name"]) for person in people)
    names: set[str] = set()
    for path in KNOWLEDGE_PATHS:
        for person in json.loads(path.read_text(encoding="utf-8"))["people"]:
            if normalize(person["name"]) not in generated:
                names.add(normalize(person["name"]))
    return names


def get_json(params: dict[str, str], attempts: int = 6) -> dict:
    request = Request(f"{API}?{urlencode({**params, 'format': 'json'})}", headers={"User-Agent": USER_AGENT})
    for attempt in range(attempts):
        try:
            with urlopen(request, timeout=30) as response:
                time.sleep(0.5)  # be polite to the public endpoint
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code != 429 or attempt == attempts - 1:
                raise
            time.sleep(30 * (attempt + 1))  # rate limited: back off and retry
    raise RuntimeError("unreachable")


NOMINATION_QUALIFIER = "P1411"  # "nominated for": an award nomination, not an award won


def claim_values(claims: dict, prop: str) -> list[str | dict]:
    values = []
    for claim in claims.get(prop, []):
        if NOMINATION_QUALIFIER in claim.get("qualifiers", {}):
            continue
        datavalue = claim.get("mainsnak", {}).get("datavalue", {})
        value = datavalue.get("value")
        if isinstance(value, dict) and "id" in value:
            values.append(value["id"])
        elif isinstance(value, dict) and "time" in value:
            values.append({"time": value["time"], "precision": value.get("precision")})
    return values


def resolve_labels(qids: set[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    ordered = sorted(qids)
    for start in range(0, len(ordered), 50):
        chunk = ordered[start:start + 50]
        data = get_json({"action": "wbgetentities", "ids": "|".join(chunk), "props": "labels", "languages": "pt|en"})
        for qid, entity in data["entities"].items():
            label = entity.get("labels", {})
            labels[qid] = (label.get("pt") or label.get("en") or {}).get("value", qid)
    return labels


def find_item(candidate: dict) -> tuple[str | None, dict | None, str]:
    """Return (qid, entity, reason). reason explains why nothing matched."""
    if candidate.get("qid"):
        qid = candidate["qid"]
    else:
        text = candidate.get("search") or candidate["name"]
        hits = get_json({"action": "wbsearchentities", "search": text, "language": "pt", "type": "item", "limit": "8"})
        qids = [hit["id"] for hit in hits.get("search", [])]
        if not qids:
            return None, None, "sem resultado no Wikidata"
        entities = get_json({"action": "wbgetentities", "ids": "|".join(qids), "props": "claims|labels", "languages": "pt|en"})["entities"]
        occupation_qids = {
            value
            for qid_ in qids
            for value in claim_values(entities.get(qid_, {}).get("claims", {}), "P106")
            if isinstance(value, str)
        }
        occupation_labels = resolve_labels(occupation_qids) if occupation_qids else {}
        expect = [keyword.lower() for keyword in candidate.get("expect", [])]
        humans = []
        for qid_ in qids:
            claims = entities.get(qid_, {}).get("claims", {})
            if HUMAN not in [value for value in claim_values(claims, "P31") if isinstance(value, str)]:
                continue
            humans.append(qid_)
            occupations = [occupation_labels.get(value, "").lower() for value in claim_values(claims, "P106") if isinstance(value, str)]
            if expect and not any(keyword in occupation for keyword in expect for occupation in occupations):
                continue
            if candidate.get("requireBrazilian") and BRAZIL not in claim_values(claims, "P27"):
                continue
            return qid_, entities[qid_], ""
        if not humans:
            return None, None, "nenhum item humano na busca"
        return None, None, "nenhum item humano com a ocupação esperada" if expect else "nenhum item brasileiro"

    entity = get_json({"action": "wbgetentities", "ids": qid, "props": "claims|labels", "languages": "pt|en"})["entities"][qid]
    return qid, entity, ""


def harvest(candidates: list[dict]) -> dict:
    skipped = []
    records = []
    existing = existing_names()
    for candidate in candidates:
        name = candidate["name"]
        if normalize(name) in existing and not candidate.get("allowExisting"):
            skipped.append({"name": name, "reason": "já existe na base"})
            continue
        qid, entity_data, reason = find_item(candidate)
        if qid is None:
            skipped.append({"name": name, "reason": reason})
            continue
        claims = entity_data.get("claims", {})
        records.append({
            "id": candidate.get("id"),
            "name": name,
            "qid": qid,
            "sourceUrl": f"https://www.wikidata.org/wiki/{qid}",
            "label": (entity_data.get("labels", {}).get("pt") or entity_data.get("labels", {}).get("en") or {}).get("value", name),
            "categories": candidate.get("categories", []),
            "claims": {prop: claim_values(claims, prop) for prop in PROPERTIES},
        })

    needed = {
        value
        for record in records
        for values in record["claims"].values()
        for value in values
        if isinstance(value, str)
    }
    labels = resolve_labels(needed)
    for record in records:
        record["claimLabels"] = {
            prop: [labels.get(value, value) if isinstance(value, str) else value for value in values]
            for prop, values in record["claims"].items()
        }
    return {"records": records, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON list of candidates")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    candidates = json.loads(args.input.read_text(encoding="utf-8"))
    report = harvest(candidates)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(report['records'])} encontrados, {len(report['skipped'])} ignorados -> {args.output}")


if __name__ == "__main__":
    main()
