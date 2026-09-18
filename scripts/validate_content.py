#!/usr/bin/env python3
import json
import math
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parents[1]
CONTENT_PATH = ROOT / "iosApp/Resources/KnowledgeBase/knowledge.json"
CREDITS_PATH = ROOT / "docs/content/image-credits.json"
CHARACTERS_PATH = ROOT / "iosApp/Resources/Characters"
CATEGORIES = {
    "Criadores digitais",
    "Futebol",
    "Artistas brasileiros",
    "Políticos",
    "História",
    "Personalidades mundiais",
    "Todos",
}
PLAYABLE_CATEGORIES = CATEGORIES - {"Todos"}
GLOBAL_CATEGORY = "Todos"
MIN_PEOPLE_PER_CATEGORY = 12
MIN_USEFUL_QUESTIONS = 6
MIN_ATTRIBUTE_COVERAGE = 0.8
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ATTRIBUTE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
REQUIRED_PERSON_FIELDS = {
    "id",
    "name",
    "categories",
    "country",
    "profession",
    "attributes",
    "avatarSymbol",
}
OPTIONAL_MEDIA_FIELDS = {"imageName"}
REQUIRED_QUESTION_FIELDS = {"id", "text", "attribute", "categories"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def require_string(value, label):
    require(isinstance(value, str) and value.strip() == value and value, f"{label} deve ser texto não vazio e sem espaços externos")


def validate_categories(value, label, *, allow_all):
    require(isinstance(value, list) and value, f"{label} deve ser uma lista não vazia")
    require(all(isinstance(item, str) for item in value), f"{label} contém categoria que não é texto")
    require(len(value) == len(set(value)), f"{label} contém categorias duplicadas")
    invalid = set(value) - CATEGORIES
    require(not invalid, f"{label} contém categorias inválidas: {sorted(invalid)}")
    if not allow_all:
        require(GLOBAL_CATEGORY not in value, f"{label} não pode usar {GLOBAL_CATEGORY}")


def load_image_credits():
    try:
        data = json.loads(CREDITS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise AssertionError(f"Manifesto de créditos ausente: {CREDITS_PATH}") from error
    except json.JSONDecodeError as error:
        raise AssertionError(f"JSON de créditos inválido: {error}") from error
    require(isinstance(data, dict) and isinstance(data.get("items"), list), "Manifesto de créditos deve conter uma lista items")
    credits = {}
    for index, item in enumerate(data["items"]):
        label = f"image-credits.items[{index}]"
        require(isinstance(item, dict), f"{label} deve ser um objeto")
        for field in ("id", "name", "file", "reviewStatus"):
            require_string(item.get(field), f"{label}.{field}")
        require(ID_PATTERN.fullmatch(item["id"]), f"{label}.id deve ser um slug ASCII")
        require(item["id"] not in credits, f"Crédito de imagem duplicado: {item['id']}")
        require(item["reviewStatus"] == "approved-visual-and-credit-review", f"Retrato não aprovado: {item['id']}")
        expected_file = f"iosApp/Resources/Characters/{item['id']}.jpg"
        require(item["file"] == expected_file, f"Caminho de crédito inesperado para {item['id']}: {item['file']}")
        image_path = ROOT / item["file"]
        require(image_path.is_file(), f"Arquivo creditado não existe: {item['file']}")
        credits[item["id"]] = item
    return credits


def validate_media(person, label, image_credits):
    if "imageName" not in person:
        return
    image_name = person["imageName"]
    require_string(image_name, f"{label}.imageName")
    require(Path(image_name).name == image_name, f"{label}.imageName deve conter somente o nome do arquivo")
    require(Path(image_name).suffix == ".jpg", f"{label}.imageName deve usar extensão .jpg")
    require(image_name == f"{person['id']}.jpg", f"{label}.imageName deve corresponder ao ID da pessoa")
    require((CHARACTERS_PATH / image_name).is_file(), f"Imagem não encontrada para {person['id']}: {image_name}")
    require(person["id"] in image_credits, f"Imagem sem entrada de crédito: {person['id']}")


def load_content():
    try:
        data = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise AssertionError(f"JSON inválido: {error}") from error
    require(isinstance(data, dict), "A raiz deve ser um objeto")
    require(set(data) == {"people", "questions"}, "A raiz deve conter somente people e questions")
    require(isinstance(data["people"], list), "people deve ser uma lista")
    require(isinstance(data["questions"], list), "questions deve ser uma lista")
    return data


def validate_people(people, known_attributes, image_credits):
    require(people, "A base deve conter pessoas")
    seen_ids = set()
    seen_names = set()
    for index, person in enumerate(people):
        label = f"people[{index}]"
        require(isinstance(person, dict), f"{label} deve ser um objeto")
        missing = REQUIRED_PERSON_FIELDS - person.keys()
        unknown = person.keys() - REQUIRED_PERSON_FIELDS - OPTIONAL_MEDIA_FIELDS
        require(not missing, f"{label} não contém: {sorted(missing)}")
        require(not unknown, f"{label} contém campos desconhecidos: {sorted(unknown)}")
        for field in ("id", "name", "country", "profession", "avatarSymbol"):
            require_string(person[field], f"{label}.{field}")
        require(ID_PATTERN.fullmatch(person["id"]), f"{label}.id deve ser um slug ASCII")
        require(person["id"] not in seen_ids, f"ID de pessoa duplicado: {person['id']}")
        normalized_name = person["name"].casefold()
        require(normalized_name not in seen_names, f"Nome de pessoa duplicado: {person['name']}")
        seen_ids.add(person["id"])
        seen_names.add(normalized_name)
        validate_categories(person["categories"], f"{label}.categories", allow_all=False)
        attributes = person["attributes"]
        require(isinstance(attributes, dict) and attributes, f"{label}.attributes deve ser um objeto não vazio")
        unknown_attributes = attributes.keys() - known_attributes
        require(not unknown_attributes, f"{label} usa atributos sem pergunta: {sorted(unknown_attributes)}")
        for attribute, value in attributes.items():
            require(isinstance(attribute, str) and ATTRIBUTE_PATTERN.fullmatch(attribute), f"Atributo inválido em {label}: {attribute!r}")
            require(not isinstance(value, bool) and isinstance(value, (int, float)), f"{label}.{attribute} deve ser numérico")
            require(math.isfinite(value) and 0 <= value <= 1, f"{label}.{attribute} deve estar entre 0 e 1")
        validate_media(person, label, image_credits)
    people_with_images = {person["id"] for person in people if "imageName" in person}
    require(people_with_images == set(image_credits), f"Retratos aprovados não integrados ou sem uso: {sorted(set(image_credits) - people_with_images)}")
    return len(people_with_images)


def validate_questions(questions):
    require(questions, "A base deve conter perguntas")
    seen_ids = set()
    seen_texts = set()
    seen_attributes = set()
    for index, question in enumerate(questions):
        label = f"questions[{index}]"
        require(isinstance(question, dict), f"{label} deve ser um objeto")
        require(set(question) == REQUIRED_QUESTION_FIELDS, f"{label} deve conter exatamente {sorted(REQUIRED_QUESTION_FIELDS)}")
        for field in ("id", "text", "attribute"):
            require_string(question[field], f"{label}.{field}")
        require(ID_PATTERN.fullmatch(question["id"]), f"{label}.id deve ser um slug ASCII")
        require(ATTRIBUTE_PATTERN.fullmatch(question["attribute"]), f"{label}.attribute inválido")
        require(question["id"] not in seen_ids, f"ID de pergunta duplicado: {question['id']}")
        require(question["text"].casefold() not in seen_texts, f"Texto de pergunta duplicado: {question['text']}")
        require(question["attribute"] not in seen_attributes, f"Atributo possui mais de uma pergunta: {question['attribute']}")
        require(question["text"].endswith("?"), f"Pergunta sem ponto de interrogação: {question['id']}")
        seen_ids.add(question["id"])
        seen_texts.add(question["text"].casefold())
        seen_attributes.add(question["attribute"])
        validate_categories(question["categories"], f"{label}.categories", allow_all=True)
        if GLOBAL_CATEGORY in question["categories"]:
            require(question["categories"] == [GLOBAL_CATEGORY], f"{label}: Todos deve aparecer sozinho")
    return seen_attributes


def validate_coverage_and_signatures(people, questions):
    counts = Counter(category for person in people for category in person["categories"])
    missing_categories = PLAYABLE_CATEGORIES - counts.keys()
    require(not missing_categories, f"Categorias sem pessoas: {sorted(missing_categories)}")

    category_metrics = {}
    for category in sorted(PLAYABLE_CATEGORIES):
        candidates = [person for person in people if category in person["categories"]]
        require(len(candidates) >= MIN_PEOPLE_PER_CATEGORY, f"Categoria {category} tem {len(candidates)} pessoas; mínimo: {MIN_PEOPLE_PER_CATEGORY}")
        eligible = [question for question in questions if GLOBAL_CATEGORY in question["categories"] or category in question["categories"]]
        useful = []
        for question in eligible:
            attribute = question["attribute"]
            values = [person["attributes"][attribute] for person in candidates if attribute in person["attributes"]]
            coverage = len(values) / len(candidates)
            if GLOBAL_CATEGORY in question["categories"]:
                require(coverage == 1, f"Pergunta global {question['id']} não cobre toda a categoria {category}")
            if coverage >= MIN_ATTRIBUTE_COVERAGE and len(set(values)) > 1:
                useful.append(question)

        require(len(useful) >= MIN_USEFUL_QUESTIONS, f"Categoria {category} tem só {len(useful)} perguntas úteis; mínimo: {MIN_USEFUL_QUESTIONS}")
        signatures = {}
        for person in candidates:
            signature = tuple(person["attributes"].get(question["attribute"]) for question in useful)
            signatures.setdefault(signature, []).append(person["id"])
        collisions = [ids for ids in signatures.values() if len(ids) > 1]
        require(not collisions, f"Pessoas indistinguíveis em {category}: {collisions}")
        category_metrics[category] = (len(candidates), len(eligible), len(useful))

    all_attributes = [question["attribute"] for question in questions]
    all_signatures = {}
    for person in people:
        signature = tuple(person["attributes"].get(attribute) for attribute in all_attributes)
        all_signatures.setdefault(signature, []).append(person["id"])
    all_collisions = [ids for ids in all_signatures.values() if len(ids) > 1]
    require(not all_collisions, f"Pessoas indistinguíveis no modo Todos: {all_collisions}")

    unused = []
    for question in questions:
        relevant_people = people if GLOBAL_CATEGORY in question["categories"] else [
            person for person in people if set(person["categories"]) & set(question["categories"])
        ]
        values = [person["attributes"][question["attribute"]] for person in relevant_people if question["attribute"] in person["attributes"]]
        coverage = len(values) / len(relevant_people) if relevant_people else 0
        if coverage < MIN_ATTRIBUTE_COVERAGE or len(set(values)) < 2:
            unused.append(question["id"])
    require(not unused, f"Perguntas sem cobertura ou poder discriminante: {unused}")
    return category_metrics


def main():
    data = load_content()
    image_credits = load_image_credits()
    questions = data["questions"]
    people = data["people"]
    known_attributes = validate_questions(questions)
    image_count = validate_people(people, known_attributes, image_credits)
    metrics = validate_coverage_and_signatures(people, questions)
    print(f"Conteúdo válido: {len(people)} pessoas, {len(questions)} perguntas, {len(known_attributes)} atributos, {image_count} retratos creditados")
    for category, (candidate_count, eligible_count, useful_count) in metrics.items():
        print(f"- {category}: {candidate_count} pessoas, {useful_count}/{eligible_count} perguntas úteis")


if __name__ == "__main__":
    main()
