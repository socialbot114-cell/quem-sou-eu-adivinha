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
PRIMARY_SOURCES_PATH = ROOT / "docs/content/primary-character-sources.json"
BATCH_150_PATH = ROOT / "scripts/character-batch-150.json"
OUTPUT_PATH = ROOT / "docs/content/jerv-answer-matrix-input.json"
ALL_OUTPUT_PATH = ROOT / "docs/content/jerv-answer-matrix-all-input.json"


def build(
    primary: dict,
    expansion: dict,
    source_manifest: dict,
    person_ids: set[str] | None = None,
    include_primary: bool = False,
    answer_cells: set[tuple[str, str]] | None = None,
) -> dict:
    questions = primary["questions"] + expansion["questions"]
    sources = {item["id"]: item for item in source_manifest["items"]}
    review_questions: dict[str, dict] = {}
    claims: list[dict] = []
    available_people = (primary["people"] if include_primary else []) + expansion["people"]
    if answer_cells is not None:
        answer_cell_people = {person_id for person_id, _ in answer_cells}
        if person_ids is not None and person_ids != answer_cell_people:
            raise ValueError("profile IDs do not match the explicit answer-cell list")
        person_ids = answer_cell_people
    people = [person for person in available_people if person_ids is None or person["id"] in person_ids]
    if person_ids is not None and {person["id"] for person in people} != person_ids:
        missing = sorted(person_ids - {person["id"] for person in people})
        raise ValueError(f"requested IDs are missing from the selected knowledge-base files: {missing}")
    for person in people:
        source = sources.get(person["id"])
        if not source or not source.get("sourceExcerpt"):
            raise ValueError(f"missing sourced excerpt for {person['id']}")
        relevant = [
            question for question in questions
            if question["attribute"] in person["attributes"]
            and (question["categories"] == ["Todos"] or set(question["categories"]) & set(person["categories"]))
            and (answer_cells is None or (person["id"], question["id"]) in answer_cells)
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
            "explicit_cell_selection": answer_cells is not None,
            "categories": sorted({category for person in people for category in person["categories"]}),
            "evidence_policy": "Use only the cited excerpt; an absent fact is insufficient evidence for a No answer.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-manifest", action="append", type=Path, help="Source manifest; repeat to merge manifests")
    parser.add_argument("--include-primary", action="store_true", help="Include original knowledge.json profiles")
    parser.add_argument("--person-id", action="append", help="Limit review to this profile ID; repeatable")
    parser.add_argument("--person-ids-file", type=Path, help="JSON ID list or catalog-validation-queue.json")
    parser.add_argument("--answer-cells-file", type=Path, help="Restrict review to cells in catalog-validation-queue.json")
    parser.add_argument("--batch-150-only", action="store_true", help="Review only the 150 newly curated character profiles")
    parser.add_argument("--category", action="append", help="With --batch-150-only, limit review to this existing category (repeatable)")
    args = parser.parse_args()
    primary = json.loads(PRIMARY_PATH.read_text(encoding="utf-8"))
    expansion = json.loads(EXPANSION_PATH.read_text(encoding="utf-8"))
    default_manifests = [SOURCES_PATH, PRIMARY_SOURCES_PATH] if args.include_primary else [SOURCES_PATH]
    manifest_paths = args.source_manifest or default_manifests
    source_items = []
    for source_path in manifest_paths:
        source_items.extend(json.loads(source_path.read_text(encoding="utf-8"))["items"])
    source_ids = [item["id"] for item in source_items]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source manifests contain duplicate profile IDs")
    sources = {"items": source_items}
    person_ids = set(args.person_id or [])
    if args.person_ids_file:
        ids_data = json.loads(args.person_ids_file.read_text(encoding="utf-8"))
        if isinstance(ids_data, list):
            person_ids.update(ids_data)
        elif isinstance(ids_data, dict) and "details" in ids_data:
            person_ids.update(
                item["personId"] for item in ids_data["details"].get("uncoveredApplicableCells", [])
            )
        else:
            raise ValueError("--person-ids-file must be a JSON ID list or catalog-validation-queue.json")
    answer_cells = None
    if args.answer_cells_file:
        if args.person_id or args.person_ids_file:
            raise ValueError("--answer-cells-file cannot be combined with profile ID selection")
        cells_data = json.loads(args.answer_cells_file.read_text(encoding="utf-8"))
        if isinstance(cells_data, dict) and "details" in cells_data:
            entries = cells_data["details"].get("uncoveredApplicableCells", [])
        elif isinstance(cells_data, dict) and "claims" in cells_data:
            entries = [
                {"personId": claim["person_id"], "questionId": claim["question_id"]}
                for claim in cells_data["claims"]
            ]
        elif isinstance(cells_data, list):
            entries = cells_data
        else:
            raise ValueError("--answer-cells-file must be a cell list, matrix input, or catalog-validation-queue.json")
        answer_cells = {(item["personId"], item["questionId"]) for item in entries}
    if not person_ids:
        person_ids = None

    if args.batch_150_only:
        if args.include_primary or args.person_id or args.person_ids_file or args.answer_cells_file:
            raise ValueError("--batch-150-only cannot be combined with primary or explicit profile selections")
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
    result = build(
        primary,
        expansion,
        sources,
        person_ids=person_ids,
        include_primary=args.include_primary,
        answer_cells=answer_cells,
    )
    if answer_cells is not None:
        built_cells = {(claim["person_id"], claim["question_id"]) for claim in result["claims"]}
        missing_cells = answer_cells - built_cells
        if missing_cells:
            raise ValueError(f"selected answer cells are not applicable/available: {sorted(missing_cells)[:20]}")
    output_path = args.output or (ALL_OUTPUT_PATH if args.include_primary else OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {result['scope']['answer_cells']} sourced answer cells for {result['scope']['people']} characters across {len(result['questions'])} unique game questions")
    print(f"JERV matrix input: {output_path}")


if __name__ == "__main__":
    main()
