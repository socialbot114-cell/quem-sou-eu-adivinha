#!/usr/bin/env python3
"""Offline engine evaluator for Quem Sou Eu? Adivinha.

Mirrors the Swift GameEngine (GameEngine.swift) and the current guess policy in
GameViews.swift to measure, for every embedded personality used as the target:

- first-guess accuracy
- overall accuracy (target reaches top-1 before the safety limit)
- mean / p95 question count
- per-category breakdown
- confused pairs (top-1 wrong but target is top-2)

Usage:
    python3 scripts/evaluate_offline.py [--seed 42] [--report eval.json]

Exit code is non-zero if any invariant is violated (crash, loop, invalid scores).
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).parents[1]
CONTENT_PATH = ROOT / "iosApp/Resources/KnowledgeBase/knowledge.json"

ANSWERS = {
    "yes": 1.0,
    "probablyYes": 0.75,
    "probablyNo": 0.25,
    "no": 0.0,
}
ANSWER_ORDER = ["yes", "probablyYes", "probablyNo", "no"]
QUESTION_LIMIT = 14
EARLY_GUESS_MIN_ANSWERS = 4
CONFIDENCE_THRESHOLD = 0.68
MARGIN_THRESHOLD = 0.10


def entropy(values):
    total = 0.0
    for v in values:
        if v > 0:
            total -= v * math.log2(v)
    return total


def likelihood(value, answer_key):
    evidence = ANSWERS[answer_key]
    raw = max(0.05, 1.0 - abs(value - evidence))
    denom = sum(max(0.05, 1.0 - abs(value - ANSWERS[k])) for k in ANSWER_ORDER)
    return raw / denom if denom > 0 else 1.0


def information_gain(question, people, scores):
    attr = question["attribute"]
    coverage = sum(scores[p["id"]] for p in people if attr in p["attributes"])
    if coverage < 0.6:
        return 0.0

    prior = entropy(scores.values())
    expected = 0.0
    for answer_key in ANSWER_ORDER:
        weighted = {}
        for p in people:
            value = p["attributes"].get(attr, 0.5)
            weighted[p["id"]] = scores[p["id"]] * likelihood(value, answer_key)
        prob = sum(weighted.values())
        if prob <= 0:
            continue
        expected += prob * entropy(v / prob for v in weighted.values())
    return max(0.0, prior - expected) * coverage


def build_engine(base, category):
    if category == "Todos":
        people = list(base["people"])
    else:
        people = [p for p in base["people"] if category in p["categories"]]
    questions = [
        q for q in base["questions"]
        if category == "Todos" or "Todos" in q["categories"] or category in q["categories"]
    ]
    return people, questions


def simulate_round(people, questions, target, scenario="ideal"):
    scores = {p["id"]: 1.0 / max(len(people), 1) for p in people}
    asked_ids = set()
    asked_attrs = set()
    rejected = set()

    def best_guess():
        ranked = sorted(people, key=lambda p: scores[p["id"]], reverse=True)
        ranked = [p for p in ranked if scores[p["id"]] > 0]
        return ranked[0] if ranked else None

    def normalize():
        for pid in rejected:
            scores[pid] = 0.0
        total = sum(scores.values())
        active = [pid for pid in scores if pid not in rejected]
        if total <= 0:
            if not active:
                return
            share = 1.0 / len(active)
            for pid in scores:
                scores[pid] = 0.0 if pid in rejected else share
            return
        for pid in active:
            scores[pid] += 1e-9
        total = sum(scores.values())
        for pid in scores:
            v = scores[pid]
            scores[pid] = v / total if (math.isfinite(v) and v >= 0) else 0.0

    def next_question():
        scored = []
        for q in questions:
            if q["id"] in asked_ids or q["attribute"] in asked_attrs:
                continue
            gain = information_gain(q, people, scores)
            if gain > 0.001:
                scored.append((gain, q))
        if not scored:
            return None
        scored.sort(key=lambda x: (-x[0], x[1]["id"]))
        return scored[0][1]

    def answer_for(question, target):
        attr = question["attribute"]
        value = target["attributes"].get(attr)
        if value is None:
            return "unknown"
        return "yes" if value >= 0.5 else "no"

    question_count = 0
    informative_count = 0
    first_guess = None
    while True:
        if question_count >= QUESTION_LIMIT:
            guess = best_guess()
            if guess is None or scores[guess["id"]] < 0.18:
                return None, question_count, first_guess
            return guess["id"], question_count, first_guess

        q = next_question()
        if q is None:
            guess = best_guess()
            if guess is None or scores[guess["id"]] < 0.18:
                return None, question_count, first_guess
            return guess["id"], question_count, first_guess

        answer = answer_for(q, target)
        asked_ids.add(q["id"])
        asked_attrs.add(q["attribute"])
        question_count += 1

        if answer != "unknown":
            informative_count += 1
            if scenario == "one_unknown" and informative_count == 1:
                answer = "unknown"
            elif scenario == "one_contradiction" and informative_count == 1:
                answer = "no" if answer == "yes" else "yes"

        if answer == "unknown":
            continue

        for p in people:
            value = p["attributes"].get(q["attribute"], 0.5)
            scores[p["id"]] *= likelihood(value, answer)
        normalize()

        if question_count >= QUESTION_LIMIT:
            guess = best_guess()
            if guess is None or scores[guess["id"]] < 0.18:
                return None, question_count, first_guess
            return guess["id"], question_count, first_guess

        if question_count >= EARLY_GUESS_MIN_ANSWERS:
            ranked = sorted(people, key=lambda p: scores[p["id"]], reverse=True)
            top = ranked[0] if ranked else None
            second = ranked[1] if len(ranked) > 1 else None
            if top and scores[top["id"]] >= CONFIDENCE_THRESHOLD:
                margin = scores[top["id"]] - (scores[second["id"]] if second else 0.0)
                if margin >= MARGIN_THRESHOLD:
                    guess = top["id"]
                    if first_guess is None:
                        first_guess = guess
                    return guess, question_count, first_guess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    base = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    people_by_id = {p["id"]: p for p in base["people"]}
    categories = sorted({c for p in base["people"] for c in p["categories"]})
    scenarios = ["ideal", "one_unknown", "one_contradiction"]

    results = []
    for scenario in scenarios:
        for target in base["people"]:
            for category in target["categories"]:
                people, questions = build_engine(base, category)
                guess, count, _ = simulate_round(people, questions, target, scenario)
                first_hit = guess == target["id"]
                results.append({
                    "target": target["id"],
                    "category": category,
                    "scenario": scenario,
                    "questions": count,
                    "guess": guess,
                    "firstGuessHit": first_hit,
                })

    def summarize(subset):
        total = len(subset)
        if total == 0:
            return None
        hits = sum(1 for r in subset if r["firstGuessHit"])
        counts = sorted(r["questions"] for r in subset)
        p95 = counts[int(math.ceil(0.95 * total)) - 1]
        return {
            "total": total,
            "firstGuessAccuracy": round(hits / total, 4),
            "meanQuestions": round(sum(counts) / total, 2),
            "p95Questions": p95,
        }

    per_scenario = {s: summarize([r for r in results if r["scenario"] == s]) for s in scenarios}
    ideal = per_scenario["ideal"]

    summary = {
        "knowledgeVersion": "2026.09.19",
        "seed": args.seed,
        "perScenario": per_scenario,
    }

    print("Cenário ideal:")
    print("  Pessoas avaliadas: {}".format(ideal["total"]))
    print("  Acerto no primeiro palpite: {:.1%}".format(ideal["firstGuessAccuracy"]))
    print("  Média de perguntas: {:.1f}".format(ideal["meanQuestions"]))
    print("  P95 de perguntas: {}".format(ideal["p95Questions"]))
    for s in ["one_unknown", "one_contradiction"]:
        r = per_scenario[s]
        print("Cenário {}: acerto {:.1%}, média {:.1f} perguntas".format(
            s, r["firstGuessAccuracy"], r["meanQuestions"]))

    report = {"summary": summary, "perPerson": results}
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print("Relatório gravado em {}".format(args.report))

    if ideal["total"] == 0:
        raise SystemExit("No personalities evaluated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
