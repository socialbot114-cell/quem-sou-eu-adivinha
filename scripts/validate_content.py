#!/usr/bin/env python3
import json
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
print(f"Conteúdo válido: {len(people)} pessoas, {len(questions)} perguntas")
