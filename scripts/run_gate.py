#!/usr/bin/env python3
"""Game gate: simulate seeds 42, 43 and 44 in parallel for a candidate expansion and compare with the published baseline.

The criteria follow docs/content/ROADMAP-1000.md ("Portão de jogo"). Values are means over the three seeds,
as in docs/content/BENCHMARK-1.2.6-45.md. The simulation itself is evaluate_gameplay.py, unchanged.

Exit codes: 0 gate passed, 1 gate failed, 2 the run or the comparison could not be done.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPTS = Path(__file__).parent
ROOT = SCRIPTS.parent
EVALUATE = SCRIPTS / "evaluate_gameplay.py"
EXPANSION_PATH = ROOT / "iosApp/Resources/KnowledgeBase/character-expansion.json"
# Published 1.2.6 (44) reports. They live in the agent scratchpad; copy them somewhere durable and pass --baseline-dir.
DEFAULT_BASELINE_DIR = Path(
    "/tmp/claude-1000/-home-richard-Documentos-play-store-quem-sou-eu--/76317c4b-dda5-45e6-97a4-d99e463f35e0/scratchpad/baseline"
)
SEEDS = (42, 43, 44)

IDEAL = "ideal"
LOSS_SCENARIO = "random_10pct"
MAX_FINAL_ACCURACY_DROP = 0.01  # not more than 1 percentage point
MAX_QUESTIONS_INCREASE = 0.5
MIN_FIRST_GUESS_ACCURACY = 0.98


def run_seeds(expansion: Path, out_dir: Path) -> dict[int, Path]:
    """Start one evaluate_gameplay.py process per seed and wait for all of them."""
    processes = []
    for seed in SEEDS:
        report = out_dir / f"seed-{seed}.json"
        log = open(out_dir / f"seed-{seed}.log", "w", encoding="utf-8")
        command = [sys.executable, str(EVALUATE), "--seed", str(seed), "--expansion", str(expansion), "--report", str(report)]
        processes.append((seed, report, log, subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)))
    failed = []
    reports = {}
    for seed, report, log, process in processes:
        code = process.wait()
        log.close()
        if code != 0:
            failed.append(f"seed {seed} exited with {code} (see {out_dir / f'seed-{seed}.log'})")
        reports[seed] = report
    if failed:
        raise RuntimeError("; ".join(failed))
    return reports


def load_reports(paths: dict[int, Path]) -> dict[int, dict]:
    return {seed: json.loads(path.read_text(encoding="utf-8")) for seed, path in paths.items()}


def mean_of(reports: dict[int, dict], scenario: str, key: str) -> float:
    values = [reports[seed]["summary"][scenario][key] for seed in SEEDS]
    return sum(values) / len(values)


def check_comparable(baseline: dict[int, dict], candidate: dict[int, dict]) -> None:
    for seed in SEEDS:
        base_config = {k: v for k, v in baseline[seed]["config"].items() if k != "seed"}
        cand_config = {k: v for k, v in candidate[seed]["config"].items() if k != "seed"}
        if base_config != cand_config:
            raise RuntimeError(f"simulation settings differ from the baseline for seed {seed}: {base_config} != {cand_config}")
        # The game count (one per person and category) grows with the catalog, so it is not compared.


def evaluate_gate(baseline: dict[int, dict], candidate: dict[int, dict]) -> list[dict]:
    loss_base = mean_of(baseline, LOSS_SCENARIO, "eventualAccuracy")
    loss_cand = mean_of(candidate, LOSS_SCENARIO, "eventualAccuracy")
    questions_base = mean_of(baseline, IDEAL, "meanQuestions")
    questions_cand = mean_of(candidate, IDEAL, "meanQuestions")
    first_cand = mean_of(candidate, IDEAL, "firstGuessAccuracy")
    first_base = mean_of(baseline, IDEAL, "firstGuessAccuracy")
    loss_delta = loss_cand - loss_base
    questions_delta = questions_cand - questions_base
    return [
        {
            "criterion": "acerto final com 10% de erros",
            "unit": "percent",
            "limit": "não cair mais de 1 ponto",
            "baseline": loss_base,
            "candidate": loss_cand,
            "delta": loss_delta,
            "passed": loss_delta >= -MAX_FINAL_ACCURACY_DROP - 1e-9,
        },
        {
            "criterion": "perguntas médias no cenário ideal",
            "unit": "questions",
            "limit": "não subir mais de 0,5",
            "baseline": questions_base,
            "candidate": questions_cand,
            "delta": questions_delta,
            "passed": questions_delta <= MAX_QUESTIONS_INCREASE + 1e-9,
        },
        {
            "criterion": "primeiro palpite no cenário ideal",
            "unit": "percent",
            "limit": "pelo menos 98%",
            "baseline": first_base,
            "candidate": first_cand,
            "delta": first_cand - first_base,
            "passed": first_cand >= MIN_FIRST_GUESS_ACCURACY - 1e-9,
        },
    ]


def scenario_table(baseline: dict[int, dict], candidate: dict[int, dict]) -> list[dict]:
    rows = []
    for scenario in baseline[SEEDS[0]]["summary"]:
        rows.append({
            "scenario": scenario,
            "firstGuess": (mean_of(baseline, scenario, "firstGuessAccuracy"), mean_of(candidate, scenario, "firstGuessAccuracy")),
            "eventual": (mean_of(baseline, scenario, "eventualAccuracy"), mean_of(candidate, scenario, "eventualAccuracy")),
            "meanQuestions": (mean_of(baseline, scenario, "meanQuestions"), mean_of(candidate, scenario, "meanQuestions")),
        })
    return rows


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def print_report(expansion: Path, baseline_dir: Path, verdicts: list[dict], rows: list[dict], baseline: dict[int, dict], candidate: dict[int, dict]) -> None:
    print(f"Portão de jogo: candidato {expansion}")
    print(f"Base publicada: {baseline_dir}")
    print(f"Sementes {', '.join(map(str, SEEDS))}; valores são médias das três sementes")
    print()
    print("Critérios do portão")
    for verdict in verdicts:
        if verdict["unit"] == "percent":
            fmt = format_percent
            delta = f"{verdict['delta'] * 100:+.2f} pp"
        else:
            fmt = lambda value: f"{value:.2f}"
            delta = f"{verdict['delta']:+.2f}"
        status = "PASSA" if verdict["passed"] else "REPROVA"
        print(f"- {verdict['criterion']}: base {fmt(verdict['baseline'])}, candidato {fmt(verdict['candidate'])}, Δ {delta}; limite {verdict['limit']}; {status}")
    print("- personagens indistinguíveis: não medido aqui; use scripts/check_wave.py e scripts/validate_content.py")
    print()
    print("Cenários (informativos, não bloqueiam)")
    print(f"{'cenário':20s} {'1º palpite base':>16s} {'1º palpite cand':>16s} {'acerto final base':>18s} {'acerto final cand':>18s} {'perguntas base':>15s} {'perguntas cand':>15s}")
    for row in rows:
        print(
            f"{row['scenario']:20s} {format_percent(row['firstGuess'][0]):>16s} {format_percent(row['firstGuess'][1]):>16s}"
            f" {format_percent(row['eventual'][0]):>18s} {format_percent(row['eventual'][1]):>18s}"
            f" {row['meanQuestions'][0]:15.2f} {row['meanQuestions'][1]:15.2f}"
        )
    print()
    print("Por semente (candidato): " + "; ".join(
        f"{seed}: 1º palpite ideal {format_percent(candidate[seed]['summary'][IDEAL]['firstGuessAccuracy'])}, "
        f"acerto final com 10% de erros {format_percent(candidate[seed]['summary'][LOSS_SCENARIO]['eventualAccuracy'])}"
        for seed in SEEDS
    ))
    print()
    print("VEREDITO: " + ("portão aprovado" if all(v["passed"] for v in verdicts) else "portão reprovado"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--expansion", type=Path, default=EXPANSION_PATH, help="candidate expansion file (default: the app's)")
    parser.add_argument("--baseline-dir", type=Path, default=DEFAULT_BASELINE_DIR, help="folder with seed-42.json, seed-43.json, seed-44.json of the published build")
    parser.add_argument("--out-dir", type=Path, help="where the candidate reports and logs go (default: a new temporary folder)")
    parser.add_argument("--reuse", type=Path, help="compare existing seed-N.json reports in this folder instead of simulating")
    parser.add_argument("--report", type=Path, help="write the comparison as JSON here")
    args = parser.parse_args()

    expansion = args.expansion.resolve()
    if not expansion.is_file():
        parser.error(f"--expansion file not found: {expansion}")
    baseline_paths = {seed: args.baseline_dir / f"seed-{seed}.json" for seed in SEEDS}
    missing = [str(path) for path in baseline_paths.values() if not path.is_file()]
    if missing:
        parser.error(f"baseline reports missing: {missing}")

    try:
        if args.reuse:
            candidate_paths = {seed: args.reuse / f"seed-{seed}.json" for seed in SEEDS}
            out_dir = args.reuse
        else:
            out_dir = args.out_dir or Path(tempfile.mkdtemp(prefix="run-gate-"))
            out_dir.mkdir(parents=True, exist_ok=True)
            print(f"Simulando sementes {', '.join(map(str, SEEDS))} em paralelo; relatórios em {out_dir}", flush=True)
            candidate_paths = run_seeds(expansion, out_dir)
        baseline = load_reports(baseline_paths)
        candidate = load_reports(candidate_paths)
        check_comparable(baseline, candidate)
    except (RuntimeError, OSError, KeyError, json.JSONDecodeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2

    verdicts = evaluate_gate(baseline, candidate)
    rows = scenario_table(baseline, candidate)
    print_report(expansion, args.baseline_dir, verdicts, rows, baseline, candidate)
    if args.report:
        args.report.write_text(json.dumps({
            "expansion": str(expansion),
            "reports": str(out_dir),
            "seeds": list(SEEDS),
            "criteria": verdicts,
            "scenarios": rows,
            "passed": all(v["passed"] for v in verdicts),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Comparação gravada em {args.report}")
    return 0 if all(v["passed"] for v in verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
