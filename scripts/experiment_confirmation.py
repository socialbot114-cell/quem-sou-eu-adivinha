#!/usr/bin/env python3
"""Experiment: Akinator-style confirmation before a guess.

The official simulator (evaluate_gameplay.py) guesses as soon as the leader has 68% confidence.
This experiment only changes that rule: the game keeps the leader unguessed until it reaches
`--guess` confidence, then asks up to `--verify` questions chosen to separate the leader from the
runner-up (questions where their answers differ the most), and only then offers the guess. A
rejected guess resumes the normal flow, as in the app.

The baseline (`--verify 0 --guess 0.68`) calls the official simulate_game, so both runs use the same
episodes (same targets, categories, scenarios and seeds). Nothing here changes the app.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evaluate_gameplay as sim  # noqa: E402

SCENARIOS = ("ideal", "one_unknown", "one_contradiction", "two_contradictions", "random_10pct", "probably_answers", "unknown_50")


def runner_up(engine, leader):
    ranked = sorted(
        (person for person in engine.people if engine.scores[person["id"]] > 0 and person["id"] != leader["id"]),
        key=lambda person: engine.scores[person["id"]],
        reverse=True,
    )
    return ranked[0] if ranked else None


def separating_question(engine, leader, rival):
    """Unasked question whose answers differ most between the leader and the runner-up (gap >= 0.5)."""
    best, best_gap = None, 0.5
    for question in engine.questions:
        if question["id"] in engine.asked_ids or question["attribute"] in engine.asked_attributes:
            continue
        a = leader["attributes"].get(question["attribute"])
        b = rival["attributes"].get(question["attribute"])
        if a is None or b is None:
            continue
        gap = abs(a - b)
        if gap >= best_gap:
            best, best_gap = question, gap
    return best


def limit(available: int, rejected: int, unknown: int, confidence: float, max_limit: int) -> int:
    """Question budget as in GuessPolicy, with the cap as a parameter (the app uses 20)."""
    if confidence < sim.EXTENSION_CONFIDENCE:
        return max(0, min(max_limit, available))
    extended = sim.QUESTION_LIMIT + sim.EXTRA_QUESTIONS_PER_REJECTED_GUESS * max(rejected, 0) + min(max(unknown, 0), sim.FREE_UNKNOWN_ANSWERS)
    return max(0, min(max_limit, extended, available))


def play_confirmed(target, people, questions, scenario, seed, *, floor, guess_confidence, verify, max_questions,
                   margin_threshold, max_rejected=4, max_limit=20):
    tie_rng = random.Random(seed)
    noise_rng = random.Random(seed ^ 0x5DEECE66D)
    engine = sim.SimulatedEngine(people, questions, floor, tie_rng.choice)
    available = len({question["attribute"] for question in questions})
    question_limit = limit(available, 0, 0, engine.confidence, max_limit)
    question_count = informative = unknown = 0
    guesses: list[str] = []
    verified: dict[str, int] = {}

    def ask(question: dict) -> None:
        nonlocal question_count, informative, unknown
        answer = sim.answer_from_attribute(target["attributes"].get(question["attribute"]))
        if answer != "unknown":
            informative += 1
        answer = sim.apply_noise(answer, scenario, informative, noise_rng)
        engine.apply(question["attribute"], answer)
        question_count += 1
        if answer == "unknown":
            unknown += 1

    while True:
        leader = engine.best_guess
        if (
            verify > 0
            and leader is not None
            and question_count >= sim.EARLY_GUESS_MIN_ANSWERS
            and engine.confidence >= guess_confidence
            and engine.margin >= margin_threshold
            and verified.get(leader["id"], 0) < verify
            and question_count < max_questions
        ):
            rival = runner_up(engine, leader)
            check = separating_question(engine, leader, rival) if rival is not None else None
            if check is not None:
                verified[leader["id"]] = verified.get(leader["id"], 0) + 1
                engine.asked_ids.add(check["id"])
                engine.asked_attributes.add(check["attribute"])
                ask(check)
                question_limit = limit(available, len(engine.rejected), unknown, engine.confidence, max_limit)
                continue

        question = engine.next_question() if question_count < question_limit else None
        if question is not None:
            ask(question)
            question_limit = limit(available, len(engine.rejected), unknown, engine.confidence, max_limit)
        should_guess = (
            question is None
            or question_count >= question_limit
            or (
                question_count >= sim.EARLY_GUESS_MIN_ANSWERS
                and engine.confidence >= guess_confidence
                and engine.margin >= margin_threshold
            )
        )
        if not should_guess:
            continue
        guess = engine.best_guess
        if guess is None:
            return sim.game_result(target["id"], guesses, question_count, success=False, stopped_without_guess=True)
        guesses.append(guess["id"])
        if guess["id"] == target["id"]:
            return sim.game_result(target["id"], guesses, question_count, success=True)
        engine.reject(guess["id"])
        question_limit = limit(available, len(engine.rejected), unknown, engine.confidence, max_limit)
        if len(engine.rejected) >= max_rejected or engine.best_guess is None:
            return sim.game_result(target["id"], guesses, question_count, success=False)


def play_episode(target, people, questions, scenario, seed, args):
    return play_confirmed(target, people, questions, scenario, seed, floor=args.floor, guess_confidence=args.guess,
                          verify=args.verify, max_questions=args.max_questions, margin_threshold=args.margin,
                          max_rejected=args.max_rejected, max_limit=args.max_limit)


def run(args) -> dict:
    base = sim.load_catalog(Path(args.expansion))
    results: dict[str, list[dict]] = {scenario: [] for scenario in args.scenarios}
    episode = 0
    for scenario in args.scenarios:
        for target in base["people"]:
            for category in target["categories"]:
                people = base["people"] if category == "Todos" else [p for p in base["people"] if category in p["categories"]]
                questions = [q for q in base["questions"]
                             if category == "Todos" or "Todos" in q["categories"] or category in q["categories"]]
                result = play_episode(target, people, questions, scenario, args.seed + episode, args)
                results[scenario].append(result)
                episode += 1
    return {scenario: sim.summarize(items) for scenario, items in results.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--verify", type=int, default=0, help="verification questions before a guess (0 = official rule)")
    parser.add_argument("--guess", type=float, default=0.68, help="confidence needed before verification or guess")
    parser.add_argument("--max-questions", type=int, default=25, help="cap for verification questions")
    parser.add_argument("--max-rejected", type=int, default=4, help="wrong guesses before the game gives up (app: 4)")
    parser.add_argument("--max-limit", type=int, default=20, help="cap of the normal question budget (app: 20)")
    parser.add_argument("--margin", type=float, default=0.10)
    parser.add_argument("--floor", type=float, default=0.18)
    parser.add_argument("--expansion", default=str(sim.EXPANSION_PATH))
    parser.add_argument("--scenarios", default=",".join(SCENARIOS))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    args.scenarios = tuple(args.scenarios.split(","))
    summary = run(args)
    Path(args.out).write_text(json.dumps({"config": vars(args), "summary": summary}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for scenario, metrics in summary.items():
        print(scenario, metrics["firstGuessAccuracy"], metrics["eventualAccuracy"], metrics["meanQuestions"], metrics["unsolvedGames"])


if __name__ == "__main__":
    main()
