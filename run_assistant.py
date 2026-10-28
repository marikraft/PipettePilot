"""
Interactive demo: type an instruction, review the validated plan, approve it, watch it run.
Every step is written to an audit trail in logs/.
"""
import asyncio
import json
from dataclasses import asdict

from lab_agent import rules
from lab_agent.audit import AuditLog
from lab_agent.deck import build_lab, snapshot
from lab_agent.executor import execute
from lab_agent.planner import MODEL, plan_instruction
from lab_agent.validator import validate

START = {"source": {"A1": 300, "A2": 300, "A3": 300}}


async def main():
    lab = await build_lab(initial_volumes=START)
    log = AuditLog()
    log.record("session_start", model=MODEL, deck=snapshot(lab),
               rules={"dead_volume_fraction": rules.DEAD_VOLUME_FRACTION,
                      "working_max_fill_ul": rules.WORKING_MAX_FILL_UL,
                      "tip_min_fraction": rules.TIP_MIN_FRACTION})
    print("Deck:\n", json.dumps(snapshot(lab), indent=2))
    print(f"Audit trail: {log.path}")

    while True:
        instruction = input("\nInstruction (or 'quit'): ").strip()
        if instruction.lower() in {"quit", "exit", ""}:
            break

        state = snapshot(lab)
        log.record("instruction", text=instruction)
        result = plan_instruction(instruction, state)
        log.record("llm_response", model=result.model, usage=result.usage, calls=result.raw_calls)

        if result.free_text:
            print("No tool call, model replied in text:", result.free_text)
            continue
        if result.refusal:
            print("Refused:", result.refusal)
            continue
        if result.question:
            print("Question:", result.question)
            continue

        print("\nProposed plan:")
        for i, step in enumerate(result.plan, 1):
            print(f"  {i}. {step.describe()}")

        report = validate(result.plan, state)
        log.record("validation", plan=[asdict(s) for s in result.plan],
                   errors=[asdict(e) for e in report.errors],
                   warnings=[asdict(w) for w in report.warnings])
        for issue in report.errors:
            print(f"  ERROR (step {issue.step}): {issue.message}")
        for issue in report.warnings:
            print(f"  WARNING (step {issue.step}): {issue.message}")

        if not report.ok:
            print("Blocked by validation. Nothing was run.")
            continue

        if report.warnings:
            answer = input("Run despite the warnings? Type 'yes' to confirm: ").strip().lower()
            approved = answer == "yes"
        else:
            approved = input("Run this plan? [y/N] ").strip().lower() == "y"
        log.record("approval", approved=approved, warnings_acknowledged=bool(report.warnings) and approved)

        if not approved:
            print("Not run.")
            continue

        await execute(lab, result.plan)
        log.record("execution", steps=len(result.plan), deck_after=snapshot(lab))
        print("Done. Deck now:\n", json.dumps(snapshot(lab), indent=2))

    log.record("session_end")
    await lab.lh.stop()


if __name__ == "__main__":
    asyncio.run(main())
