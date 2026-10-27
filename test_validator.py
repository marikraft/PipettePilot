"""
Checks the validator against hand-written plans, no LLM involved.
Run with:  python -m pytest test_validator.py
"""
from lab_agent.actions import transfer, distribute
from lab_agent.validator import validate

DECK = {
    "plates": {
        "source": {"max_volume_ul": 360, "filled_wells": {"A1": 300, "A2": 300}},
        "target": {"max_volume_ul": 360, "filled_wells": {}},
    },
    "tips_left": {"50uL": 96, "300uL": 96, "1000uL": 96},
}


def test_valid_plan_passes():
    report = validate(distribute(50, "source", "A1", "target", ["B1", "B2", "B3"]), DECK)
    assert report.ok and not report.warnings


def test_source_runs_dry_across_steps():
    report = validate(distribute(80, "source", "A1", "target", ["D1", "D2", "D3", "D4", "D5"]), DECK)
    assert [e.step for e in report.errors] == [4, 5]


def test_destination_overflows_across_steps():
    plan = transfer(200, "source", "A1", "target", "E1") + transfer(200, "source", "A2", "target", "E1")
    assert [e.step for e in validate(plan, DECK).errors] == [2]


def test_nonexistent_well():
    assert not validate(transfer(50, "source", "A1", "target", "I1"), DECK).ok


def test_volume_above_largest_tip():
    assert not validate(transfer(1500, "source", "A1", "target", "B1"), DECK).ok


def test_volume_too_small_for_any_tip():
    assert not validate(transfer(2, "source", "A1", "target", "B1"), DECK).ok


def test_dead_volume_warning():
    report = validate(transfer(280, "source", "A1", "target", "B1"), DECK)
    assert report.ok and len(report.warnings) == 1


def test_working_volume_warning():
    report = validate(transfer(250, "source", "A1", "target", "B1")
                      + transfer(10, "source", "A2", "target", "B1")
                      + transfer(50, "source", "A2", "target", "B1"), DECK)
    assert report.ok and any("working maximum" in w.message for w in report.warnings)


def test_out_of_tips():
    deck = {**DECK, "tips_left": {"50uL": 1, "300uL": 0, "1000uL": 0}}
    report = validate(distribute(20, "source", "A1", "target", ["B1", "B2"]), deck)
    assert [e.step for e in report.errors] == [2]
