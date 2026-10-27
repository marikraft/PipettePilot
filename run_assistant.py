"""
Interactive demo: type an instruction, review the validated plan, approve it, watch it run.
"""
import asyncio
import json

from lab_agent.deck import build_lab, snapshot
from lab_agent.executor import execute
from lab_agent.planner import plan_instruction
from lab_agent.validator import validate

START = {"source": {"A1": 300, "A2": 300, "A3": 300}}


async def main():
    lab = await build_lab(initial_volumes=START)
    print("Deck:\n", json.dumps(snapshot(lab), indent=2))

    while True:
        instruction = input("\nInstruction (or 'quit'): ").strip()
        if instruction.lower() in {"quit", "exit", ""}:
            break

        state = snapshot(lab)
        result = plan_instruction(instruction, state)

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

        if not approved:
            print("Not run.")
            continue

        await execute(lab, result.plan)
        print("Done. Deck now:\n", json.dumps(snapshot(lab), indent=2))

    await lab.lh.stop()


if __name__ == "__main__":
    asyncio.run(main())
