"""
Checks a whole plan against the deck before anything moves.

The plan is replayed step by step on a copy of the deck state, so problems that only
appear in combination (two transfers that together overfill a well, a source that runs
dry halfway through) are caught too.

Errors are physical impossibilities and block the plan.
Warnings break lab practice rules (rules.py); the plan can still run after explicit approval.
"""
import copy
import re
from dataclasses import dataclass, field

from .actions import Transfer
from .rules import DEAD_VOLUME_FRACTION, WORKING_MAX_FILL_UL, TIP_SIZES_UL, TIP_MIN_FRACTION, select_tip

WELL_RE = re.compile(r"^[A-H](1[0-2]|[1-9])$")


@dataclass
class Issue:
    step: int  # 1-based, matches the numbering shown to the user
    message: str


@dataclass
class ValidationReport:
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate(plan: list[Transfer], deck_state: dict) -> ValidationReport:
    report = ValidationReport()
    if not plan:
        report.errors.append(Issue(0, "The plan is empty."))
        return report

    state = copy.deepcopy(deck_state)
    tips_left = {int(k.removesuffix("uL")): v for k, v in state["tips_left"].items()}

    for i, step in enumerate(plan, 1):
        problems_before = len(report.errors)

        for plate, well in [(step.source_plate, step.source_well), (step.dest_plate, step.dest_well)]:
            if plate not in state["plates"]:
                report.errors.append(Issue(i, f"Unknown plate '{plate}'."))
            elif not WELL_RE.match(well):
                report.errors.append(Issue(i, f"Well {well} does not exist on a 96-well plate (A1-H12)."))

        if step.volume_ul <= 0:
            report.errors.append(Issue(i, f"Volume must be positive, got {step.volume_ul:g} uL."))

        tip = select_tip(step.volume_ul) if step.volume_ul > 0 else None
        if step.volume_ul > 0 and tip is None:
            if step.volume_ul > max(TIP_SIZES_UL):
                report.errors.append(Issue(i, f"{step.volume_ul:g} uL is more than the largest tip "
                                              f"({max(TIP_SIZES_UL)} uL) holds; split it into several transfers."))
            else:
                smallest_min = TIP_MIN_FRACTION * min(TIP_SIZES_UL)
                report.errors.append(Issue(i, f"{step.volume_ul:g} uL is below the smallest volume that can "
                                              f"be pipetted accurately ({smallest_min:g} uL)."))
        elif tip is not None:
            if tips_left.get(tip, 0) <= 0:
                report.errors.append(Issue(i, f"No {tip} uL tips left."))
            else:
                tips_left[tip] -= 1

        if len(report.errors) > problems_before:
            continue  # can't simulate volumes for a step that references nothing real

        src = state["plates"][step.source_plate]
        dst = state["plates"][step.dest_plate]
        max_vol = dst["max_volume_ul"]
        dead_vol = DEAD_VOLUME_FRACTION * src["max_volume_ul"]

        available = src["filled_wells"].get(step.source_well, 0)
        if step.volume_ul > available:
            report.errors.append(Issue(i, f"{step.source_plate} {step.source_well} holds {available:g} uL at this "
                                          f"point, not enough for {step.volume_ul:g} uL."))
            continue
        remaining = available - step.volume_ul
        if remaining < dead_vol:
            report.warnings.append(Issue(i, f"Leaves {remaining:g} uL in {step.source_plate} {step.source_well}, "
                                            f"below the {dead_vol:g} uL dead volume; the robot may not aspirate "
                                            f"the full amount."))

        new_dest = dst["filled_wells"].get(step.dest_well, 0) + step.volume_ul
        if new_dest > max_vol:
            report.errors.append(Issue(i, f"{step.dest_plate} {step.dest_well} would hold {new_dest:g} uL, "
                                          f"over its {max_vol:g} uL capacity."))
            continue
        if new_dest > WORKING_MAX_FILL_UL:
            report.warnings.append(Issue(i, f"{step.dest_plate} {step.dest_well} would hold {new_dest:g} uL, "
                                            f"above the {WORKING_MAX_FILL_UL} uL working maximum."))

        src["filled_wells"][step.source_well] = remaining
        dst["filled_wells"][step.dest_well] = new_dest

    return report
