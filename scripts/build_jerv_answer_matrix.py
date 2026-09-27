#!/usr/bin/env python3
"""Create a sourced JERV claim for every known expansion answer cell."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PRIMARY_PATH = ROOT / "iosApp/Resources/KnowledgeBase/knowledge.json"
EXPANSION_PATH = ROOT / "iosApp/Resources/KnowledgeBase/character-expansion.json"
SOURCES_PATH = ROOT / "docs/content/character-sources.json"
BATCH_150_PATH = ROOT / "scripts/character-batch-150.json"
OUTPUT_PATH = ROOT / "docs/content/jerv-answer-matrix-input.json"


def build(
    primary: dict,
    expansion: dict,
    source_manifest: dict,
    person_ids: set[str] | None = None,
) -> dict:
    questions = primary["questions"] + expansion["questions"]
    sources = {item["id"]: item for item in source_manifest["items"]}
    review_questions: dict[str, dict] = {}
    claims: list[dict] = []
    people = [person for person in expansion["people"] if person_ids is None or person["id"] in person_ids]
    if person_ids is not None and {person["id"] for person in people} != person_ids:
        missing = sorted(person_ids - {person["id"] for person in people})
        raise ValueError(f"batch IDs are missing from character-expansion.json: {missing}")
    for person in people:
        source = sources.get(person["id"])
        if not source or not source.get("sourceExcerpt"):
            raise ValueError(f"missing sourced excerpt for {person['id']}")
        relevant = [
            question for question in questions
            if question["attribute"] in person["attributes"]
            and (question["categories"] == ["Todos"] or set(question["categories"]) & set(person["categories"]))
        ]
        for question in relevant:
            review_questions[question["id"]] = {
                "id": question["id"],
                "text": question["text"],
                "category": question["categories"][0],
                "attribute": question["attribute"],
            }
            value = float(person["attributes"][question["attribute"]])
            answer_label = "yes" if value >= 0.75 else "no" if value <= 0.25 else "probably"
            claims.append({
                "id": f"{person['id']}--{question['attribute']}",
                "person_id": person["id"],
                "person_name": person["name"],
                "question_id": question["id"],
                "answer": value,
                "claim": f"For {person['name']}, the proposed answer to the game clue ‘{question['text']}’ is {answer_label}.",
                "source_url": source["sourceURL"],
                "source_title": source["sourceTitle"],
                "source_excerpt": source["sourceExcerpt"],
                "source_license": source["sourceLicense"],
                "source_license_url": source["sourceLicenseURL"],
                "last_verified": source["lastVerified"],
            })
    return {
        "questions": list(review_questions.values()),
        "claims": claims,
        "scope": {
            "people": len(people),
            "answer_cells": len(claims),
            "categories": sorted({category for person in people for category in person["categories"]}),
            "evidence_policy": "Use only the cited excerpt; an absent fact is insufficient evidence for a No answer.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--batch-150-only", action="store_true", help="Review only the 150 newly curated character profiles")
    parser.add_argument("--category", action="append", help="With --batch-150-only, limit review to this existing category (repeatable)")
    args = parser.parse_args()
    primary = json.loads(PRIMARY_PATH.read_text(encoding="utf-8"))
    expansion = json.loads(EXPANSION_PATH.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    person_ids = None
    if args.batch_150_only:
        batch = json.loads(BATCH_150_PATH.read_text(encoding="utf-8"))
        categories = args.category or list(batch["people"])
        unknown = set(categories) - batch["people"].keys()
        if unknown:
            raise ValueError(f"categories are not present in the new batch: {sorted(unknown)}")
        person_ids = {
            person["id"]
            for category in categories
            for person in batch["people"][category]
        }
        if len(person_ids) != 150:
            expected = sum(len(batch["people"][category]) for category in categories)
            if len(person_ids) != expected:
                raise ValueError(f"batch categories contain duplicate IDs: expected {expected}, got {len(person_ids)}")
    elif args.category:
        raise ValueError("--category requires --batch-150-only")
    result = build(primary, expansion, sources, person_ids=person_ids)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {result['scope']['answer_cells']} sourced answer cells for {result['scope']['people']} characters across {len(result['questions'])} unique game questions")


if __name__ == "__main__":
    main()
