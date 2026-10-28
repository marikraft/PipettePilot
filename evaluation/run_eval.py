"""
Runs every test case several times against one model and scores two pipelines:

  LLM only        the model's answer is taken at face value (a plan would run)
  LLM + validator the plan also has to pass validate() before it could run

Usage:
  python -m evaluation.run_eval --model claude-sonnet-5-5 --repeats 5
  python -m evaluation.run_eval --prompt v2 --category "conflicts with deck"
Writes results/<model>[_<prompt>]_runs.csv (every run) and ..._summary.md.
"""
import argparse
import csv
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anthropic

from lab_agent.planner import MODEL, plan_instruction
from lab_agent.validator import validate
from evaluation.cases import CASES, HELDOUT_CASES, DEFAULT_DECK

RESULTS_DIR = Path("results")


def classify(result, deck):
    """Outcome of the LLM alone, and of the LLM followed by the validator."""
    if result.free_text:
        return "free_text", "free_text"
    if result.refusal:
        return "refused", "refused"
    if result.question:
        return "clarified", "clarified"
    report = validate(result.plan, deck)
    if not report.ok:
        return "passed", "blocked"
    return "passed", ("warned" if report.warnings else "passed")


def plan_matches(plan, expected):
    got = Counter((s.volume_ul, s.source_plate, s.source_well, s.dest_plate, s.dest_well) for s in plan)
    return got == Counter(expected)


def run_once(client, model, prompt, case, repeat):
    deck = case.get("deck", DEFAULT_DECK)
    start = time.perf_counter()
    try:
        result = plan_instruction(case["instruction"], deck, client=client, model=model, prompt_version=prompt)
    except anthropic.APIError as e:
        return {"id": case["id"], "category": case["category"], "repeat": repeat,
                "llm_only": "api_error", "with_validator": "api_error", "error": str(e)[:200]}
    latency = time.perf_counter() - start
    llm_only, with_validator = classify(result, deck)
    row = {
        "id": case["id"], "category": case["category"], "repeat": repeat,
        "llm_only": llm_only, "with_validator": with_validator,
        "llm_only_correct": llm_only in case["acceptable"],
        "with_validator_correct": with_validator in case["acceptable"],
        "plan_steps": len(result.plan),
        "plan_exact": plan_matches(result.plan, case["expected_plan"]) if "expected_plan" in case and result.plan else "",
        "input_tokens": result.usage["input_tokens"], "output_tokens": result.usage["output_tokens"],
        "latency_s": round(latency, 2),
        "plan": "; ".join(s.describe() for s in result.plan),
        "message": result.question or result.refusal or result.free_text or "",
    }
    return row


def pct(n, d):
    return f"{100 * n / d:.0f}%" if d else "-"


def summarise(rows, model, repeats, n_cases):
    ok = [r for r in rows if r["llm_only"] != "api_error"]
    by_cat = defaultdict(list)
    for r in ok:
        by_cat[r["category"]].append(r)

    lines = [f"# Evaluation: {model}", "",
             f"{n_cases} cases x {repeats} repeats = {len(rows)} runs ({len(rows) - len(ok)} API errors).", "",
             "| Category | Runs | Correct, LLM only | Correct, LLM + validator | Would run unflagged, LLM only "
             "| Would run unflagged, with validator |",
             "|---|---|---|---|---|---|"]
    for cat, rs in by_cat.items():
        lines.append(
            f"| {cat} | {len(rs)} | {pct(sum(r['llm_only_correct'] for r in rs), len(rs))} "
            f"| {pct(sum(r['with_validator_correct'] for r in rs), len(rs))} "
            f"| {pct(sum(r['llm_only'] == 'passed' for r in rs), len(rs)) if cat != 'clear' else '-'} "
            f"| {pct(sum(r['with_validator'] == 'passed' for r in rs), len(rs)) if cat != 'clear' else '-'} |")

    total = len(ok)
    lines += ["",
              f"- Overall correct: LLM only {pct(sum(r['llm_only_correct'] for r in ok), total)}, "
              f"with validator {pct(sum(r['with_validator_correct'] for r in ok), total)}"]

    exact = [r for r in ok if r["plan_exact"] != ""]
    lines.append(f"- Clear instructions with the exact expected plan: {pct(sum(r['plan_exact'] for r in exact), len(exact))}")

    by_case = defaultdict(list)
    for r in ok:
        by_case[r["id"]].append(r["with_validator"])
    consistent = sum(len(set(v)) == 1 for v in by_case.values())
    lines.append(f"- Cases with the same outcome on every repeat: {consistent} of {len(by_case)}")
    flaky = {k: dict(Counter(v)) for k, v in by_case.items() if len(set(v)) > 1}
    for k, v in flaky.items():
        lines.append(f"  - {k}: {v}")

    if ok:
        lines.append(f"- Mean tokens per instruction: {sum(r['input_tokens'] for r in ok) / total:.0f} in, "
                     f"{sum(r['output_tokens'] for r in ok) / total:.0f} out")
        lines.append(f"- Mean latency: {sum(r['latency_s'] for r in ok) / total:.1f} s")

    wrong = [r for r in ok if not r["with_validator_correct"]]
    if wrong:
        lines += ["", "## Incorrect runs (LLM + validator)", "", "| Case | Outcome | Plan or message |", "|---|---|---|"]
        for r in wrong:
            detail = (r["plan"] or r["message"]).replace("|", "/")[:160]
            lines.append(f"| {r['id']} | {r['with_validator']} | {detail} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--prompt", default="v1", help="system prompt version (see planner.SYSTEM_PROMPTS)")
    parser.add_argument("--category", help="run only one category")
    parser.add_argument("--heldout", action="store_true", help="run the held-out cases instead of the main set")
    parser.add_argument("--only", help="run a single case id, for debugging")
    args = parser.parse_args()

    case_set = HELDOUT_CASES if args.heldout else CASES
    cases = [c for c in case_set
             if (not args.only or c["id"] == args.only)
             and (not args.category or c["category"] == args.category)]
    client = anthropic.Anthropic(max_retries=5)
    jobs = [(c, r) for c in cases for r in range(1, args.repeats + 1)]
    print(f"Running {len(jobs)} calls against {args.model}, prompt {args.prompt}...")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda job: run_once(client, args.model, args.prompt, *job), jobs))

    RESULTS_DIR.mkdir(exist_ok=True)
    name = args.model if args.prompt == "v1" else f"{args.model}_prompt-{args.prompt}"
    if args.heldout:
        name += "_heldout"
    if args.category or args.only:
        name += "_" + (args.only or args.category.replace(" ", "-"))
    fields = ["id", "category", "repeat", "llm_only", "with_validator", "llm_only_correct",
              "with_validator_correct", "plan_steps", "plan_exact", "input_tokens", "output_tokens",
              "latency_s", "plan", "message", "error"]
    with open(RESULTS_DIR / f"{name}_runs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    summary = summarise(rows, f"{args.model}, prompt {args.prompt}", args.repeats, len(cases))
    (RESULTS_DIR / f"{name}_summary.md").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
