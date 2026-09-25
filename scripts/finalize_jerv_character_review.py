#!/usr/bin/env python3
"""Combine Jev judgments with explicitly documented editorial reviews."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
REPORT_PATH = ROOT / "docs/content/jerv-character-review-report.json"
HUMAN_PATH = ROOT / "docs/content/jerv-character-human-review.json"
OUTPUT_PATH = ROOT / "docs/content/jerv-character-review-final.json"


def finalize(report: dict, human: dict) -> dict:
    result = json.loads(json.dumps(report))
    for section, manual_key in (("question_reviews", "questionReviews"), ("claim_reviews", "claimReviews")):
        manual = human.get(manual_key, {})
        for identifier, review in result[section].items():
            human_review = manual.get(identifier)
            if human_review:
                review["editorial_review"] = human_review
                review["final_status"] = "accepted" if human_review["decision"] in ("accepted", "supports") else "rejected"
            else:
                review["final_status"] = "accepted" if review["status"] == "accepted" else "pending-human"
    result["editorial_reviewed_at"] = human.get("reviewedAt")
    result["editorial_reviewer"] = human.get("reviewer")
    result["final_summary"] = {
        "questions_accepted": sum(item["final_status"] == "accepted" for item in result["question_reviews"].values()),
        "questions_pending": sum(item["final_status"] == "pending-human" for item in result["question_reviews"].values()),
        "claims_accepted": sum(item["final_status"] == "accepted" for item in result["claim_reviews"].values()),
        "claims_pending": sum(item["final_status"] == "pending-human" for item in result["claim_reviews"].values()),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--human-review", type=Path, default=HUMAN_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    human = json.loads(args.human_review.read_text(encoding="utf-8"))
    result = finalize(report, human)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["final_summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
