#!/usr/bin/env python3
"""Turn Wikidata harvests of existing characters into optional facts.

Writes docs/content/optional-facts.json, keyed by character id, for the optional questions
of Artistas brasileiros and Futebol. The build applies these facts to existing profiles
(knowledge.json and the expansion), so every character answers the same optional questions
as the 200-character batch.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(Path(__file__).parent))
import derive_character_batch_200 as derive  # noqa: E402

ARTIST_KEYS = (
    "genre_mpb", "genre_rock", "genre_pop", "genre_funk",
    "genre_bossa", "genre_pagode", "genre_axe", "genre_rap", "genre_choro",
    "genre_jazz", "genre_electronic", "composer", "born_before_1945", "born_before_1955",
    "born_before_1960", "born_before_1965", "born_before_1985", "born_in_rio", "born_in_sao_paulo",
    "born_in_northeast", "born_in_south", "born_in_minas_gerais", "born_in_bahia",
)
FOOTBALL_KEYS = (
    "born_before_1985", "played_in_brazil", "played_in_italy", "played_in_spain", "played_in_germany",
    "played_in_france", "played_in_portugal", "fifa_best",
)
DEFAULT_OUTPUT = ROOT / "docs/content/optional-facts.json"


def load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["records"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artists", type=Path, help="harvest of existing Artistas brasileiros")
    parser.add_argument("football", type=Path, help="harvest of existing Futebol")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    facts: dict[str, dict] = {}
    artists = [record for record in load(args.artists) if record.get("id")]
    derive.prepare_birthplaces(artists)
    for record in artists:
        birth = derive.birth_year(record)
        if birth is None:
            continue
        _, dynamic = derive.artist_attributes(record, birth)
        facts[record["id"]] = {
            "qid": record["qid"],
            "sourceUrl": record["sourceUrl"],
            "attributes": {key: dynamic[key] for key in ARTIST_KEYS if dynamic.get(key) is not None},
        }

    football = [record for record in load(args.football) if record.get("id")]
    clubs = derive.club_lookup(football)
    for record in football:
        if derive.birth_year(record) is None:
            continue
        values = derive.football_optional(record, clubs)
        facts[record["id"]] = {
            "qid": record["qid"],
            "sourceUrl": record["sourceUrl"],
            "attributes": {key: values[key] for key in FOOTBALL_KEYS if values.get(key) is not None},
        }

    args.output.write_text(json.dumps({"characters": facts}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(facts)} personagens com fatos opcionais -> {args.output}")


if __name__ == "__main__":
    main()
