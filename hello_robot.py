"""
Sanity check: a simulated liquid handler doing one hand-written transfer. No AI yet.

What comes from PyLabRobot: the robot, the simulator, the deck, the labware
catalogue, the commands and the volume tracker.
What is ours: every choice marked "OUR CHOICE" below.
"""
import asyncio

# OUR CHOICE: PyLabRobot instead of a vendor API (e.g. Opentrons).
# It is hardware-agnostic, so the same code could drive Hamilton, Tecan or Opentrons.
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend
from pylabrobot.resources import (
    STARLetDeck,
    TIP_CAR_480_A00,
    PLT_CAR_L5AC_A00,
    hamilton_96_tiprack_1000uL,
    set_volume_tracking,
    cor_96_wellplate_360uL_Fb,
)


async def main():
    # OUR CHOICE: turn on volume tracking. It is OFF by default in PyLabRobot,
    # and without it the system cannot know what is in each well, so no validation is possible.
    set_volume_tracking(True)

    # OUR CHOICE: a simulated backend (no hardware needed, runs on any computer)
    # and a Hamilton STARlet deck (common in pharma labs).
    lh = LiquidHandler(backend=LiquidHandlerChatterboxBackend(), deck=STARLetDeck())
    await lh.setup()

    # OUR CHOICE: standard labware with real physical limits
    # (1000 uL tips, 96-well plates of 360 uL), so validation tests are meaningful.
    tip_carrier = TIP_CAR_480_A00(name="tip_carrier")
    tip_carrier[0] = tips = hamilton_96_tiprack_1000uL(name="tips")
    lh.deck.assign_child_resource(tip_carrier, rails=3)

    plate_carrier = PLT_CAR_L5AC_A00(name="plate_carrier")
    plate_carrier[0] = source = cor_96_wellplate_360uL_Fb(name="source")
    plate_carrier[1] = target = cor_96_wellplate_360uL_Fb(name="target")
    lh.deck.assign_child_resource(plate_carrier, rails=9)

    # OUR CHOICE: the starting state of the experiment (source A1 holds 200 uL).
    source.get_well("A1").tracker.set_volume(200)

    # OUR CHOICE: the protocol itself, written by hand: transfer 50 uL from source A1 to target B1.
    # The commands are PyLabRobot's. Note: PyLabRobot only detects errors (e.g. too little
    # liquid) DURING execution, with a tip already picked up. Our validation layer will check
    # the whole plan BEFORE the first movement.
    await lh.pick_up_tips(tips["A1"])
    await lh.aspirate(source["A1"], vols=[50])
    await lh.dispense(target["B1"], vols=[50])
    await lh.drop_tips(tips["A1"])

    print("\nSource A1 now holds:", source.get_well("A1").tracker.get_used_volume(), "uL")
    print("Target B1 now holds:", target.get_well("B1").tracker.get_used_volume(), "uL")

    await lh.stop()


if __name__ == "__main__":
    asyncio.run(main())
