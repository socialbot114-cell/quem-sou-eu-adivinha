#!/usr/bin/env python3
import json
import math
from pathlib import Path

path = Path(__file__).parents[1] / "iosApp/Resources/KnowledgeBase/knowledge.json"
data = json.loads(path.read_text())
people = data["people"]
questions = data["questions"]
ids = [p["id"] for p in people]
assert len(ids) == len(set(ids)), "IDs de pessoas duplicados"
assert len({q["id"] for q in questions}) == len(questions), "IDs de perguntas duplicados"
assert all(p["name"] and p["categories"] and p["attributes"] for p in people), "Pessoa incompleta"
assert all(q["text"] and q["attribute"] for q in questions), "Pergunta incompleta"
assert all(math.isfinite(value) and 0 <= value <= 1 for person in people for value in person["attributes"].values()), "Atributos devem estar entre 0 e 1"

categories = {category for person in people for category in person["categories"]}
question_attributes = {question["attribute"] for question in questions}
assert all(question["attribute"] in question_attributes for question in questions), "Pergunta sem atributo"
for category in categories:
    candidates = [person for person in people if category in person["categories"]]
    if len(candidates) < 3:
        continue
    eligible = [question for question in questions if "Todos" in question["categories"] or category in question["categories"]]
    useful = [question for question in eligible if sum(question["attribute"] in person["attributes"] for person in candidates) >= 2]
    assert len(useful) >= 3, f"Categoria {category} não tem perguntas suficientes"
    signatures = {tuple(person["attributes"].get(question["attribute"]) for question in useful) for person in candidates}
    assert len(signatures) == len(candidates), f"Pessoas indistinguíveis em {category}"
print(f"Conteúdo válido: {len(people)} pessoas, {len(questions)} perguntas")
