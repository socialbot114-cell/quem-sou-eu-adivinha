#!/usr/bin/env python3
"""Build the JERV/TypeSafe editorial input from the local expansion and sources."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
EXPANSION_PATH = ROOT / "iosApp/Resources/KnowledgeBase/character-expansion.json"
SOURCES_PATH = ROOT / "docs/content/character-sources.json"
OUTPUT_PATH = ROOT / "docs/content/jerv-character-review-input.json"
CLAIM_OVERRIDES = {
    "ariana-grande": "Ariana Grande is an American singer, songwriter, and actress.",
    "elon-musk": "Elon Musk is a businessman and the CEO of Tesla and SpaceX.",
    "tim-cook": "Tim Cook is an American business executive and the executive chairman of Apple Inc.",
    "jack-ma": "Jack Ma is a Chinese businessman and co-founder of Alibaba Group.",
    "bernard-arnault": "Bernard Arnault is a French businessman and the chairman and CEO of LVMH, a luxury goods company.",
    "djavan": "Djavan is a Brazilian singer-songwriter and guitarist.",
}


def build_review_input(expansion: dict, source_manifest: dict) -> dict:
    sources = {item["id"]: item for item in source_manifest["items"]}
    questions = [
        {
            "id": item["id"],
            "text": item["text"],
            "category": item["categories"][0],
            "attribute": item["attribute"],
        }
        for item in expansion["questions"]
    ]
    claims = []
    unresolved = []
    for person in expansion["people"]:
        source = sources.get(person["id"])
        if not source or not source.get("sourceExcerpt"):
            unresolved.append(person["id"])
            continue
        claim_id = f"{person['id']}-main-role"
        claims.append({
            "id": claim_id,
            "person_id": person["id"],
            "person_name": person["name"],
            "answer": 1,
            "claim": CLAIM_OVERRIDES.get(
                person["id"],
                f"The source identifies {person['name']} as: {person['profession']}.",
            ),
            "source_url": source["sourceURL"],
            "source_title": source["sourceTitle"],
            "source_excerpt": source["sourceExcerpt"],
            "source_license": source["sourceLicense"],
            "source_license_url": source["sourceLicenseURL"],
            "last_verified": source["lastVerified"],
        })
    if unresolved:
        raise ValueError(f"missing source excerpts for: {', '.join(unresolved)}")
    return {"questions": questions, "claims": claims}


def main() -> None:
    expansion = json.loads(EXPANSION_PATH.read_text(encoding="utf-8"))
    source_manifest = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    data = build_review_input(expansion, source_manifest)
    OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(data['questions'])} questions and {len(data['claims'])} sourced profile claims for JERV")


if __name__ == "__main__":
    main()
