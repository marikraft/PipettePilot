"""
Runs a validated plan on the liquid handler.

A fresh tip for every transfer: slower and uses more tips, but no carry-over between
wells, which matters more than speed on an assay plate.
"""
from .actions import Transfer
from .deck import Lab, next_tip
from .rules import select_tip


async def execute(lab: Lab, plan: list[Transfer]) -> None:
    for step in plan:
        tip = next_tip(lab, select_tip(step.volume_ul))
        source = lab.plates[step.source_plate].get_well(step.source_well)
        dest = lab.plates[step.dest_plate].get_well(step.dest_well)

        # PyLabRobot takes lists (one entry per channel); only channel 0 is used here.
        await lab.lh.pick_up_tips([tip])
        await lab.lh.aspirate([source], vols=[step.volume_ul])
        await lab.lh.dispense([dest], vols=[step.volume_ul])
        await lab.lh.discard_tips()  # to the waste, not back into the rack
