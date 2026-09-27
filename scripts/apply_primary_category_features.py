#!/usr/bin/env python3
"""Add sourced-answer feature values for existing artist and creator profiles."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
PRIMARY_PATH = ROOT / "iosApp/Resources/KnowledgeBase/knowledge.json"

ARTIST_BIRTH_YEARS = {
    "anitta": 1993,
    "ivete-sangalo": 1972,
    "caetano-veloso": 1942,
    "gilberto-gil": 1942,
    "marisa-monte": 1967,
    "ludmilla": 1995,
    "fernanda-montenegro": 1929,
    "wagner-moura": 1976,
    "selton-mello": 1972,
    "xuxa": 1963,
    "lazaro-ramos": 1978,
    "gloria-pires": 1963,
    "seu-jorge": 1970,
    "sandy": 1983,
    "rodrigo-santoro": 1975,
    "tais-araujo": 1978,
}
CREATOR_BIRTH_YEARS = {
    "whindersson-nunes": 1995,
    "felipe-neto": 1988,
    "virginia-fonseca": 1999,
    "khaby-lame": 2000,
    "mrbeast": 1998,
    "casimiro-miguel": 1983,
    "bianca-andrade": 1984,
    "camila-loures": 1995,
    "lucas-rangel": 1997,
    "gkay": 1992,
    "luva-de-pedreiro": 2001,
    "juliette": 1989,
    "ibere-thenorio": 1980,
    "cellbit": 1997,
    "nathalia-arcuri": 1985,
}
SAMBA_ARTISTS = {"gilberto-gil", "seu-jorge"}
SERTANEJO_ARTISTS: set[str] = set()
PODCAST_CREATORS = {"virginia-fonseca", "casimiro-miguel", "camila-loures", "nathalia-arcuri"}
TIKTOK_ORIGIN_CREATORS = {"khaby-lame", "luva-de-pedreiro"}
ENGINEER_CREATORS: set[str] = set()


def feature_values(identifier: str) -> dict[str, int] | None:
    if identifier in ARTIST_BIRTH_YEARS:
        return {
            "born_before_1975": int(ARTIST_BIRTH_YEARS[identifier] < 1975),
            "samba_artist": int(identifier in SAMBA_ARTISTS),
            "sertanejo_artist": int(identifier in SERTANEJO_ARTISTS),
        }
    if identifier in CREATOR_BIRTH_YEARS:
        return {
            "born_before_1998": int(CREATOR_BIRTH_YEARS[identifier] < 1998),
            "creator_podcaster": int(identifier in PODCAST_CREATORS),
            "creator_tiktok_origin": int(identifier in TIKTOK_ORIGIN_CREATORS),
            "creator_engineer": int(identifier in ENGINEER_CREATORS),
        }
    return None


def apply(path: Path = PRIMARY_PATH) -> int:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    expected_ids = set(ARTIST_BIRTH_YEARS) | set(CREATOR_BIRTH_YEARS)
    seen_ids: set[str] = set()
    changed = 0

    for index, line in enumerate(lines):
        identifier_match = re.search(r'"id":"([^"]+)"', line)
        if not identifier_match:
            continue
        identifier = identifier_match.group(1)
        values = feature_values(identifier)
        if values is None:
            continue

        attributes_match = re.search(r'"attributes":\{[^{}]*\}', line)
        if not attributes_match:
            raise ValueError(f"Missing attributes object for {identifier}")
        encoded_attributes = attributes_match.group(0)[len('"attributes":'):]
        attributes = json.loads(encoded_attributes)
        attributes.update(values)
        replacement = '"attributes":' + json.dumps(attributes, ensure_ascii=False, separators=(",", ":"))
        updated_line = line[:attributes_match.start()] + replacement + line[attributes_match.end():]
        if updated_line != line:
            lines[index] = updated_line
            changed += 1
        seen_ids.add(identifier)

    missing = expected_ids - seen_ids
    if missing:
        raise ValueError(f"Missing primary characters for feature overrides: {sorted(missing)}")
    if changed:
        path.write_text("".join(lines), encoding="utf-8")
    return changed


def main() -> None:
    print(f"Updated feature values for {apply()} existing artist and creator profiles")


if __name__ == "__main__":
    main()
