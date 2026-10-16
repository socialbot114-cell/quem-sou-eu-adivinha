#!/usr/bin/env python3
"""Check an editorial wave against the rules of validate_content.py, per category and for the "Todos" mode.

Without --batch, the check runs on the catalog as build_character_expansion.build() produces it today, plus
knowledge.json. With --batch, the wave's people are built by build_batch_people (the builder's own logic) and
added to that catalog; a wave already listed in the builder is not added twice. --questions adds extra questions
the same way build() adds question-wave files (optional questions).

Rules reproduced (thresholds come from validate_content.py):
- at least MIN_PEOPLE_PER_CATEGORY people in the category;
- useful questions: coverage >= 80% and at least two distinct values; at least MIN_USEFUL_QUESTIONS of them;
- no two people of the category with the same signature over the useful questions;
- every question that applies to the category covers >= 80% of it; Todos questions cover 100%;
- no two people of the whole catalog with the same signature over all questions ("Todos" mode);
- no duplicate ids or names (validate_content.py T8).

Not reproduced here: JERV review, sources, image credits and JSON schema checks. Run validate_content.py for those.

Exit codes: 0 no failures, 1 failures found, 2 the inputs could not be read or built.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))

import build_character_expansion as builder  # noqa: E402
from validate_content import (  # noqa: E402
    CONTENT_PATH,
    GLOBAL_CATEGORY,
    MIN_ATTRIBUTE_COVERAGE,
    MIN_PEOPLE_PER_CATEGORY,
    MIN_USEFUL_QUESTIONS,
    PLAYABLE_CATEGORIES,
)


def load_catalog(batch_path: Path | None, questions_path: Path | None) -> tuple[list[dict], list[dict], list[str], bool]:
    """Return people, questions, the ids of the wave's people, and whether the wave was already inside the builder."""
    extra_questions: list[dict] = []
    if questions_path is not None and questions_path.resolve() not in {path.resolve() for path in builder.question_wave_paths()}:
        extra_questions = builder.load_question_file(questions_path)

    extra_batches: list[Path] = []
    builder_batches = {path.resolve() for path in builder.batch_wave_paths()}
    builder_batches |= {builder.BATCH_150.resolve(), builder.BATCH_200.resolve(), builder.BATCH_BANK_FUTEBOL.resolve()}
    already_in_builder = batch_path is not None and batch_path.resolve() in builder_batches
    if batch_path is not None and not already_in_builder:
        extra_batches.append(batch_path)

    built = builder.build(extra_questions=extra_questions, extra_batches=extra_batches)
    primary = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    people = primary["people"] + built["people"]
    questions = primary["questions"] + built["questions"]

    wave_ids: list[str] = []
    if batch_path is not None:
        batch = json.loads(batch_path.read_text(encoding="utf-8"))
        wave_ids = [entry["id"] for entries in batch["people"].values() for entry in entries]
    return people, questions, wave_ids, already_in_builder


def category_check(category: str, people: list[dict], questions: list[dict]) -> dict:
    candidates = [person for person in people if category in person["categories"]]
    failures = []
    if len(candidates) < MIN_PEOPLE_PER_CATEGORY:
        failures.append(f"{len(candidates)} pessoas; mínimo {MIN_PEOPLE_PER_CATEGORY}")

    eligible = [question for question in questions if GLOBAL_CATEGORY in question["categories"] or category in question["categories"]]
    rows = []
    for question in eligible:
        attribute = question["attribute"]
        values = [person["attributes"][attribute] for person in candidates if attribute in person["attributes"]]
        coverage = len(values) / len(candidates) if candidates else 0.0
        distinct = len(set(values))
        is_global = GLOBAL_CATEGORY in question["categories"]
        row = {
            "id": question["id"],
            "attribute": attribute,
            "text": question["text"],
            "global": is_global,
            "people_with_value": len(values),
            "coverage": round(coverage, 4),
            "distinct_values": distinct,
            "useful": coverage >= MIN_ATTRIBUTE_COVERAGE and distinct > 1,
        }
        rows.append(row)
        if is_global and coverage != 1:
            failures.append(f"pergunta de Todos {question['id']} precisa cobrir 100% da categoria")

    below = [row["id"] for row in rows if row["coverage"] < MIN_ATTRIBUTE_COVERAGE]
    if below:
        failures.append(f"{len(below)} pergunta(s) com cobertura abaixo de 80%")

    useful_questions = [question for question, row in zip(eligible, rows) if row["useful"]]
    if len(useful_questions) < MIN_USEFUL_QUESTIONS:
        failures.append(f"{len(useful_questions)} perguntas úteis; mínimo {MIN_USEFUL_QUESTIONS}")

    signatures: dict[tuple, list[str]] = {}
    for person in candidates:
        signature = tuple(person["attributes"].get(question["attribute"]) for question in useful_questions)
        signatures.setdefault(signature, []).append(person["id"])
    collisions = [ids for ids in signatures.values() if len(ids) > 1]
    if collisions:
        failures.append(f"{len(collisions)} grupo(s) de pessoas indistinguíveis pelas perguntas úteis")

    return {
        "category": category,
        "people": len(candidates),
        "eligible_questions": len(eligible),
        "useful_questions": len(useful_questions),
        "questions": rows,
        "below_80_percent": below,
        "collisions": collisions,
        "failures": failures,
    }


def todos_check(people: list[dict], questions: list[dict]) -> dict:
    attributes = [question["attribute"] for question in questions]
    signatures: dict[tuple, list[str]] = {}
    for person in people:
        signature = tuple(person["attributes"].get(attribute) for attribute in attributes)
        signatures.setdefault(signature, []).append(person["id"])
    collisions = [ids for ids in signatures.values() if len(ids) > 1]
    failures = [f"{len(collisions)} grupo(s) de pessoas indistinguíveis no modo Todos"] if collisions else []
    return {"people": len(people), "questions": len(questions), "collisions": collisions, "failures": failures}


