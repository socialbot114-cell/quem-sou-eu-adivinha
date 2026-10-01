#!/usr/bin/env python3
"""Report answer-evidence coverage before expanding the offline character catalog."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_character_expansion import build as rebuild_expansion


KNOWLEDGE_DIR = ROOT / "iosApp/Resources/KnowledgeBase"
BASE_PATH = KNOWLEDGE_DIR / "knowledge.json"
EXPANSION_PATH = KNOWLEDGE_DIR / "character-expansion.json"
SOURCE_PATH = ROOT / "docs/content/character-sources.json"
PRIMARY_SOURCE_PATH = ROOT / "docs/content/primary-character-sources.json"
OLD_MATRIX_INPUT_PATH = ROOT / "docs/content/jerv-answer-matrix-input.json"
OLD_MATRIX_REPORT_PATH = ROOT / "docs/content/jerv-answer-matrix-report.json"
NEW_MATRIX_INPUT_PATH = ROOT / "docs/content/jerv-answer-matrix-150-input.json"
NEW_MATRIX_REPORT_PATH = ROOT / "docs/content/jerv-answer-matrix-150-report.json"
GAP_MATRIX_INPUT_PATH = ROOT / "docs/content/jerv-answer-matrix-gap-input.json"
GAP_MATRIX_REPORT_PATH = ROOT / "docs/content/jerv-answer-matrix-gap-report.json"
NEW_ADJUDICATION_PATH = ROOT / "docs/content/jerv-answer-matrix-150-adjudications.json"
GAP_ADJUDICATION_PATH = ROOT / "docs/content/jerv-answer-matrix-gap-adjudications.json"
CONTRADICTION_ADJUDICATION_PATH = ROOT / "docs/content/jerv-answer-matrix-contradiction-adjudications.json"
CONTRADICTION_FOLLOWUP_INPUT_PATH = ROOT / "docs/content/jerv-answer-matrix-contradiction-followup-input.json"
CONTRADICTION_FOLLOWUP_REPORT_PATH = ROOT / "docs/content/jerv-answer-matrix-contradiction-followup-report.json"
HUMAN_REVIEW_PATH = ROOT / "docs/content/jerv-character-human-review.json"
CHARACTER_REVIEW_PATH = ROOT / "docs/content/jerv-character-review-final.json"

DOCUMENTED_LEGACY_ADJUDICATIONS = {"ariana-grande--acted_in_film"}
BIRTH_THRESHOLD_IMPLICATIONS = (
    ("born_before_1800", "born_before_1900"),
    ("born_before_1900", "born_before_1970"),
    ("born_before_1970", "born_before_1975"),
    ("born_before_1975", "born_before_1980"),
    ("born_before_1980", "born_before_1990"),
    ("born_before_1990", "born_before_1993"),
    ("born_before_1993", "born_before_1994"),
    ("born_before_1994", "born_before_1995"),
    ("born_before_1995", "born_before_1996"),
    ("born_before_1996", "born_before_1998"),
    ("born_before_1998", "born_before_2000"),
)


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Could not load {path.relative_to(ROOT)}: {error}") from error


def applicable_cells(people: list[dict], questions: list[dict]) -> set[tuple[str, str]]:
    cells = set()
    for person in people:
        person_categories = set(person["categories"])
        for question in questions:
            applies = question["categories"] == ["Todos"] or bool(person_categories & set(question["categories"]))
            if applies and question["attribute"] in person["attributes"]:
                cells.add((person["id"], question["id"]))
    return cells


def collect_matrix(path: Path, report_path: Path) -> dict[str, Any]:
    matrix_input = load_json(path)
    report = load_json(report_path)
    claims = matrix_input.get("claims", [])
    reviews = report.get("claim_reviews", {})
    cell_keys = set()
    statuses: Counter[str] = Counter()
    claim_ids = set()
    claim_order = []
    profiles = set()
    per_cell_source_fields = 0
    claims_by_id: dict[str, dict[str, Any]] = {}
    for claim in claims:
        claim_id = claim["id"]
        key = (claim["person_id"], claim["question_id"])
        if key in cell_keys:
            raise SystemExit(f"Duplicate matrix cell in {path.name}: {claim_id}")
        cell_keys.add(key)
        claim_ids.add(claim_id)
        claim_order.append(claim_id)
        profiles.add(claim["person_id"])
        claims_by_id[claim_id] = claim
        statuses[reviews.get(claim_id, {}).get("status", "missing-review")] += 1
        if claim.get("source_url") and claim.get("source_excerpt"):
            per_cell_source_fields += 1
    return {
        "people": len(profiles),
        "cells": len(cell_keys),
        "questionReviews": {
            status: count
            for status, count in Counter(item.get("status", "missing-status") for item in report.get("question_reviews", {}).values()).items()
        },
        "cellReviews": dict(statuses),
        "questionReviewStatusById": {
            question_id: item.get("status", "missing-status")
            for question_id, item in report.get("question_reviews", {}).items()
        },
        "cellIds": claim_ids,
        "cellKeys": cell_keys,
        "personIds": profiles,
        "claimsWithSourceExcerpt": per_cell_source_fields,
        "claimsById": claims_by_id,
        "reviewStatusById": {
            claim_id: reviews.get(claim_id, {}).get("status", "missing-review")
            for claim_id in claim_order
        },
        "reviewDetailsById": {claim_id: reviews.get(claim_id, {}) for claim_id in claim_order},
    }


def check_invariants(people: list[dict]) -> dict[str, list[str]]:
    violations: dict[str, list[str]] = {}
    for earlier, later in BIRTH_THRESHOLD_IMPLICATIONS:
        ids = [
            person["id"]
            for person in people
            if person["attributes"].get(earlier) == 1
            and later in person["attributes"]
            and person["attributes"][later] != 1
        ]
        violations[f"{earlier}_implies_{later}"] = ids

    ids = [
        person["id"]
        for person in people
        if person["attributes"].get("died_before_1900") == 1
        and person["attributes"].get("alive") != 0
    ]
    violations["died_before_1900_implies_not_alive"] = ids

    ids = [
        person["id"]
        for person in people
        if person["attributes"].get("alive") == 1
        and person["attributes"].get("died_before_1900") == 1
    ]
    violations["alive_excludes_died_before_1900"] = ids
    return violations


def audit(*, include_details: bool = False) -> dict[str, Any]:
    base = load_json(BASE_PATH)
    expansion = load_json(EXPANSION_PATH)
    regenerated_expansion = rebuild_expansion()
    sources = (
        load_json(SOURCE_PATH).get("items", [])
        + load_json(PRIMARY_SOURCE_PATH).get("items", [])
    )
    old_matrix = collect_matrix(OLD_MATRIX_INPUT_PATH, OLD_MATRIX_REPORT_PATH)
    new_matrix = collect_matrix(NEW_MATRIX_INPUT_PATH, NEW_MATRIX_REPORT_PATH)
    gap_matrix = collect_matrix(GAP_MATRIX_INPUT_PATH, GAP_MATRIX_REPORT_PATH)
    adjudications = load_json(NEW_ADJUDICATION_PATH).get("items", [])
    gap_adjudications = load_json(GAP_ADJUDICATION_PATH).get("items", [])
    contradiction_adjudications = load_json(CONTRADICTION_ADJUDICATION_PATH).get("items", [])
    contradiction_followup_input = load_json(CONTRADICTION_FOLLOWUP_INPUT_PATH)
    contradiction_followup_report = load_json(CONTRADICTION_FOLLOWUP_REPORT_PATH)
    human_review = load_json(HUMAN_REVIEW_PATH)
    character_review = load_json(CHARACTER_REVIEW_PATH)

    people = base["people"] + expansion["people"]
    questions = base["questions"] + expansion["questions"]
    cells = applicable_cells(people, questions)
    old_cells = old_matrix["cellKeys"]
    new_cells = new_matrix["cellKeys"]
    gap_cells = gap_matrix["cellKeys"]
    reviewed_cells = old_cells | new_cells | gap_cells
    overlap = (old_cells & new_cells) | (old_cells & gap_cells) | (new_cells & gap_cells)
    if overlap:
        raise SystemExit(f"Answer matrix reports overlap in {len(overlap)} person/question cells")

    all_ids = {person["id"] for person in people}
    people_by_id = {person["id"]: person for person in people}
    questions_by_id = {question["id"]: question for question in questions}
    base_ids = {person["id"] for person in base["people"]}
    expansion_ids = {person["id"] for person in expansion["people"]}
    source_ids = {item.get("id") for item in sources}
    matrix_ids = old_matrix["personIds"] | new_matrix["personIds"] | gap_matrix["personIds"]

    old_human = old_matrix["cellReviews"].get("human-review", 0)
    new_human = new_matrix["cellReviews"].get("human-review", 0)
    gap_human = gap_matrix["cellReviews"].get("human-review", 0)
    adjudicated_ids = {item.get("id") for item in adjudications}
    if not adjudicated_ids <= new_matrix["cellIds"]:
        raise SystemExit("An answer adjudication references a cell absent from the 150-person matrix")
    gap_adjudicated_ids = {item.get("id") for item in gap_adjudications}
    if not gap_adjudicated_ids <= gap_matrix["cellIds"]:
        raise SystemExit("A gap adjudication references a cell absent from the gap matrix")
    contradiction_adjudicated_ids = {item.get("id") for item in contradiction_adjudications}
    contradiction_claims = {claim["id"]: claim for claim in contradiction_followup_input.get("claims", [])}
    contradiction_reviews = contradiction_followup_report.get("claim_reviews", {})
    all_claims_by_id = {
        **old_matrix["claimsById"],
        **new_matrix["claimsById"],
        **gap_matrix["claimsById"],
    }
    if not contradiction_adjudicated_ids <= all_claims_by_id.keys():
        raise SystemExit("A contradiction adjudication references a cell absent from the reviewed matrices")
    if not contradiction_adjudicated_ids <= contradiction_claims.keys():
        raise SystemExit("A contradiction adjudication is absent from the targeted JERV follow-up input")
    if not contradiction_adjudicated_ids <= contradiction_reviews.keys():
        raise SystemExit("A contradiction adjudication is absent from the targeted JERV follow-up report")
    if len(contradiction_adjudicated_ids) != len(contradiction_adjudications):
        raise SystemExit("Duplicate contradiction adjudication IDs")
    contradiction_adjudication_checks = []
    for item in contradiction_adjudications:
        claim_id = item["id"]
        claim = all_claims_by_id[claim_id]
        followup_claim = contradiction_claims[claim_id]
        attribute = questions_by_id[claim["question_id"]]["attribute"]
        current_value = people_by_id[claim["person_id"]]["attributes"][attribute]
        contradiction_adjudication_checks.append(
            {
                "id": claim_id,
                "previousAnswerMatchesReviewedInput": float(claim["answer"]) == float(item["previousAnswer"]),
                "targetedInputMatchesPreviousAnswer": float(followup_claim["answer"]) == float(item["previousAnswer"]),
                "jervFlaggedContradiction": contradiction_reviews[claim_id].get("decision") == "contradicts",
                "currentAnswerMatchesAdjudication": float(current_value) == float(item["answer"]),
                "sourceURLsPresent": bool(item.get("sourceURLs")),
            }
        )
    new_adjudications_in_pending = sum(
        1
        for claim_id in adjudicated_ids
        if new_matrix["reviewStatusById"].get(claim_id) == "human-review"
    )
    gap_adjudications_in_pending = sum(
        1
        for claim_id in gap_adjudicated_ids
        if gap_matrix["reviewStatusById"].get(claim_id) == "human-review"
    )
    contradiction_adjudications_in_pending = sum(
        1
        for claim_id in contradiction_adjudicated_ids
        if any(
            matrix["reviewStatusById"].get(claim_id) == "human-review"
            for matrix in (old_matrix, new_matrix, gap_matrix)
        )
    )
    prior_documented_adjudications = DOCUMENTED_LEGACY_ADJUDICATIONS & old_matrix["cellIds"]
    resolved_adjudication_ids = (
        prior_documented_adjudications
        | adjudicated_ids
        | gap_adjudicated_ids
        | contradiction_adjudicated_ids
    )
    covered_but_pending = (
        old_human + new_human + gap_human
        - new_adjudications_in_pending
        - gap_adjudications_in_pending
        - contradiction_adjudications_in_pending
        - len(prior_documented_adjudications)
    )
    uncovered = cells - reviewed_cells
    invariants = check_invariants(people)
    accepted_by_model = (
        old_matrix["cellReviews"].get("accepted", 0)
        + new_matrix["cellReviews"].get("accepted", 0)
        + gap_matrix["cellReviews"].get("accepted", 0)
    )
    source_excerpt_claims = (
        old_matrix["claimsWithSourceExcerpt"]
        + new_matrix["claimsWithSourceExcerpt"]
        + gap_matrix["claimsWithSourceExcerpt"]
    )
    unresolved_contradictions = []
    for matrix_name, matrix in (("old73", old_matrix), ("new150", new_matrix), ("gap", gap_matrix)):
        for claim_id, details in matrix["reviewDetailsById"].items():
            followup = contradiction_reviews.get(claim_id, {})
            decision = followup.get("decision", details.get("decision"))
            confidence = followup.get("confidence", details.get("confidence"))
            if decision == "contradicts" and claim_id not in resolved_adjudication_ids:
                unresolved_contradictions.append(
                    {"matrix": matrix_name, "id": claim_id, "confidence": confidence}
                )
    gap_adjudication_checks = []
    for item in gap_adjudications:
        claim_id = item["id"]
        claim = gap_matrix["claimsById"][claim_id]
        attribute = questions_by_id[claim["question_id"]]["attribute"]
        current_value = people_by_id[claim["person_id"]]["attributes"][attribute]
        gap_adjudication_checks.append(
            {
                "id": claim_id,
                "previousAnswerChanged": float(item["previousAnswer"]) != float(item["answer"]),
                "currentJERVInputMatchesCatalog": float(claim["answer"]) == float(current_value),
                "currentAnswerMatchesAdjudication": float(current_value) == float(item["answer"]),
                "sourceURLsPresent": bool(item.get("sourceURLs")),
            }
        )
    matrix_question_statuses: dict[str, set[str]] = {}
    for matrix in (old_matrix, new_matrix, gap_matrix):
        for question_id, status in matrix["questionReviewStatusById"].items():
            matrix_question_statuses.setdefault(question_id, set()).add(status)
    final_question_statuses = character_review.get("question_reviews", {})
    final_question_ids = {
        question_id
        for question_id, item in final_question_statuses.items()
        if item.get("final_status") == "accepted"
    }
    final_question_ids.update(
        question_id
        for question_id, item in human_review.get("questionReviews", {}).items()
        if item.get("decision") == "accepted"
    )
    raw_human_question_ids = {
        question_id
        for question_id, statuses in matrix_question_statuses.items()
        if "human-review" in statuses
    }
    unresolved_question_ids = raw_human_question_ids - final_question_ids

    result = {
        "auditDate": date.today().isoformat(),
        "catalog": {
            "people": len(people),
            "basePeople": len(base["people"]),
            "expansionPeople": len(expansion["people"]),
            "uniqueQuestions": len({question["id"] for question in questions}),
            "categories": len({category for person in people for category in person["categories"]}),
            "attributeValues": sum(len(person["attributes"]) for person in people),
            "applicableAnswerCells": len(cells),
        },
        "expansionReproducibility": {
            "matchesGeneratorOutput": regenerated_expansion == expansion,
            "profiles": len(regenerated_expansion["people"]),
            "questions": len(regenerated_expansion["questions"]),
        },
        "answerMatrixCoverage": {
            "old73Batch": {
                "people": old_matrix["people"],
                "cells": old_matrix["cells"],
                "reviews": old_matrix["cellReviews"],
                "questionReviews": old_matrix["questionReviews"],
            },
            "new150Batch": {
                "people": new_matrix["people"],
                "cells": new_matrix["cells"],
                "reviews": new_matrix["cellReviews"],
                "questionReviews": new_matrix["questionReviews"],
                "adjudications": len(adjudicated_ids),
            },
            "previouslyUncoveredCells": {
                "people": gap_matrix["people"],
                "cells": gap_matrix["cells"],
                "reviews": gap_matrix["cellReviews"],
                "questionReviews": gap_matrix["questionReviews"],
            },
            "peopleWithMatrix": len(matrix_ids),
            "peopleWithoutMatrix": len(all_ids - matrix_ids),
            "expansionPeopleWithoutMatrix": sorted(expansion_ids - matrix_ids),
            "basePeopleWithoutMatrix": len(base_ids - matrix_ids),
            "coveredCells": len(reviewed_cells),
            "uncoveredApplicableCells": len(uncovered),
            "uncoveredCellPreview": [
                {"personId": person_id, "questionId": question_id}
                for person_id, question_id in sorted(uncovered)[:30]
            ],
            "modelAcceptedCells": accepted_by_model,
            "newBatchAdjudications": len(adjudicated_ids),
            "gapAdjudications": len(gap_adjudicated_ids),
            "contradictionAdjudications": len(contradiction_adjudicated_ids),
            "contradictionAdjudicationsVerifiedAgainstCurrentCatalog": sum(
                all(
                    check[key]
                    for key in (
                        "previousAnswerMatchesReviewedInput",
                        "targetedInputMatchesPreviousAnswer",
                        "jervFlaggedContradiction",
                        "currentAnswerMatchesAdjudication",
                        "sourceURLsPresent",
                    )
                )
                for check in contradiction_adjudication_checks
            ),
            "gapAdjudicationsVerifiedAgainstCurrentCatalog": sum(
                item["previousAnswerChanged"]
                and item["currentJERVInputMatchesCatalog"]
                and item["currentAnswerMatchesAdjudication"]
                and item["sourceURLsPresent"]
                for item in gap_adjudication_checks
            ),
            "documentedLegacyAdjudications": sorted(prior_documented_adjudications),
            "coveredCellsStillAwaitingHumanReview": covered_but_pending,
            "unresolvedContradictions": unresolved_contradictions,
        },
        "sourceCoverage": {
            "profilesInSourceManifest": len(source_ids),
            "profilesWithoutProfileSource": len(all_ids - source_ids),
            "baseProfilesWithoutSourceManifest": len(base_ids - source_ids),
            "matrixClaimsWithAnExcerpt": source_excerpt_claims,
            "matrixClaimSourceGranularity": "one profile excerpt is reused for claims; no per-claim source ledger exists",
        },
        "characterReview": {
            "finalSummary": character_review.get("final_summary", {}),
            "additionalManualQuestionReviews": len(human_review.get("questionReviews", {})),
            "additionalManualMainRoleReviews": len(human_review.get("claimReviews", {})),
        },
        "questionReviewCoverage": {
            "catalogQuestions": len({question["id"] for question in questions}),
            "questionsInMatrixReports": len(matrix_question_statuses),
            "matrixQuestionsWithoutReport": sorted({question["id"] for question in questions} - matrix_question_statuses.keys()),
            "rawQuestionHumanReviewFlags": sorted(raw_human_question_ids),
            "questionsStillWithoutFinalEditorialDisposition": sorted(unresolved_question_ids),
            "expansionQuestionsFinalAccepted": len(
                {question["id"] for question in expansion["questions"]} & final_question_ids
            ),
        },
        "crossFieldInvariants": invariants,
        "gapAdjudicationChecks": gap_adjudication_checks,
        "contradictionAdjudicationChecks": contradiction_adjudication_checks,
        "expansionGate": {
            "ready": not uncovered
            and covered_but_pending == 0
            and not unresolved_question_ids
            and regenerated_expansion == expansion
            and all(
                item["previousAnswerChanged"]
                and item["currentJERVInputMatchesCatalog"]
                and item["currentAnswerMatchesAdjudication"]
                and item["sourceURLsPresent"]
                for item in gap_adjudication_checks
            )
            and all(
                all(
                    check[key]
                    for key in (
                        "previousAnswerMatchesReviewedInput",
                        "targetedInputMatchesPreviousAnswer",
                        "jervFlaggedContradiction",
                        "currentAnswerMatchesAdjudication",
                        "sourceURLsPresent",
                    )
                )
                for check in contradiction_adjudication_checks
            )
            and not any(invariants.values()),
            "reason": "Requires complete answer-cell and question coverage, resolved human-review items, and no logical contradictions.",
        },
    }
    if include_details:
        pending_matrix_cells = []
        for matrix_name, matrix, resolved_ids in (
            ("old73", old_matrix, prior_documented_adjudications),
            ("new150", new_matrix, adjudicated_ids | contradiction_adjudicated_ids),
            ("previouslyUncovered", gap_matrix, gap_adjudicated_ids | contradiction_adjudicated_ids),
        ):
            for claim_id, status in matrix["reviewStatusById"].items():
                if status != "human-review" or claim_id in resolved_ids:
                    continue
                claim = matrix["claimsById"][claim_id]
                question = questions_by_id[claim["question_id"]]
                pending_matrix_cells.append(
                    {
                        "matrix": matrix_name,
                        "personId": claim["person_id"],
                        "personName": people_by_id[claim["person_id"]]["name"],
                        "questionId": claim["question_id"],
                        "question": question["text"],
                        "attribute": question["attribute"],
                        "proposedValue": claim["answer"],
                        "jervDecision": matrix["reviewDetailsById"].get(claim_id, {}).get("decision"),
                        "jervConfidence": matrix["reviewDetailsById"].get(claim_id, {}).get("confidence"),
                        "sourceUrl": claim.get("source_url"),
                        "sourceTitle": claim.get("source_title"),
                    }
                )

        result["details"] = {
            "pendingMatrixCells": pending_matrix_cells,
            "uncoveredApplicableCells": [
                {
                    "personId": person_id,
                    "personName": people_by_id[person_id]["name"],
                    "questionId": question_id,
                    "question": questions_by_id[question_id]["text"],
                    "attribute": questions_by_id[question_id]["attribute"],
                    "proposedValue": people_by_id[person_id]["attributes"][questions_by_id[question_id]["attribute"]],
                    "profileSourceUrl": next(
                        (item["sourceURL"] for item in sources if item.get("id") == person_id), None
                    ),
                }
                for person_id, question_id in sorted(uncovered)
            ],
            "questionReviewItems": [
                {
                    "questionId": question_id,
                    "question": questions_by_id[question_id]["text"],
                    "statusByMatrix": {
                        matrix_name: matrix["questionReviewStatusById"].get(question_id)
                        for matrix_name, matrix in (
                            ("old73", old_matrix),
                            ("new150", new_matrix),
                            ("previouslyUncovered", gap_matrix),
                        )
                        if question_id in matrix["questionReviewStatusById"]
                    },
                }
                for question_id in sorted(unresolved_question_ids)
            ],
            "profilesWithoutSourceManifest": [
                {"id": person["id"], "name": person["name"]}
                for person in people
                if person["id"] not in source_ids
            ],
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for a JSON audit report")
    parser.add_argument("--require-complete", action="store_true", help="Exit nonzero while any answer cell remains uncovered or unresolved")
    args = parser.parse_args()
    report = audit(include_details=args.output is not None)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        summary = {key: value for key, value in report.items() if key != "details"}
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(f"Detailed audit queue written to {args.output}")
    else:
        print(rendered)
    if args.require_complete and not report["expansionGate"]["ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
