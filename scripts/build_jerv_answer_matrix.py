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
OUTPUT_PATH = ROOT / "docs/content/jerv-answer-matrix-input.json"


def build(primary: dict, expansion: dict, source_manifest: dict) -> dict:
    questions = primary["questions"] + expansion["questions"]
    sources = {item["id"]: item for item in source_manifest["items"]}
    review_questions: dict[str, dict] = {}
    claims: list[dict] = []
    for person in expansion["people"]:
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
            "people": len(expansion["people"]),
            "answer_cells": len(claims),
            "evidence_policy": "Use only the cited excerpt; an absent fact is insufficient evidence for a No answer.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    primary = json.loads(PRIMARY_PATH.read_text(encoding="utf-8"))
    expansion = json.loads(EXPANSION_PATH.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    result = build(primary, expansion, sources)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {result['scope']['answer_cells']} sourced answer cells for {result['scope']['people']} characters across {len(result['questions'])} unique game questions")


if __name__ == "__main__":
    main()
