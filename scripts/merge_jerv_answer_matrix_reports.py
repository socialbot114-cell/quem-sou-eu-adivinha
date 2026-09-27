#!/usr/bin/env python3
"""Merge category-sliced JERV answer-matrix reports conservatively."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

CATEGORY_BY_SLUG = {
    "artistas": "Artistas brasileiros",
    "cinema": "Cinema e TV",
    "creators": "Criadores digitais",
    "football": "Futebol",
    "history": "História",
    "kpop": "K-pop",
    "fashion": "Moda e reality",
    "music": "Música internacional",
    "sports": "Outros esportes",
    "world": "Personalidades mundiais",
    "politics": "Políticos",
    "technology": "Tecnologia e negócios",
}


def merge_reports(reports: list[dict], categories: list[str]) -> dict:
    if not reports:
        raise ValueError("at least one JERV report is required")

    claims: dict[str, dict] = {}
    questions: dict[str, dict] = {}
    category_names = set(categories)
    for report in reports:
        for claim_id, review in report.get("claim_reviews", {}).items():
            if claim_id in claims:
                raise ValueError(f"duplicate answer cell across JERV reports: {claim_id}")
            claims[claim_id] = review
        for question_id, review in report.get("question_reviews", {}).items():
            previous = questions.get(question_id)
            if previous is None:
                questions[question_id] = review
                continue
            decisions = set(previous.get("decisions", [previous["decision"]]))
            decisions.add(review["decision"])
            confidence = min(previous["confidence"], review["confidence"])
            if len(decisions) == 1:
                decision = next(iter(decisions))
                status = "accepted" if previous["status"] == review["status"] == "accepted" else "human-review"
                questions[question_id] = {"decision": decision, "confidence": confidence, "status": status}
            else:
                questions[question_id] = {
                    "decision": "conflicting-reviews",
                    "decisions": sorted(decisions),
                    "confidence": confidence,
                    "status": "human-review",
                }

    claim_statuses = Counter(item["status"] for item in claims.values())
    question_statuses = Counter(item["status"] for item in questions.values())
    people_ids = {claim_id.rsplit("--", 1)[0] for claim_id in claims}
    return {
        "model": reports[-1]["model"],
        "confidence_threshold": reports[-1]["confidence_threshold"],
        "evaluated_at": max(report["evaluated_at"] for report in reports),
        "scope": {
            "people": len(people_ids),
            "answer_cells": len(claims),
            "categories": sorted(category_names),
        },
        "question_reviews": questions,
        "claim_reviews": claims,
        "summary": {
            "questions_accepted": question_statuses["accepted"],
            "questions_for_human": len(questions) - question_statuses["accepted"],
            "claims_accepted": claim_statuses["accepted"],
            "claims_for_human": len(claims) - claim_statuses["accepted"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in args.reports]
    slugs = [path.stem.removeprefix("jerv150-").removesuffix("-report") for path in args.reports]
    unknown_slugs = set(slugs) - CATEGORY_BY_SLUG.keys()
    if unknown_slugs:
        raise ValueError(f"unrecognized category report filename(s): {sorted(unknown_slugs)}")
    result = merge_reports(reports, [CATEGORY_BY_SLUG[slug] for slug in slugs])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print(f"Merged {result['scope']['answer_cells']} answer cells for {result['scope']['people']} characters")


if __name__ == "__main__":
    main()
