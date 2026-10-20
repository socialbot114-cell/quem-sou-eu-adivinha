#!/usr/bin/env python3
"""Animals category: birds and mammals described by EltonTraits 1.0 traits and Wikidata conservation status.

Every character answers the same yes/no questions, and each answer is a value from a dataset row:
- diet: EltonTraits Diet-* shares in percent; "principalmente" means at least 50%
- body mass: EltonTraits BodyMass-Value in grams, split into five thresholds
- nocturnal: Nocturnal (birds) or Activity-Nocturnal (mammals)
- threat: Wikidata P141 is vulnerable, endangered or critically endangered
- class: mammal, and passerine for birds (mammals answer no)

A species is kept only when its answers are unique among the selection, so the game can tell the characters apart.
Its main claim ("X é uma espécie de ...") is checked by JERV against the Portuguese Wikipedia summary.

Inputs (novos personagens/.cache/animais/, not versioned):
  candidates-birds-mammals.json  Wikidata birds (Q5113) and mammals (Q7377): id, pt label, taxon (P225), status (P141), sitelinks
  BirdFuncDat.txt, MamFuncDat.txt  EltonTraits 1.0 trait tables, joined by scientific name

Stages:
  select      -> joins traits, finds pt Wikipedia titles (Wikidata), keeps species with unique answers and a summary.
                 Writes selection.json (POOL_SIZE species).
  jerv-input  -> writes docs/content/waves/animais/jerv-input.json (questions and main-role claims) for JERV.
  wave        -> needs jerv-traits-report.json. Keeps species whose claim JERV accepted (first TARGET by notability) and
                 writes scripts/character-batch-wave-animais.json, scripts/question-wave-animais.json and pool.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).parents[1]
CACHE = ROOT / "novos personagens/.cache/animais"
WAVE_DIR = ROOT / "docs/content/waves/animais"
CANDIDATES_PATH = CACHE / "candidates-birds-mammals.json"
BIRD_TRAITS_PATH = CACHE / "BirdFuncDat.txt"
MAMMAL_TRAITS_PATH = CACHE / "MamFuncDat.txt"
SELECTION_PATH = CACHE / "selection.json"
TITLES_PATH = CACHE / "wikipedia-titles.json"
SUMMARIES_PATH = CACHE / "summaries.json"
CLASS_RANKS_PATH = CACHE / "class-ranks.json"
QLEVER = "https://qlever.dev/api/wikidata"
BATCH_PATH = ROOT / "scripts/character-batch-wave-animais.json"
QUESTIONS_PATH = ROOT / "scripts/question-wave-animais.json"
POOL_PATH = WAVE_DIR / "pool.json"
JERV_INPUT_PATH = WAVE_DIR / "jerv-input.json"
JERV_REPORT_PATH = WAVE_DIR / "jerv-traits-report.json"
EDITORIAL_PATH = WAVE_DIR / "editorial-questions.json"  # questions JERV scored below 0.8, approved by the editor
USER_AGENT = {"User-Agent": "QuemSouEuAnimals/1.0 (https://github.com/socialbot114-cell/quem-sou-eu-adivinha)"}
TARGET = 300
POOL_SIZE = 330  # a few extra species, so species JERV rejects can be replaced
EXTINCT = {"Q237350", "Q239509"}  # extinct, extinct in the wild
THREATENED = {"Q278113", "Q11394", "Q219413"}  # IUCN vulnerable, endangered, critically endangered
CLASS_NAME = {"mammal": "mamífero", "bird": "ave"}
MIN_ANSWER_DISTANCE = 2  # two animals must differ in at least 2 answers; 1-answer twins confuse the game when answers are wrong

# (attribute, player-facing question). Order is the order of the question file.
QUESTIONS = [
    ("animal_mamifero", "É um mamífero?"),
    ("animal_insetos", "Insetos são a principal comida dele?"),
    ("animal_outros_vertebrados", "Ele se alimenta principalmente de outros animais, como peixes, aves ou mamíferos?"),
    ("animal_peixes", "Peixes são a principal comida dele?"),
    ("animal_carnica", "Ele come principalmente animais mortos, ou seja, carniça?"),
    ("animal_vegetais", "Plantas são a principal comida dele?"),
    ("animal_frutas", "Frutas são a principal comida dele?"),
    ("animal_sementes", "Sementes são a principal comida dele?"),
    ("animal_folhas", "Folhas, raízes ou caules são a principal comida dele?"),
    ("animal_nectar", "Néctar de flores é a principal comida dele?"),
    ("animal_menos_30g", "Um adulto da espécie pesa menos de 30 gramas?"),
    ("animal_menos_300g", "Um adulto da espécie pesa menos de 300 gramas?"),
    ("animal_menos_3kg", "Um adulto da espécie pesa menos de 3 quilos?"),
    ("animal_menos_30kg", "Um adulto da espécie pesa menos de 30 quilos?"),
    ("animal_menos_100kg", "Um adulto da espécie pesa menos de 100 quilos?"),
    ("animal_noturno", "Ele costuma ser ativo à noite?"),
    ("animal_ameacado", "A espécie está ameaçada de extinção segundo a IUCN?"),
]

CLASS_CLAIM = {  # player-facing noun, article, and the Wikidata taxon name of the class
    "mammal": ("mamífero", "um", "Mammalia"),
    "bird": ("ave", "uma", "Aves"),
}


def read_traits(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", errors="replace", newline="") as handle:
        return {row["Scientific"].strip(): row for row in csv.DictReader(handle, delimiter="\t")}


def eligible_species() -> list[dict]:
    candidates = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
    tables = {"bird": read_traits(BIRD_TRAITS_PATH), "mammal": read_traits(MAMMAL_TRAITS_PATH)}
    species = []
    for cls, key in (("bird", "birds"), ("mammal", "mammals")):
        for entry in candidates[key]:
            row = tables[cls].get(entry.get("taxon", "").strip())
            if not row or not row.get("BodyMass-Value") or set(entry["status"]) & EXTINCT:
                continue
            if not re.fullmatch(r"[^\d\(\)\[\]]+", entry["label"]):
                continue
            species.append({**entry, "cls": cls, "row": row})
    return species


def traits_of(entry: dict) -> dict[str, int]:
    row = entry["row"]
    diet = lambda column: float(row.get(column) or 0)
    mass = float(row["BodyMass-Value"])
    nocturnal = row["Nocturnal"] if entry["cls"] == "bird" else row["Activity-Nocturnal"]
    return {
        "animal_mamifero": int(entry["cls"] == "mammal"),
        "animal_insetos": int(diet("Diet-Inv") >= 50),
        "animal_outros_vertebrados": int(diet("Diet-Vend") + diet("Diet-Vect") + diet("Diet-Vfish") >= 50),
        "animal_peixes": int(diet("Diet-Vfish") >= 50),
        "animal_carnica": int(diet("Diet-Scav") >= 50),
        "animal_vegetais": int(diet("Diet-Fruit") + diet("Diet-Seed") + diet("Diet-PlantO") + diet("Diet-Nect") >= 50),
        "animal_frutas": int(diet("Diet-Fruit") >= 50),
        "animal_sementes": int(diet("Diet-Seed") >= 50),
        "animal_folhas": int(diet("Diet-PlantO") >= 50),
        "animal_nectar": int(diet("Diet-Nect") >= 50),
        "animal_menos_30g": int(mass < 30),
        "animal_menos_300g": int(mass < 300),
        "animal_menos_3kg": int(mass < 3000),
        "animal_menos_30kg": int(mass < 30000),
        "animal_menos_100kg": int(mass < 100000),
        "animal_noturno": int(nocturnal == "1"),
        "animal_ameacado": int(bool(set(entry["status"]) & THREATENED)),
    }


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=USER_AGENT)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def load_titles(species: list[dict]) -> dict[str, dict[str, str | None]]:
    """Wikipedia article titles per species, in Portuguese and English (Wikidata sitelinks)."""
    titles = json.loads(TITLES_PATH.read_text(encoding="utf-8")) if TITLES_PATH.is_file() else {}
    missing = [entry["id"] for entry in species if entry["id"] not in titles]
    for start in range(0, len(missing), 50):
        chunk = missing[start:start + 50]
        query = urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(chunk), "props": "sitelinks",
                                        "sitefilter": "ptwiki|enwiki", "format": "json"})
        entities = get_json(f"https://www.wikidata.org/w/api.php?{query}").get("entities", {})
        for qid in chunk:
            sitelinks = entities.get(qid, {}).get("sitelinks", {})
            titles[qid] = {lang: sitelinks[f"{lang}wiki"]["title"] if f"{lang}wiki" in sitelinks else None for lang in ("pt", "en")}
        TITLES_PATH.write_text(json.dumps(titles, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(0.5)
    return titles


def class_ranks(species: list[dict]) -> dict[str, list[str]]:
    """Latin names of the classes each species sits under (Wikidata P171 up to the class rank), cached."""
    ranks = json.loads(CLASS_RANKS_PATH.read_text(encoding="utf-8")) if CLASS_RANKS_PATH.is_file() else {}
    missing = [entry["id"] for entry in species if entry["id"] not in ranks]
    for start in range(0, len(missing), 100):
        chunk = missing[start:start + 100]
        values = " ".join(f"wd:{qid}" for qid in chunk)
        query = ("PREFIX wdt: <http://www.wikidata.org/prop/direct/>\n"
                 "PREFIX wd: <http://www.wikidata.org/entity/>\n"
                 f"SELECT ?item ?clsName WHERE {{ VALUES ?item {{ {values} }} "
                 "?item wdt:P171+ ?cls . ?cls wdt:P105 wd:Q37517 ; wdt:P225 ?clsName . }")
        request = urllib.request.Request(QLEVER, data=query.encode("utf-8"), headers={**USER_AGENT, "Content-type": "application/sparql-query",
                                                                                     "Accept": "application/sparql-results+json"})
        with urllib.request.urlopen(request, timeout=280) as response:
            rows = json.load(response)["results"]["bindings"]
        for qid in chunk:
            ranks[qid] = []
        for row in rows:
            ranks[row["item"]["value"].rsplit("/", 1)[-1]].append(row["clsName"]["value"])
        CLASS_RANKS_PATH.write_text(json.dumps(ranks, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(0.5)
    return ranks


def wiki_summary(title: str, lang: str, cache: dict) -> str | None:
    key = f"{lang}:{title}"
    if key in cache:
        return cache[key]
    slug = urllib.parse.quote(title.replace(" ", "_"))
    request = urllib.request.Request(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{slug}", headers=USER_AGENT)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                cache[key] = json.load(response).get("extract")
            time.sleep(0.3)
            return cache[key]
        except HTTPError as error:
            if error.code == 404:
                cache[key] = None
                return None
            if error.code != 429 and error.code < 500:
                raise
            time.sleep(30 * (attempt + 1))  # rate limited: back off and keep the failure out of the cache
        except URLError:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Resumo indisponível na Wikipédia pt: {title}")


def select() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    species = sorted(eligible_species(), key=lambda entry: -entry["sitelinks"])
    titles = load_titles(species)
    cache = json.loads(SUMMARIES_PATH.read_text(encoding="utf-8")) if SUMMARIES_PATH.is_file() else {}
    chosen, seen = [], set()
    try:
        for entry in species:
            traits = traits_of(entry)
            signature = tuple(traits.values())
            if signature in seen:
                continue
            source = None  # Portuguese article first, English when there is no Portuguese summary
            for lang in ("pt", "en"):
                title = titles.get(entry["id"], {}).get(lang)
                extract = wiki_summary(title, lang, cache) if title else None
                if extract:
                    source = {"lang": lang, "title": title, "extract": extract}
                    break
            if not source:
                continue
            seen.add(signature)
            chosen.append({"id": entry["id"], "label": entry["label"], "sitelinks": entry["sitelinks"], "cls": entry["cls"],
                           "taxon": entry["taxon"], **source, "traits": traits})
            if len(chosen) == POOL_SIZE:
                break
    finally:
        SUMMARIES_PATH.write_text(json.dumps(cache, ensure_ascii=False) + "\n", encoding="utf-8")
    SELECTION_PATH.write_text(json.dumps(chosen, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"selected {len(chosen)} species with distinct answers | eligible {len(species)} | distinct answer sets {len(seen)}")


def identifiers(selection: list[dict]) -> dict[str, str]:
    """Stable slug per species; a duplicated name gets the Wikidata id appended."""
    names = Counter(entry["label"].casefold() for entry in selection)
    out = {}
    for entry in selection:
        slug = slugify(entry["label"]) or entry["id"].lower()
        out[entry["id"]] = f"{slug}-{entry['id'].lower()}" if names[entry["label"].casefold()] > 1 else slug
    return out


def slugify(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")


def question_entries() -> list[dict]:
    return [{"id": attribute.replace("_", "-"), "text": text, "attribute": attribute, "categories": ["Animais"]}
            for attribute, text in QUESTIONS]


def jerv_input() -> None:
    selection = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    ids = identifiers(selection)
    ranks = class_ranks(selection)
    today = date.today().isoformat()
    claims = []
    for entry in selection:
        noun, article, class_latin = CLASS_CLAIM[entry["cls"]]
        if class_latin not in ranks.get(entry["id"], []):
            continue  # Wikidata does not place it in the class the traits file implies: no claim, so it cannot be accepted
        name = entry["label"][:1].upper() + entry["label"][1:]
        identifier = ids[entry["id"]]
        claims.append({"id": f"{identifier}-main-role", "person_id": identifier, "person_name": name,
                       "claim": f"{name} é {article} {noun}.", "source_url": f"https://www.wikidata.org/wiki/{entry['id']}",
                       "source_title": "Wikidata", "source_excerpt": f"Wikidata: o táxon {entry['taxon']} pertence à classe {class_latin} (propriedade P171, taxonomia).",
                       "source_license": "CC0 1.0", "source_license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                       "last_verified": today, "answer": 1})
    questions = [{"id": q["id"], "text": q["text"], "category": "Animais", "attribute": q["attribute"]} for q in question_entries()]
    WAVE_DIR.mkdir(parents=True, exist_ok=True)
    JERV_INPUT_PATH.write_text(json.dumps({"questions": questions, "claims": claims}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"jerv input: {len(questions)} questions, {len(claims)} claims -> {JERV_INPUT_PATH}")


def wave() -> None:
    selection = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    report = json.loads(JERV_REPORT_PATH.read_text(encoding="utf-8"))
    questions = question_entries()
    approved = {item["id"] for item in json.loads(EDITORIAL_PATH.read_text(encoding="utf-8"))["questionReviews"]
                if item["editorial_decision"] == "accepted"} if EDITORIAL_PATH.is_file() else set()
    not_accepted = [q["id"] for q in questions
                    if q["id"] not in approved and report["question_reviews"].get(q["id"], {}).get("status") != "accepted"]
    if not_accepted:
        raise SystemExit(f"JERV não aceitou as perguntas (ajuste o texto e refaça): {not_accepted}")

    ids = identifiers(selection)
    today = date.today().isoformat()
    people, sources = [], []
    for entry in selection:
        identifier = ids[entry["id"]]
        if report["claim_reviews"].get(f"{identifier}-main-role", {}).get("status") != "accepted":
            continue
        if len(people) == TARGET:
            break
        if any(sum(entry["traits"][a] != other[a] for a, _ in QUESTIONS) < MIN_ANSWER_DISTANCE for other in (p["attributes"] for p in people)):
            continue
        name = entry["label"][:1].upper() + entry["label"][1:]
        profession = CLASS_NAME[entry["cls"]].capitalize()
        url = f"https://{entry['lang']}.wikipedia.org/wiki/{urllib.parse.quote(entry['title'].replace(' ', '_'))}"
        people.append({"id": identifier, "name": name, "country": "Animal", "profession": profession, "gender": "N",
                       "birthYear": 2000, "alive": 1, "attributes": entry["traits"]})
        sources.append({"id": identifier, "name": name, "profession": profession, "sourceTitle": entry["title"], "sourceURL": url,
                        "sourceExcerpt": entry["extract"].strip(), "sourceLicense": "CC BY-SA 4.0",
                        "sourceLicenseURL": "https://creativecommons.org/licenses/by-sa/4.0/", "lastVerified": today})
    if len(people) < TARGET:
        print(f"espécies mantidas: {len(people)} (meta {TARGET}; distância mínima entre animais: {MIN_ANSWER_DISTANCE} respostas)")

    BATCH_PATH.write_text(json.dumps({"people": {"Animais": people}}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    QUESTIONS_PATH.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    POOL_PATH.write_text(json.dumps({"generatedAt": today, "category": "Animais", "people": people, "sources": sources},
                                    ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"animals {len(people)} | questions {len(questions)} | sources {len(sources)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=("select", "jerv-input", "wave"))
    args = parser.parse_args()
    {"select": select, "jerv-input": jerv_input, "wave": wave}[args.stage]()


if __name__ == "__main__":
    main()
