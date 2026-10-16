#!/usr/bin/env python3
"""Runs scripts/check_wave.py on the Futebol-2 wave with the club facts of the existing footballers applied.

Integration simulated in a temporary folder (nothing in the repo is written):
- docs/content/optional-facts.json plus this wave's optional-facts.json, read by the builder and by
  apply_primary_category_features.apply (the same path the integrator uses);
- a temporary copy of iosApp/Resources/KnowledgeBase/knowledge.json with those facts applied to the 17
  primary footballers, used as the base catalog of check_wave.

Usage: python3 docs/content/waves/futebol-2/verificar_com_fatos.py [--verbose] [--report PATH]
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
import apply_primary_category_features as features  # noqa: E402
import check_wave  # noqa: E402

WAVE_DIR = ROOT / "docs/content/waves/futebol-2"
BATCH = ROOT / "scripts/character-batch-wave-futebol-2.json"
QUESTIONS = ROOT / "scripts/question-wave-futebol-2.json"


def main() -> int:
    app_facts = json.loads((ROOT / "docs/content/optional-facts.json").read_text(encoding="utf-8"))["characters"]
    wave_facts = json.loads((WAVE_DIR / "optional-facts.json").read_text(encoding="utf-8"))["characters"]
    merged = {"characters": {identifier: {**entry, "attributes": dict(entry.get("attributes", {}))} for identifier, entry in app_facts.items()}}
    for identifier, entry in wave_facts.items():
        target = merged["characters"].setdefault(identifier, {"attributes": {}})
        clash = set(target["attributes"]) & set(entry["attributes"])
        if clash:
            raise SystemExit(f"atributos repetidos para {identifier}: {sorted(clash)}")
        target["attributes"].update(entry["attributes"])

    temp = Path(tempfile.mkdtemp(prefix="futebol-2-"))
    try:
        merged_path = temp / "optional-facts.json"
        merged_path.write_text(json.dumps(merged, ensure_ascii=False), encoding="utf-8")
        features.OPTIONAL_FACTS_PATH = merged_path
        knowledge = temp / "knowledge.json"
        shutil.copy(features.PRIMARY_PATH, knowledge)
        features.apply(knowledge)
        check_wave.CONTENT_PATH = knowledge
        passthrough = sys.argv[1:]
        sys.argv = ["check_wave.py", "--batch", str(BATCH), "--questions", str(QUESTIONS), *passthrough]
        status = check_wave.main()
        import build_character_expansion as builder
        import validate_content as validator
        primary = json.loads(knowledge.read_text(encoding="utf-8"))
        built = builder.build()
        people = primary["people"] + built["people"]
        questions = primary["questions"] + built["questions"]
        try:
            validator.validate_coverage_and_signatures(people, questions)
            print("validate_content.validate_coverage_and_signatures: APROVADO")
        except AssertionError as error:
            print(f"validate_content.validate_coverage_and_signatures: REPROVADO: {str(error)[:300]}")
            status = 1
        return status
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
