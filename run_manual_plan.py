"""
Build a plan by hand (no LLM yet), print it, run it, and show the deck before and after.
"""
import asyncio
import json

from lab_agent.actions import transfer, distribute
from lab_agent.deck import build_lab, snapshot
from lab_agent.executor import execute


async def main():
    lab = await build_lab(initial_volumes={"source": {"A1": 300, "A2": 300}})
    print("Deck before:\n", json.dumps(snapshot(lab), indent=2))

    plan = (
        distribute(50, "source", "A1", "target", ["B1", "B2", "B3"])
        + transfer(100, "source", "A2", "target", "C1")
    )
    print("\nPlan:")
    for i, step in enumerate(plan, 1):
        print(f"  {i}. {step.describe()}")

    await execute(lab, plan)

    print("\nDeck after:\n", json.dumps(snapshot(lab), indent=2))
    await lab.lh.stop()


if __name__ == "__main__":
    asyncio.run(main())
