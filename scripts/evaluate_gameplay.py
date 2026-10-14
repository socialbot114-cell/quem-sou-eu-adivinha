#!/usr/bin/env python3
"""Simulate complete offline game sessions, including rejected guesses."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).parents[1]
CONTENT_PATH = ROOT / "iosApp/Resources/KnowledgeBase/knowledge.json"
EXPANSION_PATH = ROOT / "iosApp/Resources/KnowledgeBase/character-expansion.json"

ANSWER_EVIDENCE = {
    "yes": 1.0,
    "probablyYes": 0.75,
    "probablyNo": 0.25,
    "no": 0.0,
}
ANSWER_ORDER = tuple(ANSWER_EVIDENCE)
QUESTION_LIMIT = 14
EARLY_GUESS_MIN_ANSWERS = 4
MAX_REJECTED_GUESSES = 4
MIN_GUESS_CONFIDENCE = 0.18
DEFAULT_EARLY_GUESS_CONFIDENCE = 0.68
DEFAULT_MARGIN_THRESHOLD = 0.10
DEFAULT_LIKELIHOOD_FLOOR = 0.18
EXTRA_QUESTIONS_PER_REJECTED_GUESS = 3
MAXIMUM_QUESTION_LIMIT = 20
FREE_UNKNOWN_ANSWERS = 2


def question_budget(available_attributes: int, rejected_guesses: int, unknown_answers: int, policy: str) -> int:
    """Mirror of GuessPolicy.questionBudget in GameEngine.swift."""
    if policy == "legacy":
        return min(QUESTION_LIMIT, available_attributes)
    extended = QUESTION_LIMIT + EXTRA_QUESTIONS_PER_REJECTED_GUESS * rejected_guesses
    extended += min(unknown_answers, FREE_UNKNOWN_ANSWERS)
    return min(MAXIMUM_QUESTION_LIMIT, extended, available_attributes)


def entropy(values: list[float]) -> float:
    return -sum(value * math.log2(value) for value in values if value > 0)


def likelihood(value: float, answer: str, floor: float) -> float:
    evidence = ANSWER_EVIDENCE[answer]
    weights = [max(floor, 1.0 - abs(value - ANSWER_EVIDENCE[key])) for key in ANSWER_ORDER]
    total = sum(weights)
    raw = max(floor, 1.0 - abs(value - evidence))
    return raw / total if total > 0 else 1.0


class SimulatedEngine:
    """Python mirror of the score and question policy in GameEngine.swift."""

    def __init__(self, people: list[dict], questions: list[dict], floor: float, choose_candidate):
        self.people = people
        self.questions = questions
        self.floor = floor
        self.choose_candidate = choose_candidate
        self.scores = {person["id"]: 1.0 / max(len(people), 1) for person in people}
        self.asked_ids: set[str] = set()
        self.asked_attributes: set[str] = set()
        self.rejected: set[str] = set()

    def normalize(self) -> None:
        for person_id in self.rejected:
            self.scores[person_id] = 0.0
        active = [person_id for person_id in self.scores if person_id not in self.rejected]
        total = sum(self.scores.values())
        if total <= 0:
            if active:
                share = 1.0 / len(active)
                for person_id in self.scores:
                    self.scores[person_id] = 0.0 if person_id in self.rejected else share
            return
        for person_id in active:
            self.scores[person_id] += 1e-9
        smoothed_total = sum(self.scores.values())
        for person_id, value in self.scores.items():
            self.scores[person_id] = value / smoothed_total if math.isfinite(value) and value >= 0 else 0.0

    def apply(self, attribute: str, answer: str) -> None:
        if answer == "unknown":
            return
        for person in self.people:
            value = person["attributes"].get(attribute, 0.5)
            self.scores[person["id"]] *= likelihood(value, answer, self.floor)
        self.normalize()

    def reject(self, person_id: str) -> None:
        self.rejected.add(person_id)
        self.scores[person_id] = 0.0
        self.normalize()

    @property
    def best_guess(self) -> dict | None:
        active = [person for person in self.people if self.scores[person["id"]] > 0]
        return max(active, key=lambda person: self.scores[person["id"]], default=None)

    @property
    def confidence(self) -> float:
        guess = self.best_guess
        return self.scores[guess["id"]] if guess else 0.0

    @property
    def margin(self) -> float:
        ranked = sorted(
            (person for person in self.people if self.scores[person["id"]] > 0),
            key=lambda person: self.scores[person["id"]],
            reverse=True,
        )
        if not ranked:
            return 0.0
        first = self.scores[ranked[0]["id"]]
        second = self.scores[ranked[1]["id"]] if len(ranked) > 1 else 0.0
        return first - second

    def information_gain(self, question: dict) -> float:
        attribute = question["attribute"]
        coverage = sum(
            self.scores[person["id"]]
            for person in self.people
            if attribute in person["attributes"]
        )
        if coverage < 0.6:
            return 0.0

        prior_entropy = entropy(list(self.scores.values()))
        expected_entropy = 0.0
        for answer in ANSWER_ORDER:
            weighted = {
                person["id"]: self.scores[person["id"]]
                * likelihood(person["attributes"].get(attribute, 0.5), answer, self.floor)
                for person in self.people
            }
            probability = sum(weighted.values())
            if probability > 0:
                expected_entropy += probability * entropy([value / probability for value in weighted.values()])
        return max(0.0, prior_entropy - expected_entropy) * coverage

    def next_question(self) -> dict | None:
        scored = [
            (question, self.information_gain(question))
            for question in self.questions
            if question["id"] not in self.asked_ids
            and question["attribute"] not in self.asked_attributes
        ]
        scored = [(question, gain) for question, gain in scored if gain > 0.001]
        if not scored:
            return None
        best_gain = max(gain for _, gain in scored)
        tied = [question for question, gain in scored if gain >= best_gain - 0.01]
        selected = self.choose_candidate(tied)
        self.asked_ids.add(selected["id"])
        self.asked_attributes.add(selected["attribute"])
        return selected


def answer_from_attribute(value: float | None) -> str:
    if value is None or 0.375 <= value <= 0.625:
        return "unknown"
    return min(ANSWER_ORDER, key=lambda answer: abs(value - ANSWER_EVIDENCE[answer]))


def invert_answer(answer: str) -> str:
    return {
        "yes": "no",
        "probablyYes": "probablyNo",
        "probablyNo": "probablyYes",
        "no": "yes",
    }[answer]


def apply_noise(answer: str, scenario: str, informative_index: int, rng: random.Random) -> str:
    if answer == "unknown":
        return answer
    if scenario == "one_unknown" and informative_index == 1:
        return "unknown"
    if scenario == "one_contradiction" and informative_index == 1:
        return invert_answer(answer)
    if scenario == "two_contradictions" and informative_index <= 2:
        return invert_answer(answer)
    if scenario == "random_10pct" and rng.random() < 0.10:
        return invert_answer(answer)
    if scenario == "probably_answers":
        return "probablyYes" if answer in {"yes", "probablyYes"} else "probablyNo"
    return answer


def simulate_game(
    target: dict,
    people: list[dict],
    questions: list[dict],
    scenario: str,
    seed: int,
    *,
    floor: float,
    guess_confidence: float,
    margin_threshold: float,
    tie_mode: str = "seeded",
    policy: str = "adaptive",
) -> dict:
    tie_rng = random.Random(seed)
    noise_rng = random.Random(seed ^ 0x5DEECE66D)
    choose_candidate = tie_rng.choice if tie_mode == "seeded" else lambda candidates: candidates[0]
    engine = SimulatedEngine(people, questions, floor, choose_candidate)
    available_attributes = len({question["attribute"] for question in questions})
    question_limit = question_budget(available_attributes, 0, 0, policy)
    question_count = 0
    informative_count = 0
    unknown_count = 0
    guesses: list[str] = []

    while True:
        question = engine.next_question() if question_count < question_limit else None
        if question is not None:
            value = target["attributes"].get(question["attribute"])
            answer = answer_from_attribute(value)
            if answer != "unknown":
                informative_count += 1
            answer = apply_noise(answer, scenario, informative_count, noise_rng)
            engine.apply(question["attribute"], answer)
            question_count += 1
            if answer == "unknown":
                unknown_count += 1
            question_limit = question_budget(available_attributes, len(engine.rejected), unknown_count, policy)

        should_guess = (
            question is None
            or question_count >= question_limit
            or (
                question_count >= EARLY_GUESS_MIN_ANSWERS
                and engine.confidence >= guess_confidence
                and engine.margin >= margin_threshold
            )
        )
        if not should_guess:
            continue

        guess = engine.best_guess
        if guess is None or engine.confidence < MIN_GUESS_CONFIDENCE:
            return game_result(target["id"], guesses, question_count, success=False, stopped_without_guess=True)

        guesses.append(guess["id"])
        if guess["id"] == target["id"]:
            return game_result(target["id"], guesses, question_count, success=True)

        engine.reject(guess["id"])
        question_limit = question_budget(available_attributes, len(engine.rejected), unknown_count, policy)
        if len(engine.rejected) >= MAX_REJECTED_GUESSES or question_count >= question_limit or engine.best_guess is None:
            return game_result(target["id"], guesses, question_count, success=False)


def game_result(target_id: str, guesses: list[str], question_count: int, *, success: bool, stopped_without_guess: bool = False) -> dict:
    return {
        "target": target_id,
        "firstGuessHit": bool(guesses and guesses[0] == target_id),
        "eventualHit": success,
        "questions": question_count,
        "guesses": len(guesses),
        "rejectedGuesses": max(0, len(guesses) - (1 if success else 0)),
        "stoppedWithoutGuess": stopped_without_guess,
    }


def summarize(results: list[dict]) -> dict:
    if not results:
        return {}
    question_counts = sorted(result["questions"] for result in results)
    successes = [result for result in results if result["eventualHit"]]
    return {
        "games": len(results),
        "firstGuessAccuracy": round(mean(result["firstGuessHit"] for result in results), 4),
        "eventualAccuracy": round(mean(result["eventualHit"] for result in results), 4),
        "eventualAccuracyWithin10Questions": round(
            sum(result["eventualHit"] and result["questions"] <= 10 for result in results) / len(results), 4
        ),
        "eventualAccuracyWithin14Questions": round(
            sum(result["eventualHit"] and result["questions"] <= 14 for result in results) / len(results), 4
        ),
        "eventualAccuracyWithin20Questions": round(
            sum(result["eventualHit"] and result["questions"] <= 20 for result in results) / len(results), 4
        ),
        "meanQuestions": round(mean(question_counts), 2),
        "p95Questions": question_counts[math.ceil(0.95 * len(question_counts)) - 1],
        "meanGuesses": round(mean(result["guesses"] for result in results), 2),
        "meanRejectedGuesses": round(mean(result["rejectedGuesses"] for result in results), 2),
        "unsolvedGames": sum(not result["eventualHit"] for result in results),
        "stoppedWithoutGuess": sum(result["stoppedWithoutGuess"] for result in results),
    }


def load_catalog() -> dict:
    base = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    if EXPANSION_PATH.is_file():
        expansion = json.loads(EXPANSION_PATH.read_text(encoding="utf-8"))
        base["people"].extend(expansion["people"])
        base["questions"].extend(expansion["questions"])
    return base


def run(seed: int, floor: float, guess_confidence: float, margin_threshold: float, tie_mode: str, policy: str = "adaptive") -> dict:
    base = load_catalog()
    scenarios = ("ideal", "one_unknown", "one_contradiction", "two_contradictions", "random_10pct", "probably_answers")
    results: list[dict] = []
    by_scenario: dict[str, dict] = {}
    by_category: dict[str, dict] = {}
    episode = 0

    for scenario in scenarios:
        scenario_results = []
        category_results: dict[str, list[dict]] = {}
        for target in base["people"]:
            for category in target["categories"]:
                people = base["people"] if category == "Todos" else [
                    person for person in base["people"] if category in person["categories"]
                ]
                questions = [
                    question for question in base["questions"]
                    if category == "Todos"
                    or "Todos" in question["categories"]
                    or category in question["categories"]
                ]
                result = simulate_game(
                    target,
                    people,
                    questions,
                    scenario,
                    seed + episode,
                    floor=floor,
                    guess_confidence=guess_confidence,
                    margin_threshold=margin_threshold,
                    tie_mode=tie_mode,
                    policy=policy,
                )
                result.update({"category": category, "scenario": scenario})
                scenario_results.append(result)
                category_results.setdefault(category, []).append(result)
                episode += 1
        results.extend(scenario_results)
        by_scenario[scenario] = summarize(scenario_results)
        by_category[scenario] = {category: summarize(items) for category, items in sorted(category_results.items())}

    return {
        "config": {
            "seed": seed,
            "likelihoodFloor": floor,
            "earlyGuessConfidence": guess_confidence,
            "marginThreshold": margin_threshold,
            "tieMode": tie_mode,
            "budgetPolicy": policy,
            "questionLimit": QUESTION_LIMIT,
            "extraQuestionsPerRejectedGuess": EXTRA_QUESTIONS_PER_REJECTED_GUESS if policy == "adaptive" else 0,
            "freeUnknownAnswers": FREE_UNKNOWN_ANSWERS if policy == "adaptive" else 0,
            "maximumQuestionLimit": MAXIMUM_QUESTION_LIMIT if policy == "adaptive" else QUESTION_LIMIT,
            "maxRejectedGuesses": MAX_REJECTED_GUESSES,
        },
        "summary": by_scenario,
        "byCategory": by_category,
        "games": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--likelihood-floor", type=float, default=DEFAULT_LIKELIHOOD_FLOOR)
    parser.add_argument("--guess-confidence", type=float, default=DEFAULT_EARLY_GUESS_CONFIDENCE)
    parser.add_argument("--margin-threshold", type=float, default=DEFAULT_MARGIN_THRESHOLD)
    parser.add_argument("--tie-mode", choices=("seeded", "first"), default="seeded")
    parser.add_argument(
        "--budget-policy",
        choices=("adaptive", "legacy"),
        default="adaptive",
        help="adaptive: +3 questions per rejected guess and up to 2 free 'Não sei' answers (max 20); legacy: fixed 14",
    )
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not 0.0 < args.likelihood_floor < 1.0:
        parser.error("--likelihood-floor must be between 0 and 1")
    if not 0.0 < args.guess_confidence < 1.0:
        parser.error("--guess-confidence must be between 0 and 1")
    if not 0.0 <= args.margin_threshold < 1.0:
        parser.error("--margin-threshold must be between 0 and 1")

    report = run(args.seed, args.likelihood_floor, args.guess_confidence, args.margin_threshold, args.tie_mode, args.budget_policy)
    print(json.dumps({"config": report["config"], "summary": report["summary"]}, ensure_ascii=False, indent=2))
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Detailed report written to {args.report}")


if __name__ == "__main__":
    main()
