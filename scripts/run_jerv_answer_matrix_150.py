#!/usr/bin/env python3
"""Run JERV answer-cell reviews category by category for the 150-person batch."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import build_jerv_answer_matrix as matrix_builder
from merge_jerv_answer_matrix_reports import CATEGORY_BY_SLUG, merge_reports

ROOT = Path(__file__).parents[1]
PRIMARY_PATH = ROOT / "iosApp/Resources/KnowledgeBase/knowledge.json"
EXPANSION_PATH = ROOT / "iosApp/Resources/KnowledgeBase/character-expansion.json"
SOURCES_PATH = ROOT / "docs/content/character-sources.json"
BATCH_PATH = ROOT / "scripts/character-batch-150.json"
WORKER_PATH = ROOT.parent / "SKIILS/jerv/worker/review_character_content.py"
INPUT_OUTPUT = ROOT / "docs/content/jerv-answer-matrix-150-input.json"
REPORT_OUTPUT = ROOT / "docs/content/jerv-answer-matrix-150-report.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--input-output", type=Path, default=INPUT_OUTPUT)
    parser.add_argument("--output", type=Path, default=REPORT_OUTPUT)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise RuntimeError("TYPESAFE_API_KEY is not configured")
    if not WORKER_PATH.is_file():
        raise FileNotFoundError(f"JERV worker not found: {WORKER_PATH}")

    primary = json.loads(PRIMARY_PATH.read_text(encoding="utf-8"))
    expansion = json.loads(EXPANSION_PATH.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    batch = json.loads(BATCH_PATH.read_text(encoding="utf-8"))["people"]
    person_ids_by_category = {
        category: {person["id"] for person in people}
        for category, people in batch.items()
    }
    all_person_ids = set().union(*person_ids_by_category.values())
    if len(all_person_ids) != 150:
        raise ValueError(f"expected 150 distinct new characters, got {len(all_person_ids)}")

    full_input = matrix_builder.build(primary, expansion, sources, person_ids=all_person_ids)
    if full_input["scope"]["answer_cells"] != sum(
        len(matrix_builder.build(primary, expansion, sources, person_ids=ids)["claims"])
        for ids in person_ids_by_category.values()
    ):
        raise AssertionError("category-sliced answer cells do not add up to the full batch")
    args.input_output.parent.mkdir(parents=True, exist_ok=True)
    args.input_output.write_text(json.dumps(full_input, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    category_reports = []
    with tempfile.TemporaryDirectory(prefix="jerv-answer-matrix-150-") as temporary_directory:
        temporary = Path(temporary_directory)
        for index, (category, person_ids) in enumerate(person_ids_by_category.items()):
            category_input = matrix_builder.build(primary, expansion, sources, person_ids=person_ids)
            input_path = temporary / f"category-{index}.json"
            report_path = temporary / f"report-{index}.json"
            input_path.write_text(json.dumps(category_input, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            command = [
                sys.executable,
                str(WORKER_PATH),
                str(input_path),
                "--output",
                str(report_path),
                "--batch-size",
                str(args.batch_size),
            ]
            for attempt in range(3):
                try:
                    subprocess.run(command, check=True, cwd=ROOT)
                    break
                except subprocess.CalledProcessError:
                    if attempt == 2:
                        raise
                    time.sleep(2**attempt)
            category_reports.append(json.loads(report_path.read_text(encoding="utf-8")))

    result = merge_reports(category_reports, list(person_ids_by_category))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print(f"JERV reviewed {result['scope']['answer_cells']} cells for {result['scope']['people']} characters")


if __name__ == "__main__":
    main()