def identity_check(people: list[dict]) -> dict:
    ids: dict[str, int] = {}
    names: dict[str, int] = {}
    for person in people:
        ids[person["id"]] = ids.get(person["id"], 0) + 1
        names[person["name"].casefold()] = names.get(person["name"].casefold(), 0) + 1
    duplicate_ids = sorted(identifier for identifier, count in ids.items() if count > 1)
    duplicate_names = sorted(name for name, count in names.items() if count > 1)
    failures = []
    if duplicate_ids:
        failures.append(f"ids duplicados: {duplicate_ids}")
    if duplicate_names:
        failures.append(f"nomes duplicados: {duplicate_names}")
    return {"duplicate_ids": duplicate_ids, "duplicate_names": duplicate_names, "failures": failures}


def format_text(report: dict, verbose: bool) -> str:
    lines = []
    source = report["batch"] or "catálogo atual (build_character_expansion.build() + knowledge.json)"
    lines.append(f"Lote: {source}")
    if report["batch"]:
        lines.append(f"Pessoas do lote: {report['wave_people']} (já incluído no construtor: {report['batch_already_in_builder']})")
    if report["questions"]:
        lines.append(f"Perguntas extras: {report['questions']}")
    lines.append(f"Catálogo: {report['catalog_people']} pessoas, {report['catalog_questions']} perguntas")
    lines.append("")
    for category in report["categories"]:
        status = "OK" if not category["failures"] else "FALHA"
        lines.append(
            f"{category['category']}: {category['people']} pessoas, "
            f"{category['useful_questions']}/{category['eligible_questions']} perguntas úteis, "
            f"colisões {len(category['collisions'])} -> {status}"
        )
        below = [row for row in category["questions"] if row["coverage"] < MIN_ATTRIBUTE_COVERAGE]
        if below:
            for row in below:
                lines.append(f"    abaixo de 80%: {row['id']} ({row['attribute']}) cobertura {row['coverage'] * 100:.1f}%")
        else:
            lines.append("    perguntas abaixo de 80%: nenhuma")
        if category["collisions"]:
            lines.append(f"    colisões (primeiros 5 grupos): {category['collisions'][:5]}")
        if verbose:
            for row in category["questions"]:
                useful = "útil" if row["useful"] else "não útil"
                lines.append(
                    f"    {row['id']:32s} {row['coverage'] * 100:6.1f}%  valores distintos {row['distinct_values']}  {useful}"
                )
    todos = report["todos"]
    lines.append(
        f"Todos: {todos['people']} pessoas, {todos['questions']} perguntas, colisões {len(todos['collisions'])}"
        f" -> {'OK' if not todos['failures'] else 'FALHA'}"
    )
    if todos["collisions"]:
        lines.append(f"    colisões (primeiros 5 grupos): {todos['collisions'][:5]}")
    identity = report["identity"]
    lines.append(f"Identidade: {'OK' if not identity['failures'] else 'FALHA'}")
    lines.append("")
    if report["failures"]:
        lines.append(f"Resultado: REPROVADO ({len(report['failures'])} falha(s))")
        lines.extend(f"  - {failure}" for failure in report["failures"])
    else:
        lines.append("Resultado: APROVADO")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--batch", type=Path, help="wave file {\"people\": {\"<Categoria>\": [entradas]}}")
    parser.add_argument("--questions", type=Path, help="extra questions: a JSON list of {id, text, attribute, categories}")
    parser.add_argument("--category", action="append", help="category to check (repeatable); default: the batch's categories, or all playable ones")
    parser.add_argument("--report", type=Path, help="write the full report as JSON here")
    parser.add_argument("--json", action="store_true", help="print the JSON report to stdout instead of the text report")
    parser.add_argument("--verbose", action="store_true", help="also list every question's coverage in each category")
    args = parser.parse_args()

    for path in (args.batch, args.questions):
        if path is not None and not path.is_file():
            parser.error(f"file not found: {path}")
    try:
        batch_categories = None
        if args.batch is not None:
            batch = json.loads(args.batch.read_text(encoding="utf-8"))
            if not isinstance(batch, dict) or set(batch) != {"people"} or not isinstance(batch["people"], dict):
                raise ValueError(f"{args.batch.name} must contain a people object keyed by category")
            batch_categories = list(batch["people"])
        people, questions, wave_ids, already_in_builder = load_catalog(args.batch, args.questions)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print(f"Erro ao montar o catálogo: {error}", file=sys.stderr)
        return 2

    categories = args.category or batch_categories or sorted(PLAYABLE_CATEGORIES)
    unknown = [category for category in categories if category not in PLAYABLE_CATEGORIES]
    if unknown:
        parser.error(f"unknown category: {unknown}")

    category_reports = [category_check(category, people, questions) for category in categories]
    todos = todos_check(people, questions)
    identity = identity_check(people)
    failures = [f"{report['category']}: {failure}" for report in category_reports for failure in report["failures"]]
    failures += [f"Todos: {failure}" for failure in todos["failures"]]
    failures += [f"identidade: {failure}" for failure in identity["failures"]]

    report = {
        "batch": str(args.batch) if args.batch else None,
        "questions": str(args.questions) if args.questions else None,
        "wave_people": len(wave_ids),
        "batch_already_in_builder": already_in_builder,
        "catalog_people": len(people),
        "catalog_questions": len(questions),
        "categories": category_reports,
        "todos": todos,
        "identity": identity,
        "failures": failures,
        "passed": not failures,
    }
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_text(report, args.verbose))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
