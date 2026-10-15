#!/usr/bin/env python3
"""Footballer wave taken from the editorial bank, reviewed with JERV before it reaches the app.

prepare:  bank footballers with the data the Futebol questions need -> Wikidata harvest and the
          200-character derivation -> one JERV claim per person ("é jogador de futebol profissional")
          with the Wikipedia summary as the source excerpt. Writes docs/content/bank-futebol-pool.json
          and docs/content/jerv-bank-futebol-input.json.
finalize: keeps only the people whose main-role claim JERV accepted (supports, confidence >= 0.8),
          writes the batch read by build_character_expansion.py, adds their source entries and their
          claim reviews, and lists the people JERV did not accept in bank-futebol-jerv-excluded.json.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_character_expansion as builder  # noqa: E402  (the app's own assembly, used to check distinguishability)
import derive_character_batch_200 as derive  # noqa: E402  (same football derivation as the 200-character batch)
import harvest_wikidata_candidates as harvest  # noqa: E402

BANK_PATH = ROOT / "novos personagens/personagens-candidatos.json"
CACHE_DIR = ROOT / "novos personagens/.cache"
CLAIMS_CACHE = CACHE_DIR / "claims-clubes-posicoes.json"
TITLES_CACHE = CACHE_DIR / "titulos-wikipedia.json"
EXTRACT_CACHE = CACHE_DIR / "extratos-wikipedia-futebol.json"
KNOWLEDGE_PATHS = (
    ROOT / "iosApp/Resources/KnowledgeBase/knowledge.json",
    ROOT / "iosApp/Resources/KnowledgeBase/character-expansion.json",
)
POOL_PATH = ROOT / "docs/content/bank-futebol-pool.json"
JERV_INPUT_PATH = ROOT / "docs/content/jerv-bank-futebol-input.json"
JERV_REPORT_PATH = ROOT / "docs/content/jerv-bank-futebol-report.json"
JERV_FINAL_PATH = ROOT / "docs/content/jerv-character-review-final.json"
SOURCES_PATH = ROOT / "docs/content/character-sources.json"
EXCLUDED_PATH = ROOT / "docs/content/bank-futebol-jerv-excluded.json"
BATCH_PATH = ROOT / "scripts/character-batch-bank-futebol.json"
CHAMPIONS_PATH = ROOT / "docs/content/world-cup-champion-squads.json"

CATEGORY = "Futebol"
LICENSE = "CC BY-SA 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
JERV_MIN_CONFIDENCE = 0.8
FOOTBALL_TERMS = ("futebol", "football", "soccer", "futebolista", "footballer")
BLOCKING_PREFIXES = ("fortune500", "identidade", "sem-artigo", "sem-ano", "categoria-sem")
FOOTBALL_KEYS = [
    "goalkeeper", "midfielder", "forward", "ballon_dor", "played_barcelona", "brazil_team",
    "played_premier_league", "played_in_europe", "world_cup_winner", "born_before_1985",
    "played_in_brazil", "played_in_italy", "played_in_spain", "played_in_germany",
    "played_in_france", "played_in_portugal", "fifa_best",
]
USER_AGENT = {"User-Agent": "QuemSouEuCharacterBank/1.0 (footballer wave; https://github.com/socialbot114-cell/quem-sou-eu-adivinha)"}


def today() -> str:
    return date.today().isoformat()


def normalize_text(text: str) -> str:
    return harvest.normalize(text)


def app_names() -> set[str]:
    names: set[str] = set()
    for path in KNOWLEDGE_PATHS:
        for person in json.loads(path.read_text(encoding="utf-8"))["people"]:
            names.add(normalize_text(person["name"]))
    return names


def is_footballer(record: dict) -> bool:
    footballer = record.get("answers", {}).get("footballer", {}).get("answer") == "Sim"
    occupations = " ".join((record.get("facts") or {}).get("occupations", [])).lower()
    return footballer or "futebolista" in occupations or "jogador de futebol" in occupations


def is_blocked(record: dict) -> bool:
    return any(str(blocker).startswith(BLOCKING_PREFIXES) for blocker in record.get("bloqueios") or [])


def http_json(url: str, attempts: int = 5) -> dict | None:
    request = urllib.request.Request(url, headers=USER_AGENT)
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                time.sleep(0.3)  # be polite to the public endpoints
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            if error.code != 429 or attempt == attempts - 1:
                raise
            time.sleep(30 * (attempt + 1))  # rate limited: back off well beyond the usual retry delay
        except urllib.error.URLError:
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)
    return None


def fetch_extract(qid: str, titles: dict) -> dict | None:
    """Wikipedia summary (pt, then en) for the person, used as the source excerpt."""
    for site, lang in (("ptwiki", "pt"), ("enwiki", "en")):
        title = titles.get(qid, {}).get(site)
        if not title:
            continue
        slug = urllib.parse.quote(title.replace(" ", "_"))
        data = http_json(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{slug}")
        if data and data.get("extract"):
            return {"lang": lang, "title": title, "url": f"https://{lang}.wikipedia.org/wiki/{slug}", "extract": data["extract"]}
    return None


def load_extracts(qids: list[str], titles: dict) -> dict[str, dict | None]:
    """Sequential and cached as it goes, so a rate-limited run keeps what it already fetched."""
    cache = json.loads(EXTRACT_CACHE.read_text(encoding="utf-8")) if EXTRACT_CACHE.is_file() else {}
    missing = [qid for qid in qids if qid not in cache]
    for done, qid in enumerate(missing, start=1):
        cache[qid] = fetch_extract(qid, titles)
        if done % 25 == 0 or done == len(missing):
            EXTRACT_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(f"resumos: {done}/{len(missing)}", flush=True)
    return {qid: cache.get(qid) for qid in qids}


def usable(record: dict) -> bool:
    return derive.birth_year(record) is not None and derive.gender_of(record) is not None and derive.country_of(record) is not None


def existing_signatures() -> set[tuple]:
    signatures: set[tuple] = set()
    for path in KNOWLEDGE_PATHS:
        for person in json.loads(path.read_text(encoding="utf-8"))["people"]:
            if CATEGORY in person["categories"]:
                signatures.add(tuple(person["attributes"].get(key) for key in FOOTBALL_KEYS))
    return signatures


def champion_status(qid: str, titles: dict, champions: set[str]) -> int | None:
    """1 if the article is linked in a winning World Cup squad, 0 if it is not (all winning squads were read),
    None when there is no English article to match against the squads."""
    article = titles.get(qid, {}).get("enwiki")
    if not article:
        return None
    return int(article in champions)


def claim_for(person: dict, extract: dict) -> dict:
    return {
        "id": f"{person['id']}-main-role",
        "person_id": person["id"],
        "person_name": person["name"],
        # Same question the app asks ("É do futebol?"): played or plays professionally, so retired players count.
        "claim": f"{person['name']} jogou ou joga futebol profissionalmente.",
        "source_url": extract["url"],
        "source_title": extract["title"],
        "source_excerpt": extract["extract"],
        "source_license": LICENSE,
        "source_license_url": LICENSE_URL,
        "last_verified": today(),
        "answer": 1,
    }


def prepare() -> None:
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))["candidates"]
    titles = json.loads(TITLES_CACHE.read_text(encoding="utf-8"))
    claims = json.loads(CLAIMS_CACHE.read_text(encoding="utf-8"))
    taken = app_names()

    by_qid: dict[str, dict] = {}
    for record in bank:
        qid = record["wikidata"]["id"]
        if not is_footballer(record) or is_blocked(record) or normalize_text(record["name"]) in taken:
            continue
        if (record.get("facts") or {}).get("birthYear") is None:
            continue
        cached = claims.get(qid, {"clubs": [], "positions": []})
        if not cached["clubs"] or not cached["positions"]:
            continue
        by_qid[qid] = record
    print(f"candidatos com dados de futebol: {len(by_qid)}")

    extracts = load_extracts(list(by_qid), titles)
    with_text = {qid: record for qid, record in by_qid.items()
                 if extracts.get(qid) and any(term in extracts[qid]["extract"].lower() for term in FOOTBALL_TERMS)}
    print(f"com resumo da Wikipédia citando futebol: {len(with_text)}")

    report = harvest.harvest([{"name": record["name"], "qid": qid, "categories": [CATEGORY]} for qid, record in with_text.items()])
    print(f"harvest: {len(report['records'])} encontrados, {len(report['skipped'])} ignorados")
    records = [record for record in report["records"] if usable(record)]
    clubs = derive.club_lookup(records)

    champions = set(json.loads(CHAMPIONS_PATH.read_text(encoding="utf-8"))["champions"])
    seen = existing_signatures()
    pool: list[dict] = []
    dropped = {"dados-incompletos": 0, "indistinguivel": 0}
    for record in sorted(records, key=lambda item: by_qid[item["qid"]]["priorityRank"]):
        entry, _ = derive.football_entry(record, clubs)
        # Copa do Mundo comes from the official champion squads, not from the curated list.
        entry["attributes"]["world_cup_winner"] = champion_status(record["qid"], titles, champions)
        # Only the Copa attribute may stay empty (the batch builder omits it); a missing trait would break coverage.
        if any(entry["attributes"].get(key) is None for key in FOOTBALL_KEYS if key != "world_cup_winner"):
            dropped["dados-incompletos"] += 1
            continue
        signature = tuple(entry["attributes"].get(key) for key in FOOTBALL_KEYS)
        if signature in seen:
            dropped["indistinguivel"] += 1
            continue
        seen.add(signature)
        extract = extracts[record["qid"]]
        pool.append({
            "entry": entry,
            "qid": record["qid"],
            "source": {
                "id": entry["id"], "name": entry["name"], "profession": entry["profession"],
                "sourceTitle": extract["title"], "sourceURL": extract["url"], "sourceExcerpt": extract["extract"],
                "sourceLicense": LICENSE, "sourceLicenseURL": LICENSE_URL, "lastVerified": today(),
            },
            "claim": claim_for(entry, extract),
        })
    POOL_PATH.write_text(json.dumps({"generatedAt": today(), "category": CATEGORY, "people": pool}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    JERV_INPUT_PATH.write_text(json.dumps({"questions": [], "claims": [item["claim"] for item in pool]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"pool: {len(pool)} pessoas (descartadas: {dropped})")
    print(f"entrada JERV: {JERV_INPUT_PATH}")


def refresh_claims() -> None:
    """Rewrites the claims of an existing pool, keeping the sources, so JERV reviews the current wording."""
    data = json.loads(POOL_PATH.read_text(encoding="utf-8"))
    for item in data["people"]:
        source = item["source"]
        extract = {"title": source["sourceTitle"], "url": source["sourceURL"], "extract": source["sourceExcerpt"]}
        item["claim"] = claim_for(item["entry"], extract)
    POOL_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    JERV_INPUT_PATH.write_text(json.dumps({"questions": [], "claims": [item["claim"] for item in data["people"]]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"claims reescritas: {len(data['people'])}")


def finalize(limit: int | None = None) -> None:
    pool = json.loads(POOL_PATH.read_text(encoding="utf-8"))["people"]
    report = json.loads(JERV_REPORT_PATH.read_text(encoding="utf-8"))
    reviews = report["claim_reviews"]
    final = json.loads(JERV_FINAL_PATH.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    known_sources = {item["id"] for item in sources["items"]}

    accepted, excluded = [], []
    for item in pool:
        person_id = item["entry"]["id"]
        review = reviews.get(item["claim"]["id"], {})
        if not (review.get("status") == "accepted" and review.get("decision") == "supports" and review.get("confidence", 0) >= JERV_MIN_CONFIDENCE):
            excluded.append({"id": person_id, "name": item["entry"]["name"], "motivo": "JERV não aceitou a afirmação principal",
                             "decision": review.get("decision"), "confidence": review.get("confidence")})
        elif item["entry"]["attributes"].get("world_cup_winner") is None:
            # The validator needs 80% coverage for this question, and a missing title is not a "no": without
            # the official squads we cannot tell a non-champion from an unknown one, so the person waits.
            excluded.append({"id": person_id, "name": item["entry"]["name"], "motivo": "Copa do Mundo sem status verificado"})
        else:
            accepted.append(item)

    if limit is not None and len(accepted) > limit:
        # Size chosen by the gameplay gate (evaluate_gameplay.py): larger waves lower the accuracy of the game.
        excluded += [{"id": item["entry"]["id"], "name": item["entry"]["name"], "motivo": f"fora do limite do portão de jogo ({limit})"}
                     for item in accepted[limit:]]
        accepted = accepted[:limit]
    write_batch(accepted)
    dropped = drop_indistinguishable([item["entry"]["id"] for item in accepted])
    kept = [item for item in accepted if item["entry"]["id"] not in dropped]
    write_batch(kept)
    excluded += [{"id": item["entry"]["id"], "name": item["entry"]["name"], "motivo": "indistinguível pela regra do validador"}
                 for item in accepted if item["entry"]["id"] in dropped]

    for item in kept:
        if item["source"]["id"] not in known_sources:
            # The content validator rejects surrounding spaces and empty fields.
            source = {key: value.strip() if isinstance(value, str) else value for key, value in item["source"].items()}
            sources["items"].append(source)
        review = reviews[item["claim"]["id"]]
        final["claim_reviews"][item["claim"]["id"]] = {
            "decision": review["decision"],
            "confidence": review["confidence"],
            "status": review["status"],
            "source_url": item["claim"]["source_url"],
            "source_license": LICENSE,
            "source_license_url": LICENSE_URL,
            "last_verified": item["claim"]["last_verified"],
            "final_status": "accepted",
            "review_method": "jerv-automatico",
        }
    final["final_summary"]["claims_accepted"] = sum(item["final_status"] == "accepted" for item in final["claim_reviews"].values())
    sources["generatedAt"] = today()
    SOURCES_PATH.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    JERV_FINAL_PATH.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    EXCLUDED_PATH.write_text(json.dumps({"generatedAt": today(), "excluded": excluded}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"aceitos pelo JERV: {len(accepted)} | removidos por indistinguibilidade: {len(dropped)} | no lote: {len(kept)}")
    print(f"não aceitos: {len(pool) - len(accepted)} | lista: {EXCLUDED_PATH}")


def write_batch(items: list[dict]) -> None:
    BATCH_PATH.write_text(json.dumps({"people": {CATEGORY: [item["entry"] for item in items]}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validator_signatures(people: list[dict], questions: list[dict]) -> tuple[list[str], list[str]]:
    """The traits content validation compares: useful Futebol questions, and every trait for the "Todos" mode."""
    candidates = [person for person in people if CATEGORY in person["categories"]]
    useful = []
    for question in questions:
        if "Todos" not in question["categories"] and CATEGORY not in question["categories"]:
            continue
        attribute = question["attribute"]
        values = [person["attributes"][attribute] for person in candidates if attribute in person["attributes"]]
        if len(values) / len(candidates) >= 0.8 and len(set(values)) > 1:
            useful.append(attribute)
    return useful, [question["attribute"] for question in questions]


def drop_indistinguishable(new_ids: list[str]) -> dict[str, str]:
    """Drops new footballers that the validator would call indistinguishable, using the real builder output.

    Existing characters are never dropped; among equal signatures the earlier one (priority order) stays.
    """
    dropped: dict[str, str] = {}
    primary = json.loads(builder.PRIMARY.read_text(encoding="utf-8"))
    for _ in range(6):
        result = builder.build()
        # The validator reads the base characters and questions as well as the expansion.
        people = primary["people"] + result["people"]
        questions = primary["questions"] + result["questions"]
        useful, everything = validator_signatures(people, questions)
        found = False
        for attributes, label in ((useful, "Futebol"), (everything, "Todos")):
            groups: dict[tuple, list[str]] = {}
            for person in people:
                if label == "Futebol" and CATEGORY not in person["categories"]:
                    continue
                key = tuple(person["attributes"].get(attribute) for attribute in attributes)
                groups.setdefault(key, []).append(person["id"])
            for ids in groups.values():
                for identifier in ids[1:]:
                    if identifier in new_ids and identifier not in dropped:
                        dropped[identifier] = label
                        found = True
                    elif identifier not in new_ids:
                        raise SystemExit(f"colisão com personagem existente: {ids}")
        if not found:
            break
        remaining = [identifier for identifier in new_ids if identifier not in dropped]
        batch = json.loads(BATCH_PATH.read_text(encoding="utf-8"))
        batch["people"][CATEGORY] = [entry for entry in batch["people"][CATEGORY] if entry["id"] not in dropped]
        BATCH_PATH.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        new_ids = remaining
    return dropped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=("prepare", "refresh-claims", "finalize"))
    parser.add_argument("--limit", type=int, default=None, help="largest wave the gameplay gate accepts (finalize only)")
    args = parser.parse_args()
    if args.stage == "finalize":
        finalize(args.limit)
    else:
        {"prepare": prepare, "refresh-claims": refresh_claims}[args.stage]()


if __name__ == "__main__":
    main()
